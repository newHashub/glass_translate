import time
import threading
from typing import Optional, Tuple, List, Dict, Any
from PyQt6.QtCore import QThread, pyqtSignal

from capture_engine import CaptureEngine
from ocr_engine import OcrEngine
from translator_engine import TranslatorEngine, is_valid_translation, is_same_text
from config import config_manager



class TranslationWorker(QThread):
    """
    后台高响应工作线程：
    - 移动态静默省流，落位瞬间 150ms 极速直扫
    - 移窗自动重置识别比对缓存，杜绝移位后卡顿与不翻译
    """
    status_changed = pyqtSignal(str, str)
    result_ready = pyqtSignal(str, str, list, tuple)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.capture_engine = CaptureEngine()
        self.ocr_engine = OcrEngine()
        self.translator_engine = TranslatorEngine()

        self._running = True
        self._paused = False
        self._is_moving = False
        self._need_immediate_scan = False
        self._force_trigger = False
        self._force_scan_counter = 0
        self._target_rect: Optional[Tuple[int, int, int, int]] = None
        self._lock = threading.Lock()
        self._last_recognized_text = ""

    def set_moving(self, is_moving: bool):
        """窗口开始移动或缩放：立即进入静默态，避免移动中浪费算力与锁竞争"""
        with self._lock:
            self._is_moving = is_moving
            if is_moving:
                self._force_scan_counter = 0
                self.capture_engine.force_reset()

    def notify_new_position(self, rect: Tuple[int, int, int, int]):
        """窗口落位新坐标：连续3次强制刷新确保跨越DWM重绘延迟，保留内容指纹以便快速复用"""
        with self._lock:
            self._target_rect = rect
            self._is_moving = False
            self._force_scan_counter = 3
            self._need_immediate_scan = True
            self.capture_engine.force_reset()

    def trigger_once(self, rect: Optional[Tuple[int, int, int, int]] = None):
        """立即强制触发识别与翻译"""
        with self._lock:
            if rect:
                self._target_rect = rect
            self._is_moving = False
            self._force_scan_counter = 3
            self._need_immediate_scan = True
            self._force_trigger = True
            self.capture_engine.force_reset()


    def set_paused(self, paused: bool):
        with self._lock:
            self._paused = paused
        color = "paused" if paused else "ready"
        text = "已暂停实时识别" if paused else "实时就绪"
        self.status_changed.emit(text, color)

    def is_paused(self) -> bool:
        with self._lock:
            return self._paused

    def stop(self):
        self._running = False
        self.wait(1500)

    def run(self):
        while self._running:
            interval_ms = config_manager.get("scan_interval_ms", 300)
            sleep_sec = max(0.05, interval_ms / 1000.0)

            with self._lock:
                paused = self._paused
                is_moving = self._is_moving
                rect = self._target_rect
                force = (self._force_scan_counter > 0) or self._need_immediate_scan or self._force_trigger
                if self._force_scan_counter > 0:
                    self._force_scan_counter -= 1
                self._need_immediate_scan = False
                self._force_trigger = False

            # 若暂停、正在拖动移动中、或尚未设置矩形坐标
            if (paused and not force) or is_moving or not rect:
                time.sleep(0.05)
                continue

            x, y, w, h = rect
            if w <= 30 or h <= 30:
                time.sleep(0.05)
                continue

            # 1. 抓取屏幕框内图像 (底层亲和性穿透，毫秒级)
            img = self.capture_engine.capture_screen_rect(x, y, w, h)
            if not img:
                time.sleep(0.05)
                continue

            # 2. 图像变动快速比对 (若非强制刷新且画面静止，则跳过)
            if not force and not self.capture_engine.check_has_changed(img, rect):
                time.sleep(sleep_sec)
                continue

            # 3. Windows 原生硬件加速 OCR (10~20ms)
            source_lang = config_manager.get("source_lang", "auto")
            target_lang = config_manager.get("target_lang", "zh-CN")

            try:
                merged_text, blocks = self.ocr_engine.recognize(img, source_lang)
            except Exception as e:
                self.error_occurred.emit(f"OCR识别错误: {e}")
                time.sleep(sleep_sec)
                continue

            # 若框内没有文字
            if not blocks or not merged_text.strip():
                if self._last_recognized_text:
                    self._last_recognized_text = ""
                    self.result_ready.emit("", "", [], (img.width, img.height))
                self.status_changed.emit("🔍 未在框内检测到文字", "empty")
                time.sleep(sleep_sec)
                continue

            # 若非强制刷新且文字与上次实质一致 (避免 OCR 极微小抖动反复轰炸翻译引擎)
            if not force and is_same_text(merged_text, self._last_recognized_text):
                time.sleep(sleep_sec)
                continue

            # 4. 行级语义缓存极速探针：若框内所有行均已在缓存中，0ms 瞬间装配复用！
            all_cached = True
            for b in blocks:
                cached_line = self.translator_engine.get_line_translation(b["text"])
                if cached_line:
                    b["translated"] = cached_line
                else:
                    all_cached = False
                    break

            if all_cached and len(blocks) > 0:
                translated_all = "\n".join([b["translated"] for b in blocks])
                self.result_ready.emit(
                    merged_text, translated_all, blocks, (img.width, img.height)
                )
                self.status_changed.emit(f"✓ 缓存秒显 ({len(blocks)} 行)", "success")
                time.sleep(sleep_sec)
                continue

            # 5. 未完全命中缓存时，走多引擎自适应翻译 (100~180ms)
            self.status_changed.emit(f"⏳ 正在翻译 ({len(blocks)} 行)...", "busy")
            try:
                all_lines = [b["text"] for b in blocks]
                lines_payload = "\n".join(all_lines)

                translated_all = self.translator_engine.translate(
                    lines_payload, source_lang, target_lang
                )


                trans_lines = translated_all.split("\n") if translated_all else []
                valid_count = 0
                for i, b in enumerate(blocks):
                    line_trans = trans_lines[i].strip() if i < len(trans_lines) else ""
                    if line_trans and is_valid_translation(b["text"], line_trans, target_lang):
                        b["translated"] = line_trans
                        valid_count += 1
                    else:
                        b["translated"] = ""

                # 将识别与有效翻译结果发送给主界面 (若无有效翻译则 translated_all 传空，避免字幕卡片显示原文)
                self.result_ready.emit(
                    merged_text, translated_all if valid_count > 0 else "", blocks, (img.width, img.height)
                )

                if valid_count == 0 and len(blocks) > 0:
                    err_msg = self.translator_engine.last_error or "接口返回原文，未转换目标语言"
                    self.status_changed.emit(f"⚠️ 翻译未生效: {err_msg}", "error")
                elif valid_count < len(blocks):
                    self.status_changed.emit(f"✓ 部分完成 ({valid_count}/{len(blocks)} 行)", "busy")
                else:
                    self.status_changed.emit(f"✓ 翻译完成 ({valid_count} 行)", "success")
            except Exception as e:
                self.error_occurred.emit(f"翻译异常: {e}")
                self.status_changed.emit(f"⚠️ 翻译失败: {e}", "error")

            time.sleep(sleep_sec)


