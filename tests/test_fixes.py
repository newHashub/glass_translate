"""回归测试：覆盖 CODE_REVIEW.md 中三个 P0 问题的修复。全部离线运行，不访问网络。"""
from types import SimpleNamespace

import pytest
from PIL import Image

from config import config_manager
from ocr_engine import OcrEngine
from translator_engine import TranslatorEngine


# ---------------------------------------------------------------------------
# P0-1  行级缓存必须按 引擎 + 语言对 隔离
# ---------------------------------------------------------------------------
FAKE_DICT = {
    ("Hello world", "zh-CN"): "你好世界",
    ("Hello world", "ja"): "こんにちは世界",
    ("Hello world", "en"): "Hello world",
}


@pytest.fixture
def offline_translator(monkeypatch):
    t = TranslatorEngine()
    calls = []

    def fake_chunk(text, src, tgt):
        calls.append((text, src, tgt))
        return FAKE_DICT.get((text, tgt), "")

    monkeypatch.setattr(t, "_translate_single_chunk", fake_chunk)
    monkeypatch.setitem(config_manager.config, "engine", "youdao")
    return t, calls


def test_line_cache_isolated_by_target_language(offline_translator):
    t, calls = offline_translator
    assert t.translate("Hello world", "en", "zh-CN") == "你好世界"
    # 切换到日文目标语言：不能复用中文译文，必须重新请求
    assert t.translate("Hello world", "en", "ja") == "こんにちは世界"
    assert len(calls) == 2
    assert t.get_line_translation("Hello world", "en", "zh-CN") == "你好世界"
    assert t.get_line_translation("Hello world", "en", "ja") == "こんにちは世界"
    assert t.get_line_translation("Hello world", "en", "ko") is None


def test_line_cache_isolated_by_engine(offline_translator, monkeypatch):
    t, _ = offline_translator
    t.set_line_translation("Hello world", "你好世界", "en", "zh-CN")
    monkeypatch.setitem(config_manager.config, "engine", "openai")
    assert t.get_line_translation("Hello world", "en", "zh-CN") is None


def test_line_cache_no_duplicate_keys(offline_translator):
    t, _ = offline_translator
    for _ in range(5):
        t.set_line_translation("Hello world", "你好世界", "en", "zh-CN")
    assert len(t._line_cache_keys) == 1


# ---------------------------------------------------------------------------
# P0-2  框内文字消失后应清空旧译文；文字不变时不重复翻译
# ---------------------------------------------------------------------------
class _FakeCapture:
    def capture_screen_rect(self, x, y, w, h):
        return Image.new("RGB", (w, h), (255, 255, 255))

    def check_has_changed(self, img, rect):
        return True  # 模拟画面一直在变 (如背景视频)

    def force_reset(self):
        pass


def _run_worker(monkeypatch, ocr_sequence, translator):
    import worker as worker_mod
    from worker import TranslationWorker

    monkeypatch.setattr(worker_mod.time, "sleep", lambda s: None)
    w = TranslationWorker()
    w.capture_engine = _FakeCapture()
    w.translator_engine = translator
    seq = list(ocr_sequence)

    class _FakeOcr:
        def recognize(self, img, source_lang="auto"):
            if len(seq) == 1:
                w._running = False  # 最后一帧：处理完本轮后退出循环
                return seq[0]
            return seq.pop(0)

    w.ocr_engine = _FakeOcr()
    w._target_rect = (0, 0, 400, 200)
    results = []
    w.result_ready.connect(lambda o, t, b, s: results.append((o, t)))
    w.run()  # 直接在当前线程跑循环，OCR 序列耗尽后自动退出
    return results


def _block(text):
    return {"text": text, "box": (0, 0, 120, 20), "bg_rgb": (255, 255, 255),
            "text_rgb": (0, 0, 0), "translated": ""}


def test_overlay_cleared_when_text_disappears(qapp, monkeypatch, offline_translator):
    t, _ = offline_translator
    monkeypatch.setitem(config_manager.config, "target_lang", "zh-CN")
    monkeypatch.setitem(config_manager.config, "source_lang", "en")
    results = _run_worker(monkeypatch, [("Hello world", [_block("Hello world")]), ("", [])], t)
    assert results[0] == ("Hello world", "你好世界")
    assert results[-1] == ("", ""), "文字消失后应发出清空信号，否则旧译文会残留"


def test_same_text_not_retranslated(qapp, monkeypatch, offline_translator):
    t, calls = offline_translator
    monkeypatch.setitem(config_manager.config, "target_lang", "zh-CN")
    monkeypatch.setitem(config_manager.config, "source_lang", "en")
    frames = [("Hello world", [_block("Hello world")])] * 4
    results = _run_worker(monkeypatch, frames, t)
    assert len(calls) == 1
    assert len(results) == 1, "文字未变时不应反复刷新界面"


@pytest.fixture
def qapp():
    from PyQt6.QtCore import QCoreApplication
    app = QCoreApplication.instance() or QCoreApplication([])
    yield app


# ---------------------------------------------------------------------------
# P0-3  "自动" 源语言应能识别日文 / 中文 / 韩文
# ---------------------------------------------------------------------------
def _fake_res(*lines):
    return SimpleNamespace(lines=[SimpleNamespace(text=l, words=[]) for l in lines])


def _fake_ocr(engine, monkeypatch, outputs):
    called = []

    def run(img, tag):
        called.append(tag)
        return _fake_res(*outputs.get(tag, []))

    monkeypatch.setattr(engine, "_run_ocr", run)
    return called


@pytest.fixture
def ocr(monkeypatch):
    e = OcrEngine()
    e._available_languages = ["en-US", "ja-JP", "zh-Hans-CN", "ko-KR"]
    return e


IMG = Image.new("RGB", (300, 100), (255, 255, 255))


def test_auto_english_uses_single_pass(ocr, monkeypatch):
    called = _fake_ocr(ocr, monkeypatch, {"en-US": ["The quick brown fox jumps over the lazy dog."]})
    text, blocks = ocr.recognize(IMG, "auto")
    assert "quick brown fox" in text
    assert called == ["en-US"], "英文画面不应额外尝试其他识别器"


def test_auto_detects_japanese(ocr, monkeypatch):
    called = _fake_ocr(ocr, monkeypatch, {
        "en-US": ["l1 ~ ,. Il"],                     # 英文模型读日文 → 乱码
        "ja-JP": ["勇者よ、この扉の先には"],
        "zh-Hans-CN": ["勇者", "扉先"],
    })
    text, blocks = ocr.recognize(IMG, "auto")
    assert text == "勇者よ、この扉の先には"
    assert ocr._auto_sticky_tag == "ja-JP"
    # 下一帧优先使用日文识别器，一次即成功
    called.clear()
    ocr.recognize(IMG, "auto")
    assert called == ["ja-JP"]


def test_auto_detects_korean(ocr, monkeypatch):
    _fake_ocr(ocr, monkeypatch, {"en-US": ["O1 0"], "ko-KR": ["용사여, 이 문 너머에는"]})
    text, _ = ocr.recognize(IMG, "auto")
    assert text.startswith("용사여")


def test_auto_prefers_chinese_over_japanese_without_kana(ocr, monkeypatch):
    _fake_ocr(ocr, monkeypatch, {
        "en-US": [""], "ja-JP": ["现代操作系统内置"], "zh-Hans-CN": ["现代操作系统内置了引擎"],
    })
    text, _ = ocr.recognize(IMG, "auto")
    assert ocr._auto_sticky_tag == "zh-Hans-CN"


def test_explicit_language_skips_detection(ocr, monkeypatch):
    called = _fake_ocr(ocr, monkeypatch, {"ja-JP": ["こんにちは"]})
    ocr.recognize(IMG, "ja")
    assert called == ["ja-JP"]
