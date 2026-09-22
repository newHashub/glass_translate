import time
import threading
import re
from typing import Optional, Tuple, List, Dict, Any
from PyQt6.QtCore import QThread, pyqtSignal

from capture_engine import CaptureEngine
from ocr_engine import OcrEngine
from translator_engine import TranslatorEngine, is_valid_translation, is_same_text
from config import config_manager


def cluster_blocks(blocks: List[Dict[str, Any]]) -> List[List[int]]:
    """
    将 OCR 视觉行智能聚类为自然段落/语义句簇：
    1. 若前一行末尾不是终止标点 (. ! ? 。 ！ ？ : ； ; 等)，合并为同一语义句簇，防止断句翻译错漏
    2. 若两行之间的垂直行距 (pitch) 明显大于正常行间距，则判定为段落视觉分隔
    """
    if not blocks:
        return []

    clusters: List[List[int]] = []
    cur_cluster: List[int] = [0]

    for i in range(1, len(blocks)):
        prev_b = blocks[i - 1]
        cur_b = blocks[i]

        prev_text = prev_b.get("text", "").strip()
        cur_text = cur_b.get("text", "").strip()
        ends_with_terminal = bool(re.search(r"[.!?。！？:：;；]$", prev_text))

        prev_box = prev_b.get("box", (0, 0, 0, 20))
        cur_box = cur_b.get("box", (0, 0, 0, 20))
        prev_y = prev_box[1]
        prev_h = prev_box[3]
        cur_y = cur_box[1]
        pitch = cur_y - (prev_y + prev_h)

        # 行间距大于行高 0.65 倍即判定为物理换行/段落间隔
        is_large_gap = pitch > max(8.0, prev_h * 0.65)
        # 列表标识 (如 1. / - / * 等)
        is_list = bool(re.match(r"^(\d+[\.\)]|[-*•])\s+", cur_text))
        # 上一行较短且当前行首字母大写 (如短句、标题、各行独立的短语)
        is_short_title = len(prev_text) <= 35 and bool(cur_text) and cur_text[0].isupper()

        if ends_with_terminal or is_large_gap or is_list or is_short_title:
            clusters.append(cur_cluster)
            cur_cluster = [i]
        else:
            cur_cluster.append(i)

    if cur_cluster:
        clusters.append(cur_cluster)
    return clusters


def wrap_text_to_lines(text: str, line_widths: List[float]) -> List[str]:
    """
    将整句/整段翻译结果按各原视觉行的相对像素宽度比例，平滑分布到对应的物理行中
    """
    if not text:
        return ["" for _ in line_widths]
    if len(line_widths) == 1:
        return [text]

    total_w = sum(line_widths)
    if total_w <= 0:
        total_w = float(len(line_widths))
        line_widths = [1.0 for _ in line_widths]

    total_chars = len(text)
    allocated_lengths = []
    accum = 0
    for idx, w in enumerate(line_widths):
        if idx == len(line_widths) - 1:
            allocated_lengths.append(total_chars - accum)
        else:
            n = int(round(total_chars * (w / total_w)))
            n = max(1, min(total_chars - accum - (len(line_widths) - 1 - idx), n))
            allocated_lengths.append(n)
            accum += n

    res_lines = []
    char_idx = 0
    for n in allocated_lengths:
        segment = text[char_idx : char_idx + n].strip()
        char_idx += n
        res_lines.append(segment)

    return res_lines



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
        self._capture_engine = None
        self._ocr_engine = None
        self._translator_engine = None

        self._running = True
        self._paused = False
        self._is_moving = False
        self._need_immediate_scan = False
        self._force_trigger = False
        self._force_scan_counter = 0
        self._target_rect: Optional[Tuple[int, int, int, int]] = None
        self._lock = threading.Lock()
        self._last_recognized_text = ""

    @property
    def capture_engine(self):
        if self._capture_engine is None:
            self._capture_engine = CaptureEngine()
        return self._capture_engine

    @capture_engine.setter
    def capture_engine(self, val):
        self._capture_engine = val

    @property
    def ocr_engine(self):
        if self._ocr_engine is None:
            self._ocr_engine = OcrEngine()
        return self._ocr_engine

    @ocr_engine.setter
    def ocr_engine(self, val):
        self._ocr_engine = val

    @property
    def translator_engine(self):
        if self._translator_engine is None:
            self._translator_engine = TranslatorEngine()
        return self._translator_engine

    @translator_engine.setter
    def translator_engine(self, val):
        self._translator_engine = val

    def set_moving(self, is_moving: bool):
        """窗口开始移动或缩放：立即进入静默态，避免移动中浪费算力与锁竞争"""
        with self._lock:
            self._is_moving = is_moving
            if is_moving:
                self._force_scan_counter = 0
                if self._capture_engine is not None:
                    self._capture_engine.force_reset()

    def notify_new_position(self, rect: Tuple[int, int, int, int]):
        """窗口落位新坐标：连续3次强制刷新确保跨越DWM重绘延迟，保留内容指纹以便快速复用"""
        with self._lock:
            self._target_rect = rect
            self._is_moving = False
            self._force_scan_counter = 3
            self._need_immediate_scan = True
            if self._capture_engine is not None:
                self._capture_engine.force_reset()

    def trigger_once(self, rect: Optional[Tuple[int, int, int, int]] = None):
        """立即强制触发识别与翻译"""
        with self._lock:
            if rect:
                self._target_rect = rect
            self._is_moving = False
            self._force_scan_counter = 3
            self._need_immediate_scan = True
            self._force_trigger = True
            if self._capture_engine is not None:
                self._capture_engine.force_reset()


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
        # 在后台工作线程就绪时并行预热三大引擎，绝不阻塞主 GUI 线程与窗口呈现
        try:
            _ = self.capture_engine
            _ = self.ocr_engine
            _ = self.translator_engine
        except Exception as e:
            print(f"[TranslationWorker] 后台预热引擎异常: {e}")

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

            # 5. 未完全命中缓存时，走自然句簇聚类与多引擎自适应翻译 (100~180ms)
            self.status_changed.emit(f"⏳ 正在翻译 ({len(blocks)} 行)...", "busy")
            try:
                clusters = cluster_blocks(blocks)
                # 聚类为自然语义完整句子，彻底解决 OCR 屏幕物理折行导致的断句丢意与行数错乱
                cluster_sentences = [" ".join([blocks[i]["text"] for i in cl]) for cl in clusters]
                payload = "\n".join(cluster_sentences)

                translated_all = self.translator_engine.translate(
                    payload, source_lang, target_lang
                )

                trans_lines = [l.strip() for l in translated_all.split("\n") if l.strip()] if translated_all else []

                # 1. 若翻译返回行数与 blocks 物理行数直接相等，1对1精准对应
                if len(trans_lines) == len(blocks):
                    for idx, b in enumerate(blocks):
                        blocks[idx]["translated"] = trans_lines[idx]

                # 2. 若翻译返回句数与聚类句簇数一致，按各簇内视觉行物理宽度平滑映射
                elif len(trans_lines) == len(clusters):
                    for cl, t_sent in zip(clusters, trans_lines):
                        t_clean = t_sent.strip()
                        c_blocks = [blocks[i] for i in cl]
                        widths = [b["box"][2] for b in c_blocks]
                        wrapped_subs = wrap_text_to_lines(t_clean, widths)
                        for b_idx, sub_t in zip(cl, wrapped_subs):
                            blocks[b_idx]["translated"] = sub_t

                # 3. 容灾平滑分发：当翻译结果仅返回 1 行或行数少于 blocks 时，
                #    按所有物理行的实际宽度比例自动平滑折行切分分布到各行，绝不允许把全部译文塞进第一行！
                else:
                    all_widths = [max(30.0, float(b["box"][2])) for b in blocks]
                    full_clean = " ".join(trans_lines) if trans_lines else (translated_all.strip() if translated_all else "")
                    wrapped_all = wrap_text_to_lines(full_clean, all_widths)
                    for idx, b in enumerate(blocks):
                        blocks[idx]["translated"] = wrapped_all[idx] if idx < len(wrapped_all) else ""

                # 6. 100% 全覆盖保障网：针对任何因切分、过滤或网络抖动遗漏的行，自动精准补齐
                valid_count = 0
                for b in blocks:
                    t_val = b.get("translated", "").strip()
                    if t_val and is_valid_translation(b["text"], t_val, target_lang):
                        valid_count += 1
                    else:
                        cached_l = self.translator_engine.get_line_translation(b["text"])
                        if cached_l:
                            b["translated"] = cached_l
                            valid_count += 1
                        else:
                            single_t = self.translator_engine.translate(b["text"], source_lang, target_lang)
                            if single_t and is_valid_translation(b["text"], single_t, target_lang):
                                b["translated"] = single_t
                                valid_count += 1
                            else:
                                b["translated"] = ""

                # 重新构建带清晰物理换行的完整译文，供卡片模式和复制到剪贴板使用
                valid_lines = [b["translated"].strip() for b in blocks if b.get("translated", "").strip()]
                if len(valid_lines) > 1:
                    final_translated = "\n".join(valid_lines)
                else:
                    final_translated = translated_all if valid_count > 0 else ""

                # 将识别与有效翻译结果发送给主界面 (保证卡片模式与复制均有优雅换行)
                self.result_ready.emit(
                    merged_text, final_translated, blocks, (img.width, img.height)
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


