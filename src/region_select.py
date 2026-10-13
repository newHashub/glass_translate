from typing import Optional

from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QCursor, QGuiApplication
from PyQt6.QtWidgets import QWidget

# 小于该尺寸的选区视为误触/单击，直接取消
MIN_SELECT_W = 40
MIN_SELECT_H = 24


def normalize_selection(p1: QPoint, p2: QPoint) -> QRect:
    """把拖拽起点与终点规整为左上角起算的矩形 (支持任意方向拖拽)"""
    x0, x1 = sorted((p1.x(), p2.x()))
    y0, y1 = sorted((p1.y(), p2.y()))
    return QRect(x0, y0, x1 - x0, y1 - y0)


def is_valid_selection(rect: QRect) -> bool:
    return rect.width() >= MIN_SELECT_W and rect.height() >= MIN_SELECT_H


class RegionSelectOverlay(QWidget):
    """
    全屏框选蒙层 (类似微信/QQ 截图)：
    - 按下快捷键后覆盖所有屏幕并压暗画面
    - 左键拖出矩形，松手即发出 region_selected(全局坐标矩形)
    - Esc 或右键取消
    """
    region_selected = pyqtSignal(QRect)
    cancelled = pyqtSignal()

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        self._origin: Optional[QPoint] = None  # 局部坐标
        self._current: Optional[QPoint] = None
        self._finished = False

        # 覆盖整个虚拟桌面 (多显示器)
        screen = QGuiApplication.primaryScreen()
        self._desktop = screen.virtualGeometry() if screen else QRect(0, 0, 1920, 1080)
        self.setGeometry(self._desktop)

    # ---------------- 生命周期 ----------------
    def start(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()
        self.grabKeyboard()

    def _finish(self, rect: Optional[QRect]):
        if self._finished:
            return
        self._finished = True
        self.releaseKeyboard()
        self.hide()
        if rect is not None:
            self.region_selected.emit(rect)
        else:
            self.cancelled.emit()
        self.close()

    # ---------------- 选区 ----------------
    def selection_rect(self) -> Optional[QRect]:
        """当前选区 (局部坐标)"""
        if self._origin is None or self._current is None:
            return None
        return normalize_selection(self._origin, self._current)

    # ---------------- 事件 ----------------
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._finish(None)
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self._finish(None)
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.position().toPoint()
            self._current = self._origin
            self.update()

    def mouseMoveEvent(self, event):
        if self._origin is not None:
            self._current = event.position().toPoint()
        else:
            self._hover = event.position().toPoint()
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or self._origin is None:
            return
        self._current = event.position().toPoint()
        local = self.selection_rect()
        if local is None or not is_valid_selection(local):
            # 选区太小视为误触，重新等待拖拽而不是直接退出
            self._origin = self._current = None
            self.update()
            return
        self._finish(local.translated(self._desktop.topLeft()))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        full = self.rect()
        sel = self.selection_rect()

        # 压暗画面；选区内保持几乎透明 (alpha=1 保证仍能接收鼠标事件)
        dim = QColor(2, 6, 23, 110)
        if sel is None or sel.isEmpty():
            painter.fillRect(full, dim)
        else:
            painter.fillRect(QRect(full.left(), full.top(), full.width(), sel.top() - full.top()), dim)
            painter.fillRect(QRect(full.left(), sel.bottom() + 1, full.width(), full.bottom() - sel.bottom()), dim)
            painter.fillRect(QRect(full.left(), sel.top(), sel.left() - full.left(), sel.height()), dim)
            painter.fillRect(QRect(sel.right() + 1, sel.top(), full.right() - sel.right(), sel.height()), dim)
            painter.fillRect(sel, QColor(0, 0, 0, 1))

            # 选区边框 + 四角对焦标 (与取景框风格一致)
            painter.setPen(QPen(QColor(56, 189, 248, 120), 1.0, Qt.PenStyle.DashLine))
            painter.drawRect(sel)
            painter.setPen(QPen(QColor(56, 189, 248, 230), 2.0))
            s = 16
            l, t, r, b = sel.left(), sel.top(), sel.right(), sel.bottom()
            for (ax, ay, dx, dy) in ((l, t, 1, 1), (r, t, -1, 1), (l, b, 1, -1), (r, b, -1, -1)):
                painter.drawLine(ax, ay, ax + dx * s, ay)
                painter.drawLine(ax, ay, ax, ay + dy * s)

            # 尺寸提示
            painter.setFont(QFont("Segoe UI", 9))
            painter.setPen(QColor(226, 232, 240))
            label_y = t - 8 if t > 24 else b + 18
            painter.drawText(l, label_y, f"{sel.width()} × {sel.height()}")

        # 顶部操作提示
        if sel is None:
            hint = "拖动鼠标框选要翻译的区域   ·   Esc / 右键 取消"
            painter.setFont(QFont("Microsoft YaHei", 11))
            fm = painter.fontMetrics()
            geo = QGuiApplication.screenAt(QCursor.pos())
            area = geo.geometry().translated(-self._desktop.topLeft()) if geo else full
            w = fm.horizontalAdvance(hint) + 40
            box = QRect(area.center().x() - w // 2, area.top() + 40, w, 40)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(15, 23, 42, 230))
            painter.drawRoundedRect(box, 20, 20)
            painter.setPen(QColor(241, 245, 249))
            painter.drawText(box, int(Qt.AlignmentFlag.AlignCenter), hint)
