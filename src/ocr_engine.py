import asyncio
import re
from typing import List, Optional, Tuple, Dict, Any
from PIL import Image, ImageEnhance


class OcrEngine:
    """Windows 原生硬件加速 OCR 引擎，支持行级坐标提取与背景色自适应采样"""

    def __init__(self):
        self._available_languages: Optional[List[str]] = None

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

    def recognize(
        self, img: Image.Image, source_lang: str = "auto"
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        执行 OCR 文字识别。
        返回: (merged_text, blocks)
        blocks 包含每个文本行的物理矩形坐标、文本内容以及自适应背景/文字颜色。
        """
        lang_tag = self._resolve_lang_tag(source_lang)

        try:
            import winocr
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                res = loop.run_until_complete(winocr.recognize_pil(img, lang_tag))
            finally:
                loop.close()

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

            is_cjk = "zh" in lang_tag.lower() or "ja" in lang_tag.lower()
            merged_text = self.clean_and_merge_lines(raw_lines, is_cjk=is_cjk)
            return merged_text, blocks
        except Exception as e:
            print(f"[OcrEngine] 识别异常: {e}")
            return "", []
