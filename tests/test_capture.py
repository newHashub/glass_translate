import pytest
import sys
from PIL import Image, ImageDraw
from PyQt6.QtWidgets import QApplication
from capture_engine import CaptureEngine


def test_capture_and_diff():
    # 确保存在 QApplication 实例
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    engine = CaptureEngine(diff_threshold=2.0)

    # 创建第一张图像
    img1 = Image.new("RGB", (200, 200), color=(255, 255, 255))
    draw1 = ImageDraw.Draw(img1)
    draw1.rectangle([10, 10, 50, 50], fill=(0, 0, 0))

    rect = (100, 100, 200, 200)

    # 首次检查：视为有变化
    changed1 = engine.check_has_changed(img1, rect)
    assert changed1 is True

    # 画面未变化再次检查：应返回 False (节约算力)
    changed2 = engine.check_has_changed(img1, rect)
    assert changed2 is False

    # 画面发生大幅变动
    img2 = Image.new("RGB", (200, 200), color=(0, 0, 0))
    changed3 = engine.check_has_changed(img2, rect)
    assert changed3 is True
    print("\n[Test Capture] 画面变动差分检测正常")
