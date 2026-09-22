# 🪟 GlassTranslate (透视翻译器)

<div align="center">

![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D4?logo=windows)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Tests](https://img.shields.io/badge/Tests-16%20Passed-brightgreen)
![Fast](https://img.shields.io/badge/Latency-~60ms-orange)

**专为 Windows 打造的无边框透明玻璃实时透视翻译器**  
*摆脱繁琐的“截图 - 划词 - 弹窗查看”，把取景框覆盖在文字上方，原地秒变中文！*

[✨ 核心特性](#-核心特性) • [🚀 快速开始](#-快速开始) • [🎮 交互与快捷键](#-交互与快捷键) • [🏗️ 架构与技术栈](#️-架构设计) • [❓ 常见问题](#-常见问题)

</div>

---

## 🌟 为什么选择 GlassTranslate？

在阅读外语文献、浏览海外网站、玩未汉化游戏、查阅英文代码或看外语生肉视频时，传统的划词插件或截图翻译软件往往需要繁琐的多步操作，且会弹出突兀的卡片窗口打断视线。

**GlassTranslate** 提供了一种极其优雅的“透视感”体验：
- 就像在桌面上**放置了一块完全透明的取景玻璃**；
- 框内的外文字符会被**原地精准替换为优美排版的中文**；
- 底层背景、视频画面、软件界面完全保持原样，视野零遮挡。

---

## ✨ 核心特性

### 1. 🪟 极致纯净的透明取景体验
- **无标题栏、无常驻外边框**：全窗口 100% 透明，仅保留四角青蓝直角对焦标。
- **原地文字智能替换 (In-Place Translation)**：提取框内文字的真实屏幕物理坐标，自动采样文字周边底色与明度，以两遍绘制（Two-Pass）架构优雅覆盖微胶囊背景并渲染中文。
- **像移动一块纯净玻璃**：鼠标左键在框内任意位置按下即可平滑拖拽，**移动瞬间清屏为透明，松手落位瞬间智能吸附**，完全符合物理直觉。

### 2. ⚡ 毫秒级极速双通道与零 411 限流
- **Windows 原生硬件加速 OCR**：基于 Windows 10/11 WinRT 硬件 OCR 引擎，本地识别仅需 **10~20ms**，零 CPU 占用。
- **有道官方移动端生产通道**：单次请求仅需 **50~90ms**，彻底告别 Demo 接口频繁报错 `411 访问受限` 的烦恼。
- **智能多级容灾熔断**：移动端主通道 ➔ aidemo 熔断备用 ➔ MyMemory 多语种启发式兜底，永不宕机。

### 3. 🧠 行级/句子级智能语义持久缓存
- **微调移动 0ms 瞬间秒显**：不仅支持整段 MD5 缓存，更细化到每一行、每一句的独立语义指纹；
- **重音与变音符号模糊容错**：引入 `unicodedata` 变音折叠技术（如 `à->a`, `é->e`），即使轻微拖动取景框导致切边或标点微扰，**100% 命中缓存，零网络请求秒级贴合**！

### 4. 🖱️ 8 向边缘自适应缩放与框内滚轮缩放
- **边缘感应 8 向平滑缩放**：鼠标划过边缘 14px 范围自动变为缩放手势，纯 Qt 状态机调度，杜绝 Win32 模态消息死锁。
- **框内鼠标锚点滚轮缩放**：鼠标在框内直接滚动滚轮，以鼠标所在光标为中心等比快速缩放取景范围。

### 5. ⌨️ 全局快捷键与后台静默驻留
- **Alt + R 全局瞬移呼出**：按下 `Alt + R` 瞬间在当前鼠标指针位置居中唤出翻译框；再次按下即可快捷隐藏。
- **系统托盘后台驻留**：不占用任务栏，右键托盘或右键窗口任意空白处，均可唤出全能控制菜单。
- **底部状态提示条开关（默认关闭）**：默认状态保持通透无干扰；需要排查网络或查看进度时可在菜单栏一键勾选打开。

### 6. 🌐 支持自定义大模型 (OpenAI / DeepSeek 等)
- 内置偏好设置面板，不仅支持内置高速引擎，还可自由接入自定义 API（如 OpenAI `gpt-4o-mini`、`deepseek-chat` 或本地 Ollama）。

---

## 🚀 快速开始

### 环境依赖
- **操作系统**：Windows 10 / Windows 11
- **Python 版本**：Python 3.10+ (推荐 Python 3.12)

### 1. 克隆代码
```bash
git clone https://github.com/newHashub/glass_translate.git
cd glass_translate
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 启动运行
- **方式一：原生应用程序（零黑框，推荐）**
  - 直接双击根目录的 **`GlassTranslate.lnk`** 或 **`dist/GlassTranslate.exe`**。
  - 纯原生 Windows GUI 程序，不依赖本地 Python，双击即开，零控制台黑框！
- **方式二：运行脚本**
  - 双击 **`run.bat`** 或 **`run.vbs`**（脚本将自动寻找完整 Python 环境或直接调用 EXE）。
- **方式三：命令行启动**
  ```powershell
  python main.py
  ```

### 📦 一键打包独立 EXE
如果您修改了代码并希望重新生成单文件 `.exe`：
- 直接双击运行 **`build_exe.bat`**，脚本将自动处理依赖并在 `dist/` 目录下生成全新的 `GlassTranslate.exe`！

---

## 🎮 交互与快捷键

| 操作 / 快捷键 | 功能说明 |
| :--- | :--- |
| **Alt + R** | **全局快速呼出/隐藏**：在当前鼠标所在位置秒显/收起翻译框 |
| **框内按住左键拖拽** | 平滑移动取景框；按下瞬间清屏，松手瞬间吸附秒显译文 |
| **四周边缘按住拖拽** | 8 个方向自由调整取景框宽度与高度 |
| **鼠标在框内滑动滚轮** | 以鼠标为中心快速放大/缩小取景窗口（可在菜单中开启/关闭） |
| **在框内点击鼠标右键** | 唤出全能控制菜单（语言选择、模式切换、置顶、偏好设置等） |
| **双击系统托盘图标** | 快速显示 / 隐藏翻译框 |

---

## ⚙️ 右键全能控制中心概览

鼠标在框内右键或在任务栏右下角托盘图标右键均可唤出（**所有配置一键直达，零冗余弹窗**）：

- 🪟 **显示/隐藏翻译框**
- ⏸️ **实时自动翻译** (开启/暂停实时检测)
- ⚡ **立即识别刷新** (手动强制触发扫描)
- 🌐 **翻译语言 ➔** (自动➔中文、英文➔中文、日文➔中文、中文➔英文)
- 🚀 **翻译引擎 ➔** (⚡ 有道官方直连 [默认]、🌐 MyMemory 免费通道、🤖 自定义大模型)
- 🔤 **显示模式 ➔** (原地文字替换 / 悬浮卡片字幕)
- 🔍 **译文字号 ➔** (紧凑 85%、标准 100% [默认]、稍大 115%、醒目 130%)
- ⏱️ **识别频率 ➔** (极速 200ms、均衡 300ms [默认]、节能 600ms、慢速 1000ms)
- 🖱️ **框内滚轮缩放窗口** (勾选开关)
- 💡 **显示底部状态提示** (勾选开关，默认关闭保持极致通透)
- 📌 **窗口始终置顶** (勾选开关)
- 📋 **复制最新译文**
- 🔑 **自定义 API 配置...** (专为 OpenAI / DeepSeek / Ollama 用户准备的轻量端点与 Key 设置)
- ❌ **退出程序**

---

## 🏗️ 架构设计

本项目采用高响应、完全解耦的多线程异步流水线架构：

```mermaid
flowchart TD
    subgraph UI ["🎨 前台界面层 (GUI Thread)"]
        GW["GlassWindow (完全透明 / 纯 Qt 8向缩放 / 无锁拖拽)"]
        TP["Two-Pass 渲染引擎 (底色微胶囊 + 像素级字号匹配)"]
        TM["TrayManager (托盘管理与全功能右键菜单)"]
    end

    subgraph Pipeline ["⚡ 后台工作流流水线 (TranslationWorker)"]
        CE["CaptureEngine (屏幕截取 + 80x80 快速差分比对)"]
        OCR["OcrEngine (WinRT 原生硬件加速 OCR: 10~20ms)"]
        TE["TranslatorEngine (行级语义持久缓存 + 双通道高速请求)"]
    end

    subgraph Hardware ["🖥️ Windows 底层支持"]
        WDA["WDA_EXCLUDEFROMCAPTURE (防自截屏递归穿透)"]
        DWM["DWM 原生窗口圆角与毛玻璃支持"]
        HK["Win32 RegisterHotKey 全局消息泵 (Alt+R)"]
    end

    GW -->|坐标与静止触发| Pipeline
    CE --> OCR --> TE
    TE -->|result_ready 信号| GW
    GW --> TP
    Hardware -.-> GW
```

### 目录结构说明
```
glass_translate/
├── main.py              # 主入口 (控制台隐藏、热键初始化、生命周期管理)
├── glass_window.py      # 玻璃质感透明视窗、自适应排版、事件状态机与设置面板
├── worker.py            # 后台高响应工作线程 (去抖检测、缓存秒显探针、调度分发)
├── capture_engine.py    # 屏幕捕获与图像像素变动差分检测引擎
├── ocr_engine.py        # Windows 原生 OCR (WinRT) 封装与智能分词
├── translator_engine.py # 多引擎调度器 (移动端高速通道、熔断隔离、行级语义缓存)
├── global_hotkey.py     # Win32 RegisterHotKey 全局原生热键线程
├── win32_utils.py       # 防截屏穿透、DWM 圆角与高 DPI 感知
├── config.py            # 本地配置管理器 (自适应缺省值与自动持久化)
├── run.bat              # 便携智能启动批处理脚本
├── run.vbs              # 完全无黑框后台静默启动脚本
├── build_exe.bat        # 一键打包生成原生 EXE 脚本
├── app_icon.ico         # 专属高分辨率玻璃质感应用图标
├── requirements.txt     # 项目 Python 依赖库声明
├── pytest.ini           # 单元测试自动化配置
├── LICENSE              # MIT 开源许可证
└── tests/               # 自动化单元测试套件 (覆盖排版、捕获、缓存、热键等)
```

---

## ❓ 常见问题 (FAQ)

<details>
<summary><b>Q1: 为什么移动翻译框时底层画面不会被翻译框本身遮挡？</b></summary>
本项目通过调用 Windows 底层 API <code>SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)</code>，使翻译窗口在 Windows 的屏幕抓取流（BitBlt / DirectX / DWM）中被底层自动隐形穿透，彻底杜绝了“自截屏递归产生无限画中画”的问题。
</details>

<details>
<summary><b>Q2: 为什么我的文字排版不会遮挡上一行或字体过大？</b></summary>
内置自适应排版引擎会根据 OCR 提取的每行实际高度（<code>wh</code>）以及真实行间距（<code>pitch</code>），智能约束背景微胶囊的高度与行距，并采用“先画所有胶囊背景，再画所有文字”的两遍绘制（Two-Pass）技术，无论字体如何缩放均不会产生覆盖截断。
</details>

<details>
<summary><b>Q3: 是否需要付费申请 API Key？</b></summary>
不需要。默认搭载的有道官方移动端生产通道无需任何 API Key，开箱即用；如果您有自己的私有大模型（如 OpenAI、DeepSeek 等），也可以在偏好设置中随时填入自己的 Key。
</details>

---

## 📄 开源许可证

本项目采用 [MIT License](LICENSE) 开源协议。欢迎提交 Issue 和 Pull Request！

如果你觉得这个项目对你有帮助，欢迎在 GitHub 上点一个 ⭐️ **Star** 支持一下！  
GitHub 仓库地址：[https://github.com/newHashub/glass_translate](https://github.com/newHashub/glass_translate)
