import pytest
from PIL import Image, ImageDraw
from ocr_engine import OcrEngine


def test_ocr_recognition():
    engine = OcrEngine()
    # 创建包含清晰英文字符的测试图片
    img = Image.new("RGB", (400, 120), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "GlassTranslate Engine 2026", fill=(0, 0, 0))
    draw.text((20, 60), "Realtime OCR on Windows", fill=(0, 0, 0))

    merged_text, raw_lines = engine.recognize(img, source_lang="en")

    assert len(raw_lines) >= 1
    assert "GlassTranslate" in merged_text or "Engine" in merged_text or "Windows" in merged_text
    print(f"\n[Test OCR] 成功识别: {merged_text}")


def test_clean_and_merge_lines():
    engine = OcrEngine()
    raw = [
        "This is the first part of a very long sen-",
        "tence that continues on the second line.",
        "Here is another separate sentence."
    ]
    merged = engine.clean_and_merge_lines(raw, is_cjk=False)
    assert "sentence that" in merged
    assert "Here is another" in merged
