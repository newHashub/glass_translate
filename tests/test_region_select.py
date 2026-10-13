"""框选翻译功能测试：选区规整、误触过滤、选中后取景框吸附并触发识别。"""
import pytest
from PyQt6.QtCore import QPoint, QPointF, QRect, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication

from config import config_manager
from region_select import RegionSelectOverlay, normalize_selection, is_valid_selection


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_normalize_selection_any_direction():
    # 从右下往左上拖，也应得到正向矩形
    r = normalize_selection(QPoint(300, 200), QPoint(100, 50))
    assert (r.x(), r.y(), r.width(), r.height()) == (100, 50, 200, 150)


def test_tiny_selection_rejected():
    assert not is_valid_selection(QRect(0, 0, 10, 10))
    assert is_valid_selection(QRect(0, 0, 200, 60))


def _mouse(kind, x, y, button=Qt.MouseButton.LeftButton):
    p = QPointF(x, y)
    buttons = button if kind != QMouseEvent.Type.MouseButtonRelease else Qt.MouseButton.NoButton
    return QMouseEvent(kind, p, p, p, button, buttons, Qt.KeyboardModifier.NoModifier)


def _drag(overlay, x0, y0, x1, y1):
    overlay.mousePressEvent(_mouse(QMouseEvent.Type.MouseButtonPress, x0, y0))
    overlay.mouseMoveEvent(_mouse(QMouseEvent.Type.MouseMove, x1, y1, Qt.MouseButton.NoButton))
    overlay.mouseReleaseEvent(_mouse(QMouseEvent.Type.MouseButtonRelease, x1, y1))


def test_overlay_emits_global_rect(qapp):
    ov = RegionSelectOverlay()
    got = []
    ov.region_selected.connect(got.append)
    _drag(ov, 400, 300, 100, 120)
    assert len(got) == 1
    r = got[0]
    origin = ov._desktop.topLeft()
    assert (r.x() - origin.x(), r.y() - origin.y(), r.width(), r.height()) == (100, 120, 300, 180)


def test_overlay_click_is_not_a_selection(qapp):
    ov = RegionSelectOverlay()
    got = []
    ov.region_selected.connect(got.append)
    _drag(ov, 100, 100, 104, 103)  # 单击/轻微抖动
    assert got == []
    assert not ov._finished, "误触后应继续等待用户拖拽，而不是直接关闭"


def test_overlay_right_click_cancels(qapp):
    ov = RegionSelectOverlay()
    cancelled = []
    ov.cancelled.connect(lambda: cancelled.append(True))
    ov.mousePressEvent(_mouse(QMouseEvent.Type.MouseButtonPress, 10, 10, Qt.MouseButton.RightButton))
    assert cancelled == [True]


def test_window_snaps_to_selection_and_triggers_scan(qapp, monkeypatch):
    import glass_window

    class FakeWorker:
        def __init__(self, *a, **k):
            self.calls = []
            self.result_ready = self.status_changed = self.error_occurred = _Sig()
        def start(self): pass
        def set_moving(self, v): self.calls.append(("moving", v))
        def notify_new_position(self, r): self.calls.append(("pos", r))
        def trigger_once(self, r): self.calls.append(("trigger", r))
        def stop(self): pass

    class _Sig:
        def connect(self, *a): pass

    monkeypatch.setattr(glass_window, "TranslationWorker", FakeWorker)
    monkeypatch.setattr(config_manager, "save", lambda: None)
    win = glass_window.GlassWindow()
    win.start_region_select()
    assert not win.isVisible(), "框选时取景框应先隐藏，避免被截进画面"
    overlay = win._region_overlay
    _drag(overlay, 200, 150, 700, 400)

    o = overlay._desktop.topLeft()
    g = win.geometry()
    assert (g.x(), g.y(), g.width(), g.height()) == (o.x() + 200, o.y() + 150, 500, 250)
    assert win.isVisible()
    assert ("trigger", (g.x(), g.y(), 500, 250)) in win.worker.calls
    assert win._region_overlay is None
