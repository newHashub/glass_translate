import pytest
from translator_engine import TranslatorEngine


def test_translator_cache_and_dispatch():
    translator = TranslatorEngine()
    test_text = "Good morning, this is a fast translation test."
    
    # 第一次翻译
    res1 = translator.translate(test_text, src_lang="en", tgt_lang="zh-CN")
    assert res1 and len(res1) > 0
    print(f"\n[Test Translator] 第一次翻译结果: {res1}")

    # 第二次翻译：应命中缓存
    res2 = translator.translate(test_text, src_lang="en", tgt_lang="zh-CN")
    assert res2 == res1
    print(f"[Test Translator] 缓存命中成功: {res2}")


def test_empty_text_translation():
    translator = TranslatorEngine()
    res = translator.translate("   ", src_lang="en", tgt_lang="zh-CN")
    assert res == ""


def test_chunk_lines():
    translator = TranslatorEngine()
    lines = [f"This is line number {i}" for i in range(25)]
    chunks = translator._chunk_lines(lines, max_lines=10, max_chars=400)
    assert len(chunks) == 3
    assert len(chunks[0]) == 10
    assert len(chunks[1]) == 10
    assert len(chunks[2]) == 5


def test_long_text_translation():
    translator = TranslatorEngine()
    lines = "\n".join([f"Item {i}: Hello world" for i in range(20)])
    res = translator.translate(lines, src_lang="en", tgt_lang="zh-CN")
    assert res and len(res.splitlines()) > 0


def test_is_same_text_and_validation():
    from translator_engine import is_same_text, is_valid_translation

    s1 = "Le week-end, je ne vais pas à l’école."
    s2 = "  le week-end, je ne vais pas a l'ecole! \n"
    assert is_same_text("Hello World", "hello  world.")
    assert not is_valid_translation(s1, s1, "zh-CN")
    assert not is_valid_translation(s1, "MYMEMORY WARNING: QUERY LENGTH LIMIT", "zh-CN")
    assert not is_valid_translation(s1, "", "zh-CN")
    assert is_valid_translation(s1, "周末我不去上学。", "zh-CN")


def test_detect_language():
    from translator_engine import detect_language

    assert detect_language("Le week-end, je ne vais pas à l’école.") == "fr"
    assert detect_language("Guten Tag, wie geht es Ihnen?") == "de"
    assert detect_language("Привет мир, как дела?") == "ru"
    assert detect_language("こんにちは世界") == "ja"
    assert detect_language("안녕하세요") == "ko"
    assert detect_language("Hello everyone, how are you?") == "en"


def test_french_user_paragraph_translation():
    translator = TranslatorEngine()
    french_text = (
        "Le week-end, je ne vais pas à l’école. Je me réveille tard, généralement à neuf heures. "
        "Je prends un petit déjeuner avec ma famille. L’après-midi, je fais ce que j’aime. "
        "Parfois, je vais au parc avec mes amis, nous jouons ensemble. Parfois, je lis des livres "
        "ou regarde des films à la maison. Le soir, ma famille et moi mangeons un dîner délicieux. "
        "Nous parlons de nos journées heureuses. Le week-end est ma période préférée, "
        "parce que je peux me détendre et passer du temps avec mes proches."
    )
    res = translator.translate(french_text, src_lang="auto", tgt_lang="zh-CN")
    # 必须成功翻译出中文，且绝对不能等于原法语文本
    assert res and len(res) > 0
    assert "周末" in res or "上学" in res or "学校" in res
    assert not res.startswith("Le week-end")


def test_worker_validation_pipeline():
    from translator_engine import is_valid_translation

    blocks = [
        {"box": (10, 10, 100, 20), "text": "Le week-end, je ne vais pas à l’école.", "translated": ""},
        {"box": (10, 35, 100, 20), "text": "Je me réveille tard.", "translated": ""}
    ]
    target_lang = "zh-CN"

    # 场景1：若引擎异常返回了原文相同内容
    echoed_trans = ["Le week-end, je ne vais pas à l’école.", "Je me réveille tard."]
    valid_count = 0
    for i, b in enumerate(blocks):
        line_trans = echoed_trans[i]
        if line_trans and is_valid_translation(b["text"], line_trans, target_lang):
            b["translated"] = line_trans
            valid_count += 1
        else:
            b["translated"] = ""

    assert valid_count == 0
    assert blocks[0]["translated"] == ""
    assert blocks[1]["translated"] == ""

    # 场景2：若引擎正常返回了中文
    proper_trans = ["周末我不去上学。", "我起得很晚。"]
    valid_count = 0
    for i, b in enumerate(blocks):
        line_trans = proper_trans[i]
        if line_trans and is_valid_translation(b["text"], line_trans, target_lang):
            b["translated"] = line_trans
            valid_count += 1
        else:
            b["translated"] = ""

    assert valid_count == 2
    assert blocks[0]["translated"] == "周末我不去上学。"
    assert blocks[1]["translated"] == "我起得很晚。"


def test_line_level_cache_and_shift_reuse():
    from translator_engine import TranslatorEngine, norm_line_key

    translator = TranslatorEngine()
    # 预存翻译行
    translator.set_line_translation("Le week-end, je ne vais pas à l’école.", "周末我不去上学。")
    translator.set_line_translation("Je me réveille tard.", "我起得很晚。")

    # 1. 验证标点与空白轻微变动时的行级归一化匹配
    assert translator.get_line_translation("  le week-end, je ne vais pas a l'école! ") == "周末我不去上学。"
    assert translator.get_line_translation("Je me réveille tard... ") == "我起得很晚。"

    # 2. 验证多行微移装配：即使整体文本是新的组合，也能 0ms 瞬间从行级缓存装配
    shifted_text = "Je me réveille tard.\nLe week-end, je ne vais pas à l’école."
    assembled = translator.translate(shifted_text, src_lang="auto", tgt_lang="zh-CN")
    assert assembled == "我起得很晚。\n周末我不去上学。"


def test_user_long_multi_paragraph_translation():
    text = (
        "You want to change your life.\n"
        "Like really bad.\n"
        "You’re tired of where you are. You’re tired of your physique, or how your mind is not your friend, or how you have to stress over not being able to pay the bills each month, or how you’re going to end up alone.\n"
        "You finally gain the motivation to start in the gym, start the business, start talking to more people, you know the drill.\n"
        "Fast forward 2-4 weeks and nothing has changed.\n"
        "You don’t even know how it happened... you just ended up back in your old life without making any progress.\n"
        "And this isn’t the first time. You lock in, fall off, lock in again, fall off, and 10 years go by (for some people, their entire life goes by) without breaking the habit of being your worst self.\n"
        "It sucks."
    )
    engine = TranslatorEngine()
    res = engine.translate(text, "en", "zh-CN")
    res_lines = res.splitlines()
    assert len(res_lines) == 8
    assert "这已经不是第一次" in res_lines[6] or "第一次" in res_lines[6]
    assert len(res_lines[7]) > 0


def test_user_wrapped_paragraphs_and_clustering():
    from worker import cluster_blocks, wrap_text_to_lines
    from translator_engine import is_valid_translation

    # 模拟真实屏幕上因折行导致的 14 个物理视觉行块
    mock_blocks = [
        {"box": (20, 26, 225, 20), "text": "Because, well, frankly, you didn’t."},
        {"box": (20, 50, 154, 20), "text": "You didn’t actually try."},
        {"box": (20, 74, 136, 20), "text": "So what do you do?"},
        {"box": (20, 98, 585, 20), "text": "If you look at the top athletes, startup founders, visionaries, and strategists who seem"},
        {"box": (20, 122, 567, 20), "text": "to work 16 hours a day without breaking a sweat, do you think they struggle to do"},
        {"box": (20, 146, 34, 20), "text": "that?"},
        {"box": (20, 170, 221, 20), "text": "Or is that what they want to do?"},
        {"box": (20, 194, 564, 20), "text": "Is it actually hard for them? No. In fact, it’s extremely hard for them to do what the"},
        {"box": (20, 218, 570, 20), "text": "average person does. It’s a living hell for them to even sense that they’re devolving"},
        {"box": (20, 242, 135, 20), "text": "into a mediocre life."},
        {"box": (20, 266, 238, 20), "text": "Why? Because that’s who they are."},
        {"box": (20, 290, 280, 20), "text": "How do we replicate this in our own life?"},
        {"box": (20, 314, 69, 20), "text": "Buckle up."},
        {"box": (20, 338, 97, 20), "text": "It gets bumpy."}
    ]

    clusters = cluster_blocks(mock_blocks)
    assert len(clusters) == 10  # 14 行精准聚类为 10 个自然句/段

    cluster_sentences = [" ".join([mock_blocks[i]["text"] for i in cl]) for cl in clusters]
    payload = "\n".join(cluster_sentences)

    engine = TranslatorEngine()
    translated_all = engine.translate(payload, "en", "zh-CN")
    trans_lines = translated_all.splitlines()

    assert len(trans_lines) == len(clusters)

    for cl, t_sent in zip(clusters, trans_lines):
        c_blocks = [mock_blocks[i] for i in cl]
        widths = [b["box"][2] for b in c_blocks]
        wrapped_subs = wrap_text_to_lines(t_sent.strip(), widths)
        for b_idx, sub_t in zip(cl, wrapped_subs):
            mock_blocks[b_idx]["translated"] = sub_t

    valid_count = sum(1 for b in mock_blocks if b.get("translated") and is_valid_translation(b["text"], b["translated"], "zh-CN"))
    assert valid_count == 14  # 14 个块全部成功得到有效中文翻译，100% 覆盖零漏行
    assert "颠簸" in mock_blocks[13]["translated"] or len(mock_blocks[13]["translated"]) > 0


def test_map_youdao_type_and_multilingual_validation():
    from translator_engine import map_youdao_type, is_valid_translation

    assert map_youdao_type("auto", "zh-CN") == "AUTO"
    assert map_youdao_type("en", "zh-CN") == "EN2ZH_CN"
    assert map_youdao_type("zh", "en") == "ZH_CN2EN"
    assert map_youdao_type("ja", "zh-CN") == "JA2ZH_CN"
    assert map_youdao_type("zh", "ja") == "ZH_CN2JA"
    assert map_youdao_type("ko", "zh-CN") == "KR2ZH_CN"
    assert map_youdao_type("fr", "zh-CN") == "FR2ZH_CN"

    # 多语言验证测试
    # 目标为英文时：原文是中文，译文如果仍是中文，无效
    assert not is_valid_translation("你好世界", "你好世界", "en")
    assert is_valid_translation("你好世界", "Hello world", "en")

    # 目标为日文时：原文是中文，译文如果是日文，有效
    assert is_valid_translation("你好", "こんにちは", "ja")

    # 目标为韩文时：原文是英文，译文是韩文，有效
    assert is_valid_translation("Hello", "안녕하세요", "ko")





