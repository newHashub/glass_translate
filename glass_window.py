import sys
from typing import Optional, Tuple, List, Dict, Any
from PyQt6.QtCore import Qt, QPoint, QRect, QRectF, QTimer, pyqtSlot
from PyQt6.QtGui import (
    QColor, QPainter, QBrush, QPen, QFont, QFontMetrics,
    QPainterPath, QCursor
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QScrollArea, QFrame, QSlider, QDialog, QLineEdit,
    QCheckBox, QApplication
)

from config import config_manager
from win32_utils import enable_acrylic, set_exclude_from_capture, set_rounded_corners
from worker import TranslationWorker

# 边缘缩放感应宽度 (14px)
RESIZE_MARGIN = 14


def layout_text_blocks(
    blocks: List[Dict[str, Any]],
    cw: float,
    ch: float,
    iw: int,
    ih: int,
    font_scale: float = 1.0
) -> List[Dict[str, Any]]:
    """
    自适应排版引擎：
    1. 像素级字号匹配：基准字号以原文实际像素高度 wh 与行距 limit_h 为锚定，下限精准下调至 9px，彻底解决字体臃肿偏大；
    2. 计算每行文字的真实行距 (pitch)，严密约束背景高度，杜绝下一行背景切除上一行文字下半部；
    3. 生成两遍绘制 (Two-Pass) 数据结构，彻底消除底色覆盖截断。
    """
    scale_x = float(iw) / float(max(1, cw))
    scale_y = float(ih) / float(max(1, ch))

    valid_blocks = [b for b in blocks if b.get("translated", "").strip()]
    sorted_blocks = sorted(valid_blocks, key=lambda b: b["box"][1])

    items = []
    for i, b in enumerate(sorted_blocks):
        bx, by, bw, bh = b["box"]
        wx = bx / scale_x
        wy = by / scale_y
        ww = max(16.0, bw / scale_x)
        wh = max(12.0, bh / scale_y)

        # 与下一行的真实垂直间距
        if i + 1 < len(sorted_blocks):
            next_wy = sorted_blocks[i + 1]["box"][1] / scale_y
            line_pitch = next_wy - wy
            if 0 < line_pitch < wh * 2.2:
                limit_h = line_pitch
            else:
                limit_h = wh + 3
        else:
            limit_h = wh + 3

        trans_text = b["translated"].strip()

        # 像素级精准字号：基准尺寸锚定原文行高 wh 与 limit_h，字体自然精致
        target_px = int(min(wh * 0.76, limit_h * 0.74) * font_scale)
        target_px = max(9, target_px)

        best_font = QFont("Microsoft YaHei")
        best_font.setPixelSize(target_px)
        best_font.setWeight(QFont.Weight.Medium)
        fm = QFontMetrics(best_font)

        while target_px > 9 and fm.height() > limit_h:
            target_px -= 1
            best_font.setPixelSize(target_px)
            fm = QFontMetrics(best_font)

        text_w = fm.horizontalAdvance(trans_text)
        text_h = fm.height()

        target_w = max(ww + 4, text_w + 6)
        target_h = max(wh, min(limit_h, text_h + 2))

        pad_rect = QRectF(wx - 1, wy, target_w, target_h)
        text_y_offset = (target_h - text_h) / 2.0
        text_rect = QRectF(wx + 2, wy + text_y_offset, target_w - 4, text_h + 1)

        items.append({
            "pad_rect": pad_rect,
            "text_rect": text_rect,
            "font": best_font,
            "text": trans_text,
            "bg_rgb": b.get("bg_rgb", (245, 245, 245)),
            "text_rgb": b.get("text_rgb", (15, 23, 42)),
        })

    return items


class ApiConfigDialog(QDialog):
    """自定义大模型 API 配置面板 (轻量专注，零冗余设置)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("自定义 API 配置")
        self.setFixedSize(380, 310)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)

        container = QFrame(self)
        container.setObjectName("apiContainer")
        container.setStyleSheet("""
            #apiContainer {
                background-color: rgba(18, 24, 38, 248);
                border: 1px solid rgba(56, 189, 248, 0.4);
                border-radius: 12px;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 13px;
                font-family: 'Segoe UI', 'Microsoft YaHei';
            }
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 6px;
                padding: 6px 10px;
                color: #ffffff;
                font-size: 12px;
            }
            QPushButton {
                background: #0284c7;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #0369a1;
            }
        """)

        form = QVBoxLayout(container)
        form.setContentsMargins(18, 16, 18, 16)
        form.setSpacing(10)

        # 标题栏
        header_box = QHBoxLayout()
        title_label = QLabel("🔑 自定义大模型 API 配置", self)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8;")
        close_btn = QPushButton("✕", self)
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94a3b8;
                font-size: 13px;
                border-radius: 12px;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.85);
                color: white;
            }
        """)
        close_btn.clicked.connect(self.close)
        header_box.addWidget(title_label)
        header_box.addStretch()
        header_box.addWidget(close_btn)
        form.addLayout(header_box)

        # 提示
        tip = QLabel("兼容 OpenAI、DeepSeek、Ollama 等标准协议接口")
        tip.setStyleSheet("color: #94a3b8; font-size: 11px;")
        form.addWidget(tip)

        form.addWidget(QLabel("API 端点 (URL):"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://api.openai.com/v1/chat/completions")
        self.url_input.setText(config_manager.get("api_url", "https://api.openai.com/v1/chat/completions"))
        form.addWidget(self.url_input)

        form.addWidget(QLabel("API 密钥 (Key):"))
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("sk-...")
        self.key_input.setText(config_manager.get("api_key", ""))
        form.addWidget(self.key_input)

        form.addWidget(QLabel("模型名称 (Model):"))
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("gpt-4o-mini 或 deepseek-chat")
        self.model_input.setText(config_manager.get("api_model", "gpt-4o-mini"))
        form.addWidget(self.model_input)

        save_btn = QPushButton("确定并启用自定义大模型", self)
        save_btn.clicked.connect(self._save_and_close)
        form.addWidget(save_btn)

        main_layout.addWidget(container)

    def _save_and_close(self):
        config_manager.set("api_url", self.url_input.text().strip(), auto_save=False)
        config_manager.set("api_key", self.key_input.text().strip(), auto_save=False)
        config_manager.set("api_model", self.model_input.text().strip(), auto_save=False)
        config_manager.set("engine", "openai", auto_save=True)
        if self.parent():
            if hasattr(self.parent(), "tray_manager") and self.parent().tray_manager:
                self.parent().tray_manager.sync_states()
            self.parent().trigger_refresh()
        self.accept()


# 保持向后兼容别名
SettingsDialog = ApiConfigDialog



class GlassWindow(QWidget):
    """
    无外边框、无工具栏、完全透明、纯粹Qt原生平滑拖拽与8向缩放的实时透视翻译窗口
    """

    def __init__(self):
        super().__init__()

        # 无边框、置顶、透明背景、Tool类型(不占任务栏)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)

        # 拖拽与缩放纯 Qt 状态机
        self._dragging = False
        self._resizing = False
        self._hovered = False
        self._drag_start_pos = QPoint()
        self._window_start_rect = QRect()
        self._resize_dir: Optional[str] = None

        # 移动静止去抖触发器 (250ms)
        self._drag_settle_timer = QTimer(self)
        self._drag_settle_timer.setSingleShot(True)
        self._drag_settle_timer.timeout.connect(self._on_drag_settled)

        # 识别与替换数据及渲染缓存 (消除 60fps 重绘字体度量开销)
        self.text_blocks: List[Dict[str, Any]] = []
        self.img_size: Tuple[int, int] = (1, 1)
        self.merged_original = ""
        self.merged_translated = ""
        self._result_version = 0
        self._cached_layout_items: List[Dict[str, Any]] = []
        self._cached_layout_signature = None

        # 玻璃状态指示胶囊 (直观反馈原因: 正在翻译 / 未检测到文字 / 网络超时 / 接口报错等)
        self._status_text = ""
        self._status_type = "ready"
        self._status_clear_timer = QTimer(self)
        self._status_clear_timer.setSingleShot(True)
        self._status_clear_timer.timeout.connect(self._clear_status_pill)

        # 加载历史坐标尺寸
        x = config_manager.get("window_x", 200)
        y = config_manager.get("window_y", 200)
        w = config_manager.get("window_width", 560)
        h = config_manager.get("window_height", 320)
        self.setGeometry(x, y, w, h)
        self.setMinimumSize(140, 80)

        self._init_ui()

        # 启动后台处理线程
        self.worker = TranslationWorker()
        self.worker.result_ready.connect(self._on_result_ready)
        self.worker.status_changed.connect(self._on_status_changed)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()

        # 首次坐标同步
        QTimer.singleShot(100, self._sync_capture_rect)

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        set_rounded_corners(hwnd)
        set_exclude_from_capture(hwnd, True)

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.card_scroll = QScrollArea(self)
        self.card_scroll.setWidgetResizable(True)
        self.card_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.card_scroll.setStyleSheet("background: transparent; border: none;")

        self.card_widget = QFrame()
        self.card_widget.setStyleSheet("""
            background-color: rgba(15, 23, 42, 0.88);
            border: 1px solid rgba(56, 189, 248, 0.35);
            border-radius: 8px;
            padding: 8px;
        """)
        card_inner_layout = QVBoxLayout(self.card_widget)
        self.card_label = QLabel("🪟 拖拽此取景框覆盖文字，即可实时翻译 (右键唤出设置菜单)", self.card_widget)
        self.card_label.setWordWrap(True)
        self.card_label.setStyleSheet("color: #f8fafc; font-size: 13px; font-family: 'Segoe UI', 'Microsoft YaHei';")
        card_inner_layout.addWidget(self.card_label)

        self.card_scroll.setWidget(self.card_widget)
        root_layout.addWidget(self.card_scroll)

        cur_mode = config_manager.get("display_mode", "inplace")
        self.apply_mode(cur_mode)

    def apply_mode(self, mode: str):
        config_manager.set("display_mode", mode)
        if mode == "inplace":
            self.card_scroll.setVisible(False)
        else:
            self.card_scroll.setVisible(True)
        self.update()

    def _clear_stale_content(self):
        self.text_blocks = []
        self.merged_translated = ""
        self.card_label.setText("")
        self._cached_layout_items = []
        self._cached_layout_signature = None
        self._result_version += 1
        self._status_text = ""
        self.update()

    def _update_layout_cache(self) -> List[Dict[str, Any]]:
        """按需计算并缓存排版结果，当窗口尺寸或文字发生变动时刷新"""
        cw = self.width()
        ch = self.height()
        iw, ih = self.img_size
        font_scale = config_manager.get("font_scale", 1.0)
        sig = (cw, ch, iw, ih, font_scale, self._result_version)
        if sig != self._cached_layout_signature:
            if self.text_blocks and iw > 0 and ih > 0:
                self._cached_layout_items = layout_text_blocks(
                    self.text_blocks, cw, ch, iw, ih, font_scale
                )
            else:
                self._cached_layout_items = []
            self._cached_layout_signature = sig
        return self._cached_layout_items

    # ---------------- 窗口绘制：完全透明 + 取景框四角直角标 + 两遍绘制 ----------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = self.rect()

        # alpha=1 保证 Windows 捕获鼠标点击，杜绝点击穿透
        painter.fillRect(rect, QColor(0, 0, 0, 1))

        # 取景框四角直角标 (长度 16px)
        corner_pen = QPen(QColor(56, 189, 248, 190), 2.0)
        painter.setPen(corner_pen)
        s = 16
        w, h = rect.width(), rect.height()
        painter.drawLine(2, 2, 2 + s, 2)
        painter.drawLine(2, 2, 2, 2 + s)
        painter.drawLine(w - 2 - s, 2, w - 2, 2)
        painter.drawLine(w - 2, 2, w - 2, 2 + s)
        painter.drawLine(2, h - 2 - s, 2, h - 2)
        painter.drawLine(2, h - 2, 2 + s, h - 2)
        painter.drawLine(w - 2 - s, h - 2, w - 2, h - 2)
        painter.drawLine(w - 2, h - 2 - s, w - 2, h - 2)

        # 悬停时辅助微虚线
        if self._hovered or self._resizing or self._dragging:
            guide_pen = QPen(QColor(56, 189, 248, 70), 1.0, Qt.PenStyle.DashLine)
            painter.setPen(guide_pen)
            painter.drawRect(rect.adjusted(1, 1, -2, -2))

        # 原地文字替换渲染 (Two-Pass 两遍绘制架构：底色先铺，文字后画)
        mode = config_manager.get("display_mode", "inplace")
        if mode == "inplace":
            layout_items = self._update_layout_cache()
            if layout_items:
                # 【第一遍 PASS 1】：统一画所有微胶囊背景底色
                for it in layout_items:
                    bg = it["bg_rgb"]
                    patch_bg = QColor(bg[0], bg[1], bg[2], 245)
                    painter.setBrush(QBrush(patch_bg))
                    painter.setPen(QPen(QColor(bg[0], bg[1], bg[2], 120), 1.0))
                    painter.drawRoundedRect(it["pad_rect"], 3.0, 3.0)

                # 【第二遍 PASS 2】：统一画所有文字（绝不被底色截断）
                for it in layout_items:
                    painter.setFont(it["font"])
                    fg = it["text_rgb"]
                    painter.setPen(QColor(fg[0], fg[1], fg[2]))
                    painter.drawText(
                        it["text_rect"],
                        int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                        f" {it['text']}"
                    )



        # 底部状态指示胶囊 (受菜单栏开关控制，直观在玻璃框上反馈原因: 正在翻译/未检测到文字/网络超时/接口报错等)
        if config_manager.get("show_status_pill", False) and self._status_text:
            self._draw_status_pill(painter, rect)



    def _draw_status_pill(self, painter: QPainter, rect: QRect):
        font = QFont("Microsoft YaHei", 9)
        font.setWeight(QFont.Weight.Medium)
        fm = QFontMetrics(font)
        text_w = fm.horizontalAdvance(self._status_text)
        pill_w = min(float(rect.width() - 24), float(text_w + 24))
        pill_h = 24.0
        pill_x = (rect.width() - pill_w) / 2.0
        pill_y = max(6.0, float(rect.height() - pill_h - 10))

        st = self._status_type
        if st == "busy":
            bg_color = QColor(15, 23, 42, 230)
            border_color = QColor(56, 189, 248, 180)
            text_color = QColor(56, 189, 248)
        elif st == "error":
            bg_color = QColor(69, 10, 10, 240)
            border_color = QColor(248, 113, 113, 220)
            text_color = QColor(254, 202, 202)
        elif st == "empty":
            bg_color = QColor(15, 23, 42, 205)
            border_color = QColor(148, 163, 184, 130)
            text_color = QColor(203, 213, 225)
        elif st == "paused":
            bg_color = QColor(15, 23, 42, 225)
            border_color = QColor(251, 191, 36, 180)
            text_color = QColor(251, 191, 36)
        elif st == "success":
            bg_color = QColor(6, 78, 59, 225)
            border_color = QColor(52, 211, 153, 180)
            text_color = QColor(167, 243, 208)
        else:
            bg_color = QColor(15, 23, 42, 210)
            border_color = QColor(56, 189, 248, 120)
            text_color = QColor(226, 232, 240)

        pill_rect = QRectF(pill_x, pill_y, pill_w, pill_h)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 1.0))
        painter.drawRoundedRect(pill_rect, 12.0, 12.0)

        painter.setFont(font)
        painter.setPen(text_color)
        elided = fm.elidedText(self._status_text, Qt.TextElideMode.ElideRight, int(pill_w - 14))
        painter.drawText(pill_rect, int(Qt.AlignmentFlag.AlignCenter), elided)

    @pyqtSlot(str, str)
    def _on_status_changed(self, text: str, status_type: str):
        self._status_text = text
        self._status_type = status_type
        if status_type in ["success", "ready"]:
            self._status_clear_timer.start(1800)
        else:
            self._status_clear_timer.stop()
        self.update()
        self.repaint()

    def _clear_status_pill(self):
        self._status_text = ""
        self.update()
        self.repaint()

    # ---------------- 交互事件处理：纯 Qt 极速拖拽与 8 向缩放 (零模态卡死) ----------------
    def _get_resize_direction(self, pos: QPoint) -> Optional[str]:
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        m = RESIZE_MARGIN

        left = x <= m
        right = x >= w - m
        top = y <= m
        bottom = y >= h - m

        if top and left:
            return "top_left"
        if top and right:
            return "top_right"
        if bottom and left:
            return "bottom_left"
        if bottom and right:
            return "bottom_right"
        if left:
            return "left"
        if right:
            return "right"
        if top:
            return "top"
        if bottom:
            return "bottom"
        return None

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        # 右键呼出菜单
        if event.button() == Qt.MouseButton.RightButton:
            if hasattr(self, "tray_manager") and self.tray_manager:
                self.tray_manager.sync_states()
                if hasattr(self, "worker"):
                    self.worker.set_paused(True)
                self.tray_manager.menu.exec(event.globalPosition().toPoint())
                if hasattr(self, "worker"):
                    self.worker.set_paused(not config_manager.get("auto_translate", True))
            event.accept()
            return

        # 左键按下
        if event.button() == Qt.MouseButton.LeftButton:
            rdir = self._get_resize_direction(event.pos())
            # 按下瞬间清空内容，像移动一块纯净透明的取景玻璃
            self._clear_stale_content()

            if hasattr(self, "worker"):
                self.worker.set_moving(True)



            if rdir:
                # 边缘开始缩放
                self._resizing = True
                self._resize_dir = rdir
                self._drag_start_pos = event.globalPosition().toPoint()
                self._window_start_rect = self.geometry()
            else:
                # 框内开始平滑拖拽移动
                self._dragging = True
                self._drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # 1. 处于平滑拖拽移动中 (纯 Qt 原生定位，绝对不发生 Win32 模态卡死)
        if self._dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_start_pos
            self.move(new_pos)
            self._drag_settle_timer.start(250)
            event.accept()
            return

        # 2. 处于平滑边缘缩放中
        if self._resizing and self._resize_dir:
            delta = event.globalPosition().toPoint() - self._drag_start_pos
            rect = QRect(self._window_start_rect)
            min_w, min_h = self.minimumWidth(), self.minimumHeight()

            if "left" in self._resize_dir:
                new_w = max(min_w, rect.width() - delta.x())
                rect.setLeft(rect.right() - new_w)
            elif "right" in self._resize_dir:
                rect.setWidth(max(min_w, rect.width() + delta.x()))

            if "top" in self._resize_dir:
                new_h = max(min_h, rect.height() - delta.y())
                rect.setTop(rect.bottom() - new_h)
            elif "bottom" in self._resize_dir:
                rect.setHeight(max(min_h, rect.height() + delta.y()))

            self.setGeometry(rect)
            self._drag_settle_timer.start(250)
            self.update()
            event.accept()
            return

        # 3. 鼠标悬停根据位置动态切换光标
        rdir = self._get_resize_direction(event.pos())
        if rdir in ["top_left", "bottom_right"]:
            self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
        elif rdir in ["top_right", "bottom_left"]:
            self.setCursor(QCursor(Qt.CursorShape.SizeBDiagCursor))
        elif rdir in ["left", "right"]:
            self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
        elif rdir in ["top", "bottom"]:
            self.setCursor(QCursor(Qt.CursorShape.SizeVerCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._resizing or self._dragging:
                self._resizing = False
                self._dragging = False
                self._resize_dir = None
                self._drag_settle_timer.stop()

                # 松开鼠标瞬间，立即保存坐标并启动极速扫描！
                self._on_drag_settled()
                self.update()
                event.accept()
                return

        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """鼠标位于玻璃框内时，直接滑动滚轮进行以鼠标为锚点的等比缩放"""
        if not config_manager.get("wheel_zoom_enabled", True):
            super().wheelEvent(event)
            return

        delta = event.angleDelta().y()
        if delta == 0:
            return

        pos = event.position().toPoint()
        w, h = self.width(), self.height()

        factor = 0.08 if delta > 0 else -0.08
        dw = int(w * factor)
        dh = int(h * factor)

        min_w, min_h = self.minimumWidth(), self.minimumHeight()
        screen = QApplication.screenAt(self.geometry().center())
        screen_geo = screen.availableGeometry() if screen else QRect(0, 0, 3840, 2160)

        new_w = max(min_w, min(screen_geo.width() - 40, w + dw))
        new_h = max(min_h, min(screen_geo.height() - 40, h + dh))

        rx = pos.x() / max(1, w)
        ry = pos.y() / max(1, h)
        new_x = int(self.x() - (new_w - w) * rx)
        new_y = int(self.y() - (new_h - h) * ry)

        new_x = max(screen_geo.left(), min(new_x, screen_geo.right() - new_w))
        new_y = max(screen_geo.top(), min(new_y, screen_geo.bottom() - new_h))

        self._clear_stale_content()
        self.setGeometry(new_x, new_y, new_w, new_h)
        self._drag_settle_timer.start(250)
        event.accept()



    @pyqtSlot()
    def toggle_summon(self):
        """Alt+R 全局快捷键呼出/收起：隐藏时移至鼠标位置居中呼出并识别，已显示时快捷隐藏"""
        if not self.isVisible():
            cursor_pos = QCursor.pos()
            w, h = self.width(), self.height()
            target_x = cursor_pos.x() - w // 2
            target_y = cursor_pos.y() - h // 2

            screen = QApplication.screenAt(cursor_pos)
            if screen:
                sg = screen.availableGeometry()
                target_x = max(sg.left(), min(target_x, sg.right() - w))
                target_y = max(sg.top(), min(target_y, sg.bottom() - h))

            self.move(target_x, target_y)
            self.show()
            self.activateWindow()
            self._clear_stale_content()
            self._on_drag_settled()
        else:
            self.hide()

    def _save_geometry(self):
        geom = self.geometry()
        config_manager.set("window_x", geom.x(), auto_save=False)
        config_manager.set("window_y", geom.y(), auto_save=False)
        config_manager.set("window_width", geom.width(), auto_save=False)
        config_manager.set("window_height", geom.height(), auto_save=True)

    def _on_drag_settled(self):
        """窗口移动或缩放停止后，立即通知后台线程直扫新视野"""
        self._save_geometry()
        geom = self.geometry()
        rect = (geom.x(), geom.y(), geom.width(), geom.height())
        if hasattr(self, "worker"):
            self.worker.notify_new_position(rect)

    def _sync_capture_rect(self):
        geom = self.geometry()
        x, y, w, h = geom.x(), geom.y(), geom.width(), geom.height()
        if hasattr(self, "worker"):
            self.worker.notify_new_position((x, y, w, h))

    # ---------------- 托盘调用的接口 ----------------
    def trigger_refresh(self):
        geom = self.geometry()
        rect = (geom.x(), geom.y(), geom.width(), geom.height())
        if hasattr(self, "worker"):
            self.worker.trigger_once(rect)

    def set_auto_translate(self, is_auto: bool):
        config_manager.set("auto_translate", is_auto)
        if hasattr(self, "worker"):
            self.worker.set_paused(not is_auto)

    def set_always_on_top(self, is_top: bool):
        config_manager.set("always_on_top", is_top)
        flags = self.windowFlags()
        if is_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def set_show_status_pill(self, show: bool):
        config_manager.set("show_status_pill", show)
        if hasattr(self, "tray_manager") and self.tray_manager:
            self.tray_manager.sync_states()
        if not show:
            self._status_text = ""
        self.update()


    def copy_translation(self):
        text = self.merged_translated.strip() or self.card_label.text().strip()
        if text and not text.startswith("🪟"):
            QApplication.clipboard().setText(text)

    def open_api_settings(self):
        dialog = ApiConfigDialog(self)
        dialog.exec()

    def open_settings(self):
        self.open_api_settings()

    @pyqtSlot(str, str, list, tuple)
    def _on_result_ready(self, original: str, translated: str, blocks: list, img_size: tuple):
        self.merged_original = original
        self.merged_translated = translated
        self.text_blocks = blocks
        self.img_size = img_size
        self._result_version += 1

        if translated:
            self.card_label.setText(f"{translated}")
        else:
            self.card_label.setText("🪟 拖拽此取景框覆盖文字，即可实时翻译 (右键唤出设置菜单)")

        self.update()
        self.repaint()

    @pyqtSlot(str)
    def _on_error(self, err_msg: str):
        print(f"[UI] 错误提示: {err_msg}")

    def closeEvent(self, event):
        if getattr(self, "_force_close", False):
            event.accept()
            return
        event.ignore()
        self.hide()
        if hasattr(self, "tray_manager") and self.tray_manager:
            self.tray_manager.sync_states()

