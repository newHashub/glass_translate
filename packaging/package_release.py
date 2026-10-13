"""把 dist/GlassTranslate 打成发布用的 ZIP（由 build_exe.bat 调用）。

ZIP 解压后是一个 GlassTranslate 文件夹，里面有：
  GlassTranslate.exe         主程序
  创建桌面快捷方式.vbs        双击后在桌面放一个启动图标
  使用说明.txt
  _internal/                 运行库，不要删
"""
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from version import __version__  # noqa: E402

APP_DIR = os.path.join(ROOT, "dist", "GlassTranslate")
ZIP_NAME = f"GlassTranslate-v{__version__}-Windows-x64.zip"

# 绝不能打进发布包的文件：本机配置里可能有 API Key
EXCLUDE_NAMES = {"config.json"}

SHORTCUT_VBS = (
    'Set WshShell = CreateObject("WScript.Shell")\r\n'
    'Set fso = CreateObject("Scripting.FileSystemObject")\r\n'
    'currentDir = fso.GetParentFolderName(WScript.ScriptFullName)\r\n'
    'exePath = currentDir & "\\GlassTranslate.exe"\r\n'
    'Set link = WshShell.CreateShortcut(WshShell.SpecialFolders("Desktop") & "\\GlassTranslate.lnk")\r\n'
    'link.TargetPath = exePath\r\n'
    'link.WorkingDirectory = currentDir\r\n'
    'link.IconLocation = exePath & ",0"\r\n'
    'link.Description = "GlassTranslate"\r\n'
    'link.Save\r\n'
    'MsgBox "已在桌面创建 GlassTranslate 快捷方式。", 64, "GlassTranslate"\r\n'
)

USAGE_TXT = (
    f"GlassTranslate v{__version__}\r\n"
    "https://github.com/newHashub/glass_translate\r\n"
    "\r\n"
    "【开始使用】\r\n"
    "1. 双击 GlassTranslate.exe 启动，取景框出现在屏幕上，托盘里会有图标。\r\n"
    "2. 想在桌面放个图标：双击本文件夹里的「创建桌面快捷方式.vbs」。\r\n"
    "3. 把取景框拖到外文上，框里的文字会被替换成译文。\r\n"
    "\r\n"
    "【快捷键】\r\n"
    "- Alt + R：在鼠标处显示 / 隐藏取景框\r\n"
    "- Alt + S：框选区域翻译（拖出一块区域，Esc 或右键取消）\r\n"
    "- 框内或托盘图标上点右键：设置语言、翻译引擎、快捷键等\r\n"
    "\r\n"
    "【识别日文、韩文】\r\n"
    "需要先在 Windows 设置 → 时间和语言 → 语言和区域 中添加日语或韩语，\r\n"
    "并勾选「光学字符识别」，装好后重启本程序。\r\n"
    "\r\n"
    "【注意】\r\n"
    "- _internal 文件夹是运行库，请和 GlassTranslate.exe 放在一起，不要删除。\r\n"
    "- 系统要求：Windows 10 / 11（64 位），无需安装 Python。\r\n"
)


def make_release() -> bool:
    exe = os.path.join(APP_DIR, "GlassTranslate.exe")
    if not os.path.exists(exe):
        print("[错误] 没有找到 dist\\GlassTranslate\\GlassTranslate.exe，打包失败。")
        return False

    # vbs 由 wscript 执行，需要系统 ANSI 编码；txt 用带 BOM 的 UTF-8，记事本能正确显示
    with open(os.path.join(APP_DIR, "创建桌面快捷方式.vbs"), "w", encoding="gbk", newline="") as f:
        f.write(SHORTCUT_VBS)
    with open(os.path.join(APP_DIR, "使用说明.txt"), "w", encoding="utf-8-sig", newline="") as f:
        f.write(USAGE_TXT)

    zip_path = os.path.join(ROOT, "dist", ZIP_NAME)
    print(f"正在生成 {zip_path} ...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(APP_DIR):
            for name in files:
                if name in EXCLUDE_NAMES:
                    continue
                full = os.path.join(root, name)
                zf.write(full, os.path.join("GlassTranslate", os.path.relpath(full, APP_DIR)))

    size_mb = os.path.getsize(zip_path) / 1024 / 1024
    print(f"[完成] {ZIP_NAME}（{size_mb:.1f} MB）")
    return True


if __name__ == "__main__":
    sys.exit(0 if make_release() else 1)
