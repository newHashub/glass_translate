# 🪟 GlassTranslate

<div align="center">

**简体中文** • [English](docs/README_EN.md) • [日本語](docs/README_JA.md) • [한국어](docs/README_KO.md)

![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D4?logo=windows)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**一块透明的翻译玻璃：放在外文上，译文直接显示在原文的位置。**

<a href="docs/assets/GlassTranslate-Promo.mp4">
  <img src="docs/assets/preview.gif" alt="GlassTranslate 演示" width="860" />
</a>

[▶️ 观看完整演示视频（46 秒）](docs/assets/GlassTranslate-Promo.mp4)

</div>

GlassTranslate 是一个 Windows 屏幕实时翻译工具。它是一个没有边框的透明取景框，拖到哪里，框里的外文就被译文覆盖在哪里，原本的画面不会被弹窗挡住。适合看外文网页和文档、玩没有汉化的游戏、看生肉视频。

## 功能

- **原地翻译**：识别每一行文字的位置，取周围的底色，把译文画在原文上方。
- **随手拖动**：在框内按住左键拖动，四边可以缩放，滚轮以鼠标为中心缩放。松手后自动重新识别。
- **框选翻译**：按 `Alt + S`，像截图一样拖出一块区域，取景框直接贴上去翻译。
- **自动识别语言**：在已安装的英、日、中、韩 OCR 中自动选择，韩文、日文夹杂英文也能识别。
- **免 Key 即用**：默认使用有道网页通道；也可以接入 DeepSeek、OpenAI 或本地 Ollama。
- **识别快、启动快**：使用 Windows 自带 OCR，本地识别；挪开再放回同样的文字，直接用缓存，不再请求网络。

## 下载与使用

1. 打开 [Releases](https://github.com/newHashub/glass_translate/releases)，下载最新版的 `GlassTranslate-vX.Y.Z-Windows-x64.zip`（在页面下方的 Assets 里）。
2. 解压到任意位置，打开解压出来的 `GlassTranslate` 文件夹，双击 `GlassTranslate.exe` 启动。
3. 把取景框拖到外文上即可。按 `Alt + R` 可以随时在鼠标处呼出或隐藏。

解压后的文件夹里有：

```
GlassTranslate/
├── GlassTranslate.exe      ← 双击启动
├── 创建桌面快捷方式.vbs     ← 想在桌面放个图标就双击它
├── 使用说明.txt
└── _internal/              ← 运行库，请勿删除或单独移动 exe
```

> 仓库首页的源代码（Code → Download ZIP）是给开发者的，不能直接运行。普通用户请下载 Releases 里的 ZIP。

不需要安装 Python。如果要识别日文或韩文，需要先安装对应的 OCR 语言包，见[常见问题](#常见问题)。

## 快捷键与操作

| 操作 | 作用 |
| :--- | :--- |
| `Alt + R` | 在鼠标处呼出 / 隐藏取景框 |
| `Alt + S` | 框选翻译：拖出一块区域即翻译，`Esc` 或右键取消 |
| 框内按住左键拖动 | 移动取景框 |
| 拖动四边或四角 | 调整大小 |
| 框内滚动滚轮 | 以鼠标为中心缩放（可在菜单中关闭） |
| 框内右键 / 托盘图标右键 | 打开设置菜单 |
| 单击托盘图标 | 显示 / 隐藏取景框 |

两个快捷键都可以在右键菜单 **⌨️ 唤出快捷键** 中修改，改完立即生效。

## 设置菜单

在框内或托盘图标上点右键，可以设置：

- **翻译语言**：12 组常用预设（自动/英/日/韩/法/德/俄/西 → 中文，中文 → 英/日/韩，自动 → 英文），或在「自定义自由选择」里任意搭配。
- **翻译引擎**：有道网页通道（默认）、MyMemory、自定义大模型（OpenAI 兼容接口）。
- **显示模式**：原地替换（默认）或悬浮字幕卡片。
- **译文字号、识别频率、窗口置顶、底部状态提示、滚轮缩放**。
- **复制最新译文**、**自定义 API 配置**。

## 常见问题

<details>
<summary><b>选了"自动"，为什么只识别出英文？</b></summary>

Windows 只带有你所安装语言的 OCR。没有装日语或韩语，就识别不了这两种文字。

安装方法：**设置 → 时间和语言 → 语言和区域 → 添加语言**，选日语或韩语，确保勾选"光学字符识别"。不需要切换系统显示语言，装好后重启 GlassTranslate。
</details>

<details>
<summary><b>需要 API Key 吗？默认通道稳定吗？</b></summary>

不需要 Key。但默认的有道通道调用的是有道网页端接口，**不是官方开放 API**：高频使用可能被限流，网页改版后也可能失效。程序会在失败时依次换用有道的另一个接口和 MyMemory。

需要长期稳定时，建议在右键菜单 **🔑 自定义 API 配置...** 里接入大模型，例如：

- DeepSeek：`https://api.deepseek.com/v1/chat/completions`
- 本地 Ollama（完全离线）：`http://localhost:11434/v1/chat/completions`
</details>

<details>
<summary><b>取景框会把自己也截进去吗？</b></summary>

不会。窗口设置了 `WDA_EXCLUDEFROMCAPTURE`，截屏时它对自己不可见，所以不会出现"画中画"或闪烁。
</details>

<details>
<summary><b>长段落会漏翻吗？</b></summary>

长文本会切成小块分别翻译，再按行数校对；如果某几行没对上，会单独补翻这几行。
</details>

<details>
<summary><b>Alt + R 没反应？</b></summary>

快捷键可能被其他软件占用了。在托盘图标右键菜单 **⌨️ 唤出快捷键** 里换一个组合。另外检查托盘里是否同时开了多个 GlassTranslate。
</details>

## 开发

需要 Windows 10/11 和 Python 3.10 以上（推荐 3.12）。

```bash
git clone https://github.com/newHashub/glass_translate.git
cd glass_translate
pip install -r requirements-dev.txt
python main.py        # 运行
pytest                # 运行测试（离线）
```

**打包**：双击 `build_exe.bat`。它会在 `.venv-build` 里建一个干净的虚拟环境，生成 `dist\GlassTranslate\`、桌面快捷方式和 `dist\GlassTranslate-v版本号-Windows-x64.zip`。版本号在 `src/version.py` 里改。

<details>
<summary><b>工作原理与目录结构</b></summary>

后台线程循环执行：截取取景框下的画面 → 和上一帧比较，没变化就跳过 → Windows OCR 识别出每一行的文字和位置 → 先查行级缓存，没有再请求翻译 → 把译文画回对应位置。

```
glass_translate/
├── main.py                  # 程序入口
├── src/                     # 源代码
│   ├── main.py              # 启动流程：托盘、全局快捷键、退出清理
│   ├── glass_window.py      # 透明取景框、译文排版、设置对话框
│   ├── region_select.py     # Alt+S 框选遮罩（支持多显示器）
│   ├── worker.py            # 后台工作线程
│   ├── capture_engine.py    # 截屏与画面变化检测
│   ├── ocr_engine.py        # Windows OCR 封装、自动识别语言
│   ├── translator_engine.py # 翻译通道调度、分块、缓存
│   ├── global_hotkey.py     # 全局快捷键（RegisterHotKey）
│   ├── tray_manager.py      # 托盘图标与右键菜单
│   ├── win32_utils.py       # 防自截屏、窗口样式、高 DPI
│   ├── config.py            # 配置读写
│   └── version.py           # 版本号
├── tests/                   # pytest 测试
├── packaging/               # 打包用：PyInstaller 配置、生成快捷方式和发布 ZIP 的脚本
├── resources/               # 图标
├── docs/                    # 其他语言 README、同类工具对比、演示素材
├── build_exe.bat            # 一键打包
├── requirements.txt         # 运行依赖
└── requirements-dev.txt     # 开发与打包依赖
```
</details>

## 同类工具

爱译客、WinLens、团子翻译器、LunaTranslator 等工具各有所长。GlassTranslate 的定位是开源、轻量、免 Key、随手拖动。详细对比见 [同类工具对比](docs/COMPARISON.md)。

## 许可证

[MIT](LICENSE)。欢迎提 Issue 和 Pull Request。觉得有用的话，点个 ⭐ 支持一下。
