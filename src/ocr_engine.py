import asyncio
import re
from typing import List, Optional, Tuple, Dict, Any
from PIL import Image, ImageEnhance


class OcrEngine:
    """Windows 原生硬件加速 OCR 引擎，支持行级坐标提取与背景色自适应采样"""

    def __init__(self):
        self._available_languages: Optional[List[str]] = None
        # "自动" 模式下记住上一次识别成功的语言，下次优先尝试，避免每帧都多语言轮询
        self._auto_sticky_tag: Optional[str] = None

    @property
    def available_languages(self) -> List[str]:
        if self._available_languages is None:
            self._available_languages = self._detect_supported_languages()
        return self._available_languages

    def _detect_supported_languages(self) -> List[str]:
        try:
            import winrt.windows.media.ocr as ocr
            langs = [l.language_tag for l in ocr.OcrEngine.available_recognizer_languages]
            return langs
        except Exception:
            return ["en-US", "zh-Hans-CN"]

    def _resolve_lang_tag(self, source_lang: str) -> str:
        """根据用户选项映射为 Windows OCR 语言标签，支持任意系统语言包动态前缀匹配"""
        if not source_lang or source_lang == "auto":
            # auto 优先找英文或中文，找不到则选列表首个
            for tag in self.available_languages:
                if tag.lower().startswith("en"):
                    return tag
            for tag in self.available_languages:
                if "zh" in tag.lower() or "hans" in tag.lower():
                    return tag
            return self.available_languages[0] if self.available_languages else "en-US"

        prefix = source_lang.split("-")[0].lower()
        # 中文分支 (区分繁简)
        if prefix in ["zh", "chi"]:
            if any(k in source_lang.lower() for k in ["hant", "tw", "hk"]):
                for tag in self.available_languages:
                    if any(k in tag.lower() for k in ["hant", "tw", "hk"]):
                        return tag
            for tag in self.available_languages:
                if "hans" in tag.lower() or "zh" in tag.lower():
                    return tag
            return "zh-Hans-CN"

        # 动态前缀匹配 (en, ja, ko, fr, de, ru, es, it, pt, vi, etc.)
        for tag in self.available_languages:
            if tag.lower().startswith(prefix):
                return tag

        return self.available_languages[0] if self.available_languages else "en-US"

    def _sample_background_and_text_color(
        self, img: Image.Image, box: Tuple[float, float, float, float]
    ) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
        """
        采样文字周围的底色，并自动计算出高对比度的文字前景颜色
        """
        bx, by, bw, bh = box
        w_img, h_img = img.size
        sample_points = [
            (max(0, int(bx)), max(0, int(by - 2))),
            (min(w_img - 1, int(bx + bw)), max(0, int(by - 2))),
            (max(0, int(bx)), min(h_img - 1, int(by + bh + 2))),
            (min(w_img - 1, int(bx + bw)), min(h_img - 1, int(by + bh + 2))),
        ]

        rgb_list = []
        for sx, sy in sample_points:
            try:
                pixel = img.getpixel((sx, sy))
                if isinstance(pixel, (tuple, list)) and len(pixel) >= 3:
                    rgb_list.append((pixel[0], pixel[1], pixel[2]))
            except Exception:
                pass

        if rgb_list:
            avg_r = sum(c[0] for c in rgb_list) // len(rgb_list)
            avg_g = sum(c[1] for c in rgb_list) // len(rgb_list)
            avg_b = sum(c[2] for c in rgb_list) // len(rgb_list)
        else:
            avg_r, avg_g, avg_b = (245, 245, 245)

        brightness = (avg_r * 299 + avg_g * 587 + avg_b * 114) / 1000
        if brightness > 130:
            # 浅色底色（如网页白底）：背景偏白，文字为深色
            bg_rgb = (avg_r, avg_g, avg_b)
            text_rgb = (15, 23, 42)
        else:
            # 深色底色（如深色模式或游戏）：背景偏深，文字为纯白/浅色
            bg_rgb = (avg_r, avg_g, avg_b)
            text_rgb = (248, 250, 252)

        return bg_rgb, text_rgb

    def clean_and_merge_lines(self, raw_lines: List[str], is_cjk: bool = False) -> str:
        """清洗并将 OCR 折行断句自然拼接为连贯段落，同时严密保护物理换行"""
        cleaned_lines = [line.strip() for line in raw_lines if line.strip()]
        if not cleaned_lines:
            return ""

        merged = []
        for line in cleaned_lines:
            if not merged:
                merged.append(line)
                continue

            last = merged[-1]
            if last.endswith("-"):
                # 连字符折行断词 (如 sen- / tence)
                merged[-1] = last[:-1] + line
            elif is_cjk:
                # 中日文字符判定
                if re.search(r"[。！？!?；;：:]$", last):
                    merged.append(line)
                else:
                    merged[-1] = last + line
            else:
                # 判定当前行是否是独立的新换行项：
                # 1. 上一行以句末标点结尾
                is_terminal = bool(re.search(r"[.?!:：。！？;；]$", last))
                # 2. 当前行以列表标识开头 (如 1. / 1) / - / * / •)
                is_list_item = bool(re.match(r"^(\d+[\.\)]|[-*•])\s+", line))
                # 3. 上一行很短 (<= 35 字符) 且当前行以大写字母开头 (通常是标题、独立段落、列表短句)
                is_short_and_capital = len(last) <= 35 and line[0].isupper()

                if is_terminal or is_list_item or is_short_and_capital:
                    merged.append(line)
                elif line[0].islower() and len(last) > 35:
                    # 仅当上一行较长 (屏幕右侧回流折行) 且下一行以小写字母接续时，才视为同一句折行拼接
                    merged[-1] = last + " " + line
                else:
                    merged.append(line)

        return "\n".join(merged)

    # ---------------- "自动" 源语言的多识别器探测 ----------------
    _RE_CJK = re.compile(r"[\u4e00-\u9fff]")
    _RE_KANA = re.compile(r"[\u3040-\u30ff]")
    _RE_HANGUL = re.compile(r"[\uac00-\ud7af]")
    _RE_LATIN_WORD = re.compile(r"[A-Za-z]+")

    @classmethod
    def script_score(cls, text: str, lang_tag: str) -> float:
        """评估识别结果与识别器语种的吻合度 (0~1)。
        Windows OCR 是单语识别器：用英文模型读日文时会输出零碎的乱码字母，
        用日文模型读日文时则会输出大量假名/汉字，据此判断哪个识别器"读懂了"。"""
        chars = [c for c in text if not c.isspace()]
        if not chars:
            return 0.0
        n = float(len(chars))
        tag = lang_tag.lower()
        if tag.startswith("ja"):
            kana = len(cls._RE_KANA.findall(text))
            han = len(cls._RE_CJK.findall(text))
            # 没有假名时更可能是中文：压低到采纳阈值以下，让中文识别器参与比较
            return (kana + han) / n * (1.0 if kana > 0 else 0.5)
        if tag.startswith("zh"):
            return len(cls._RE_CJK.findall(text)) / n
        if tag.startswith("ko"):
            return len(cls._RE_HANGUL.findall(text)) / n
        # 拉丁语系：统计"像真实单词"的字母比例 (长度>=2 且含元音)
        good = 0
        for w in cls._RE_LATIN_WORD.findall(text):
            if len(w) >= 2 and re.search(r"[aeiouyAEIOUY]", w):
                good += len(w)
            elif w.lower() in ("a", "i"):
                good += 1
        return good / n

    def _auto_candidates(self) -> List[str]:
        """自动模式下按优先级排列的候选识别器：上次成功 > 英文 > 日文 > 简体中文 > 韩文"""
        langs = self.available_languages
        order: List[str] = []

        def pick(pred):
            for tag in langs:
                if pred(tag.lower()) and tag not in order:
                    order.append(tag)
                    return

        if self._auto_sticky_tag and self._auto_sticky_tag in langs:
            order.append(self._auto_sticky_tag)
        pick(lambda t: t.startswith("en"))
        pick(lambda t: t.startswith("ja"))
        pick(lambda t: t.startswith("zh") and not any(k in t for k in ("hant", "tw", "hk")))
        pick(lambda t: t.startswith("ko"))
        if not order:
            order.append(langs[0] if langs else "en-US")
        return order

    def _run_ocr(self, img: Image.Image, lang_tag: str):
        """调用一次 Windows OCR，返回 winocr 结果对象 (失败抛异常)"""
        import winocr
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(winocr.recognize_pil(img, lang_tag))
        finally:
            loop.close()

    @staticmethod
    def _result_text(res) -> str:
        return "\n".join(l.text.strip() for l in getattr(res, "lines", []) if l.text.strip())

    AUTO_ACCEPT_SCORE = 0.6

    def _recognize_auto(self, img: Image.Image):
        """自动模式：先试最可能的识别器，结果可信则直接采用；
        否则依次尝试其他已安装的识别器，取吻合度最高者，并记住它供下一帧优先使用。"""
        best = None  # (score, tag, res)
        for tag in self._auto_candidates():
            try:
                res = self._run_ocr(img, tag)
            except Exception as e:
                print(f"[OcrEngine] 识别器 {tag} 异常: {e}")
                continue
            text = self._result_text(res)
            if not text:
                continue
            score = self.script_score(text, tag)
            if best is None or score > best[0]:
                best = (score, tag, res)
            if score >= self.AUTO_ACCEPT_SCORE:
                break
        if best is None:
            return None, self._auto_candidates()[0]
        self._auto_sticky_tag = best[1]
        return best[2], best[1]

    def recognize(
        self, img: Image.Image, source_lang: str = "auto"
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        执行 OCR 文字识别。
        返回: (merged_text, blocks)
        blocks 包含每个文本行的物理矩形坐标、文本内容以及自适应背景/文字颜色。
        "自动" 源语言下会在已安装的 英/日/中/韩 识别器中自动挑选读得懂的那一个。
        """
        try:
            if not source_lang or source_lang == "auto":
                res, lang_tag = self._recognize_auto(img)
                if res is None:
                    return "", []
            else:
                lang_tag = self._resolve_lang_tag(source_lang)
                res = self._run_ocr(img, lang_tag)

            blocks: List[Dict[str, Any]] = []
            raw_lines: List[str] = []

            for line in res.lines:
                text = line.text.strip()
                if not text:
                    continue

                raw_lines.append(text)

                # 计算该行文字在物理图像中的外接矩形
                if hasattr(line, "words") and line.words:
                    xs = [w.bounding_rect.x for w in line.words]
                    ys = [w.bounding_rect.y for w in line.words]
                    x2s = [w.bounding_rect.x + w.bounding_rect.width for w in line.words]
                    y2s = [w.bounding_rect.y + w.bounding_rect.height for w in line.words]
                    bx = min(xs)
                    by = min(ys)
                    bw = max(x2s) - bx
                    bh = max(y2s) - by
                else:
                    # 回退
                    bx, by, bw, bh = (0.0, 0.0, float(img.width), 20.0)

                box = (bx, by, bw, bh)
                bg_rgb, text_rgb = self._sample_background_and_text_color(img, box)

                blocks.append({
                    "text": text,
                    "box": box,
                    "bg_rgb": bg_rgb,
                    "text_rgb": text_rgb,
                    "translated": "",
                })

            is_cjk = any(k in lang_tag.lower() for k in ("zh", "ja"))  # 韩文词间有空格，按拉丁规则拼接
            merged_text = self.clean_and_merge_lines(raw_lines, is_cjk=is_cjk)
            return merged_text, blocks
        except Exception as e:
            print(f"[OcrEngine] 识别异常: {e}")
            return "", []
