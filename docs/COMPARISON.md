# GlassTranslate 与同类工具对比

> 整理于 2026 年 10 月，信息来自各项目公开页面，功能与价格可能随版本变化，以官方为准。

屏幕实时翻译在 Windows 上已经有不少成熟方案。下面按「译文显示方式」把常见工具分成三类，方便你判断 GlassTranslate 是否适合自己的场景。

## 一、原地覆盖类（译文压回原文位置）

| 工具 | 开源 / 价格 | 特点 |
| :--- | :--- | :--- |
| **GlassTranslate** | 开源 (MIT)，免费 | 可随手拖动、8 向缩放、滚轮缩放的透明取景框；行级语义缓存，挪开再放回 0 次请求；约 0.6 秒启动，分发包约 36 MB |
| [爱译客 Gaminik](https://apps.apple.com/cn/app/id6779198056) | 商业，免费额度 + 会员（约 $3.25/月、$49.99 终身） | 擦除原文修补底色、匹配字色字号；漫画气泡识别、竖排日文重排、术语词库；Windows / macOS / 安卓 |
| [WinLens](https://github.com/marco-beltrame/WinLens) | 开源，免费 | 「Windows 版 Google Lens」，热键截屏后原地覆盖译文，匹配背景与字体 |
| [AFK Live Translate](https://www.producthunt.com/p/afklivetranslate) | 免费 + 自带 Key | 框选区域原地替换，术语表、缓存、可接 DeepL / Azure / LibreTranslate |
| [ScreenTranslator](https://booth.pm/en/items/8487391) | 付费（¥500，3 天试用） | 框选翻译 + 实时模式，支持全离线翻译（日↔英） |
| [OverTranslate](https://github.com/Hon-Lu/OverTranslate) | 开源，免费 | 区域持续识别，在原位置更新译文，区分字幕/漫画与游戏 UI 两种模式 |

## 二、翻译框类（译文显示在独立窗口）

| 工具 | 开源 / 价格 | 特点 |
| :--- | :--- | :--- |
| [团子翻译器](https://github.com/OverTM/PantsuDango.Dango-Translator) | 开源，免费（在线 OCR 有额度） | 国内最流行的游戏 OCR 翻译器；本地 / 在线 / 漫画 OCR，竖排识别，鼠标穿透，15+ 翻译源 |
| [Translumo](https://github.com/ramjke/Translumo) | 开源 (Apache 2.0)，免费 | 多 OCR 引擎并行 + 模型择优；可选 EasyOCR（需 NVIDIA 显卡），完整包约 477 MB |
| [Pot](https://github.com/pot-app/pot-desktop) | 开源，免费 | 划词翻译 / 截图翻译 / 剪贴板监听，多引擎并排对比，插件系统；非实时取景 |

## 三、文本钩取类（直接从游戏进程读取文字）

| 工具 | 开源 / 价格 | 特点 |
| :--- | :--- | :--- |
| [LunaTranslator](https://github.com/HIllya51/LunaTranslator) | 开源，免费 | 视觉小说首选；Hook + OCR + 剪贴板三种取词，40+ 翻译引擎，部分引擎可把译文嵌回游戏 |
| Textractor | 开源，免费 | 经典文本钩取工具，原版已基本停更 |

钩取方案拿到的是渲染前的原始字符串，**不存在识别错误**，但只对特定游戏引擎有效；OCR 方案（包括 GlassTranslate）对任何画面都通用，但精度受字体和背景影响。两者常常搭配使用。详见 [Text hooking vs OCR](https://playto.dev/blog/ocr-vs-text-hooker/)。

## GlassTranslate 适合谁

**更适合：**

- 浏览外文网页、技术文档、软件界面，想「看哪框哪」，不想先设置区域再开自动翻译的人；
- 在意启动速度和资源占用、希望免安装、免 Key 即开即用的人；
- 需要反复来回查看同一段内容的场景（行级缓存让二次显示几乎零延迟）。

**目前不如别人的地方：**

- 不支持文本钩取，玩视觉小说时精度不如 LunaTranslator；
- 没有术语词库、漫画气泡与竖排日文重排，这些方面 Gaminik 做得更细；
- 「自动」源语言下 OCR 默认按英文识别，识别日文 / 韩文时需要手动选择对应语言；
- 默认翻译通道依赖有道网页接口，稳定性无法保证，重要场景建议配置自定义大模型 API。
