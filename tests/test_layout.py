import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from glass_window import layout_text_blocks
from config import config_manager
from global_hotkey import GlobalHotkeyThread

@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app


def test_layout_text_blocks_font_size(qapp):
    blocks = [
        {"box": (10, 10, 100, 14), "translated": "这是小号文字测试", "bg_rgb": (255, 255, 255), "text_rgb": (0, 0, 0)},
        {"box": (10, 30, 200, 16), "translated": "这是第二行正常小字", "bg_rgb": (255, 255, 255), "text_rgb": (0, 0, 0)},
        {"box": (10, 60, 300, 36), "translated": "这是大标题测试", "bg_rgb": (255, 255, 255), "text_rgb": (0, 0, 0)},
    ]
    items = layout_text_blocks(blocks, cw=600, ch=400, iw=600, ih=400, font_scale=1.0)
    assert len(items) == 3

    # 小字行高 14px，字号应为 9~11px，绝不应膨胀到 20px
    font0 = items[0]["font"]
    assert 9 <= font0.pixelSize() <= 12

    # 正常小字 16px，字号应为 10~13px
    font1 = items[1]["font"]
    assert 10 <= font1.pixelSize() <= 14

    # 大标题 36px，字号应明显大于小字
    font2 = items[2]["font"]
    assert font2.pixelSize() > font0.pixelSize()


def test_wheel_zoom_config():
    config_manager.set("wheel_zoom_enabled", True)
    assert config_manager.get("wheel_zoom_enabled") is True
    config_manager.set("wheel_zoom_enabled", False)
    assert config_manager.get("wheel_zoom_enabled") is False
    config_manager.set("wheel_zoom_enabled", True)


def test_hotkey_thread_lifecycle(qapp):
    th = GlobalHotkeyThread("R", True)
    th.start()
    assert th.isRunning()
    th.stop()
    assert not th.isRunning()


def test_show_status_pill_config():
    config_manager.set("show_status_pill", True)
    assert config_manager.get("show_status_pill") is True
    config_manager.set("show_status_pill", False)
    assert config_manager.get("show_status_pill") is False


def test_api_config_dialog_and_menu_sync(qapp):
    from glass_window import ApiConfigDialog
    from tray_manager import TrayManager
    from PyQt6.QtWidgets import QWidget

    class MockWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.refreshed = False
        def trigger_refresh(self):
            self.refreshed = True
        def apply_mode(self, mode):
            pass
        def copy_translation(self):
            pass
        def open_api_settings(self):
            pass
        def open_hotkey_settings(self):
            pass
        def reload_hotkey(self, hk):
            config_manager.set("hotkey_summon", hk)
        def set_auto_translate(self, b):
            pass
        def set_always_on_top(self, b):
            pass

    win = MockWindow()
    tray = TrayManager(win)

    # 测试修改引擎与同步
    tray._set_engine("youdao")
    assert config_manager.get("engine") == "youdao"
    tray._set_font_scale(1.15)
    assert abs(config_manager.get("font_scale") - 1.15) < 0.01
    tray._set_interval(200)
    assert config_manager.get("scan_interval_ms") == 200

    # 测试修改热键
    tray._set_hotkey("Alt+Q")
    assert config_manager.get("hotkey_summon") == "Alt+Q"

    # 测试 ApiConfigDialog 初始化与尺寸
    dlg = ApiConfigDialog(win)
    assert dlg.url_input.text()
    assert dlg.model_input.text()
    assert dlg.height() >= 400
    dlg.close()

    # 测试 HotkeyDialog 初始化
    from glass_window import HotkeyDialog
    from global_hotkey import parse_hotkey
    hk_dlg = HotkeyDialog(win)
    assert hk_dlg.hotkey_edit.text() == "Alt+Q"
    hk_dlg.close()

    # 测试热键解析器
    mods, vk = parse_hotkey("Ctrl+Alt+T")
    assert vk == ord("T")
    mods2, vk2 = parse_hotkey("F4")
    assert vk2 == 0x73


def test_multiline_cluster_and_boundary_constraint(qapp):
    from worker import cluster_blocks, wrap_text_to_lines
    from ocr_engine import OcrEngine

    # 1. 验证短句/标题换行不会被吞并为一个簇
    b1 = {"box": (10, 10, 120, 20), "text": "First title item"}
    b2 = {"box": (10, 40, 130, 20), "text": "Second title item"}
    clusters = cluster_blocks([b1, b2])
    assert len(clusters) == 2
    assert clusters == [[0], [1]]

    # 2. 验证 OCR clean_and_merge_lines 保持换行
    ocr = OcrEngine()
    merged = ocr.clean_and_merge_lines(["First line", "Second line"])
    assert "\n" in merged

    # 3. 验证超长文本在 layout_text_blocks 中被窗口右边界安全约束
    b_long = {"box": (10, 10, 100, 20), "translated": "这是一段非常非常长的翻译文本，测试它会不会无限向右延伸超出取景框边界", "bg_rgb": (255, 255, 255), "text_rgb": (0, 0, 0)}
    items = layout_text_blocks([b_long], cw=300, ch=200, iw=300, ih=200)
    assert len(items) == 1
    # 确保 pad_rect.right() <= 窗口宽度 cw (300)
    assert items[0]["pad_rect"].right() <= 300.0



