# 🪟 GlassTranslate

<div align="center">

[简体中文](../README.md) • **English** • [日本語](README_JA.md) • [한국어](README_KO.md)

![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D4?logo=windows)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**A pane of transparent glass: place it over foreign text and the translation appears right where the original was.**

<a href="assets/GlassTranslate-Promo.mp4">
  <img src="assets/preview.gif" alt="GlassTranslate demo" width="860" />
</a>

[▶️ Watch the full demo video (46s, Chinese captions)](assets/GlassTranslate-Promo.mp4)

</div>

GlassTranslate is a real-time screen translator for Windows. It is a frameless, transparent viewfinder: drag it over foreign text and the translation is drawn on top of the original, without popups covering what you are looking at. Useful for foreign websites and documents, untranslated games, and raw videos.

## Features

- **In-place translation**: finds the position of each text line, samples the surrounding background, and draws the translation over the original.
- **Drag it anywhere**: drag inside the frame to move, drag the edges to resize, scroll to zoom around the cursor. It re-reads the text as soon as you let go.
- **Region select**: press `Alt + S` and drag out an area like a screenshot tool; the viewfinder snaps to it and translates.
- **Automatic language detection**: picks among the installed English, Japanese, Chinese and Korean OCR recognizers, including Korean or Japanese mixed with English.
- **No API key needed**: uses the Youdao web channel by default; DeepSeek, OpenAI or a local Ollama model can be connected instead.
- **Fast**: uses the OCR built into Windows, locally. Moving away and back to the same text uses the cache instead of the network.

> The translation channels are tuned for Chinese. Translating into English works, but Chinese is the primary target.

## Download and use

1. Open [Releases](https://github.com/newHashub/glass_translate/releases) and download the latest `GlassTranslate-vX.Y.Z-Windows-x64.zip` (under Assets at the bottom of the release).
2. Unzip it anywhere, open the `GlassTranslate` folder inside, and double-click `GlassTranslate.exe`.
3. Drag the viewfinder over foreign text. Press `Alt + R` at any time to show or hide it at the mouse cursor.

The unzipped folder contains:

```
GlassTranslate/
├── GlassTranslate.exe      ← double-click to start
├── 创建桌面快捷方式.vbs     ← "Create desktop shortcut": double-click for a desktop icon
├── 使用说明.txt             ← usage notes (Chinese)
└── _internal/              ← runtime files; keep them next to the exe
```

> The source code on the repository page (Code → Download ZIP) is for developers and won't run by itself. Download the ZIP from Releases instead.

Python is not required. To recognize Japanese or Korean you need the matching OCR language pack; see the [FAQ](#faq).

## Shortcuts and controls

| Action | Effect |
| :--- | :--- |
| `Alt + R` | Show / hide the viewfinder at the mouse cursor |
| `Alt + S` | Region select: drag out an area to translate it; `Esc` or right-click to cancel |
| Drag inside the frame | Move the viewfinder |
| Drag an edge or corner | Resize |
| Scroll inside the frame | Zoom around the cursor (can be turned off in the menu) |
| Right-click the frame or tray icon | Open the settings menu |
| Click the tray icon | Show / hide the viewfinder |

Both shortcuts can be changed under **⌨️ 唤出快捷键** (Summon Hotkey) in the right-click menu; changes take effect immediately.

## Settings menu

Right-click inside the frame or on the tray icon to set:

- **Languages**: 12 common presets (Auto/English/Japanese/Korean/French/German/Russian/Spanish → Chinese, Chinese → English/Japanese/Korean, Auto → English), or any pair under "Custom".
- **Engine**: Youdao web channel (default), MyMemory, or a custom LLM (OpenAI-compatible API).
- **Display mode**: in-place replacement (default) or a floating subtitle card.
- **Font size, scan interval, always on top, status pill, wheel zoom**.
- **Copy latest translation** and **Custom API settings**.

> The menus are currently in Chinese only.

## FAQ

<details>
<summary><b>I chose "Auto" but only English is recognized. Why?</b></summary>

Windows only ships OCR for the languages you have installed. Without Japanese or Korean installed, those scripts cannot be recognized.

To add one: **Settings → Time & language → Language & region → Add a language**, choose Japanese or Korean, and make sure "Optical character recognition" is included. You don't need to change your display language. Restart GlassTranslate afterwards.
</details>

<details>
<summary><b>Do I need an API key? Is the default channel reliable?</b></summary>

No key is needed. But the default Youdao channel calls Youdao's web endpoints, **not an official open API**: heavy use may be rate-limited, and it can stop working if the site changes. When a request fails, the app falls back to another Youdao endpoint and then MyMemory.

For long-term reliability, connect an LLM under **🔑 自定义 API 配置...** (Custom API Settings) in the right-click menu, for example:

- DeepSeek: `https://api.deepseek.com/v1/chat/completions`
- Local Ollama (fully offline): `http://localhost:11434/v1/chat/completions`
</details>

<details>
<summary><b>Does the viewfinder capture itself?</b></summary>

No. The window uses `WDA_EXCLUDEFROMCAPTURE`, so it is invisible to its own screen capture and there is no picture-in-picture loop or flicker.
</details>

<details>
<summary><b>Will long paragraphs be cut off?</b></summary>

Long text is split into small chunks and the result is checked line by line; any lines that don't match up are translated again individually.
</details>

<details>
<summary><b>Alt + R does nothing?</b></summary>

Another app may already be using that shortcut. Pick a different one under **⌨️ 唤出快捷键** (Summon Hotkey) in the tray menu. Also check that only one GlassTranslate is running in the tray.
</details>

## Development

Requires Windows 10/11 and Python 3.10+ (3.12 recommended).

```bash
git clone https://github.com/newHashub/glass_translate.git
cd glass_translate
pip install -r requirements-dev.txt
python main.py        # run
pytest                # run the tests (offline)
```

**Building**: double-click `build_exe.bat`. It creates a clean virtual environment in `.venv-build` and produces `dist\GlassTranslate\`, a desktop shortcut, and `dist\GlassTranslate-v<version>-Windows-x64.zip`. The version lives in `src/version.py`.

<details>
<summary><b>How it works and project layout</b></summary>

A background thread loops: capture the screen under the viewfinder → skip if nothing changed since the last frame → Windows OCR returns each line's text and position → look up the line cache, otherwise request a translation → draw the translation back at each line's position.

```
glass_translate/
├── main.py                  # Entry point
├── src/                     # Source code
│   ├── main.py              # Startup: tray, global hotkeys, cleanup
│   ├── glass_window.py      # Transparent viewfinder, layout, dialogs
│   ├── region_select.py     # Alt+S selection overlay (multi-monitor)
│   ├── worker.py            # Background worker thread
│   ├── capture_engine.py    # Screen capture and change detection
│   ├── ocr_engine.py        # Windows OCR wrapper, automatic language detection
│   ├── translator_engine.py # Translation channels, chunking, cache
│   ├── global_hotkey.py     # Global hotkeys (RegisterHotKey)
│   ├── tray_manager.py      # Tray icon and right-click menu
│   ├── win32_utils.py       # Capture exclusion, window styling, high DPI
│   ├── config.py            # Settings
│   └── version.py           # Version number
├── tests/                   # pytest tests
├── packaging/               # Build files: PyInstaller spec, shortcut and release ZIP scripts
├── resources/               # Icon
├── docs/                    # Translated READMEs, comparison, demo assets
├── build_exe.bat            # One-click build
├── requirements.txt         # Runtime dependencies
└── requirements-dev.txt     # Development and build dependencies
```
</details>

## Similar tools

Gaminik, WinLens, Dango Translator, LunaTranslator and others each have their strengths. GlassTranslate aims to be open source, lightweight, key-free and quick to drag around. See the [comparison](COMPARISON.md) (in Chinese).

## License

[MIT](../LICENSE). Issues and pull requests are welcome. If you find it useful, a ⭐ is appreciated.
