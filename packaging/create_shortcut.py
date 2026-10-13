import os
import sys

def create_shortcuts():
    try:
        import win32com.client
    except ImportError:
        print("[警告] 未安装 pywin32，无法创建快捷方式")
        return

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exe_path = os.path.join(root_dir, "dist", "GlassTranslate", "GlassTranslate.exe")
    work_dir = os.path.join(root_dir, "dist", "GlassTranslate")
    icon_path = os.path.join(root_dir, "resources", "app_icon.ico")

    wscript = win32com.client.Dispatch("WScript.Shell")
    desktop = wscript.SpecialFolders("Desktop")

    targets = [
        os.path.join(desktop, "GlassTranslate.lnk"),
        os.path.join(root_dir, "GlassTranslate.lnk")
    ]

    for link_path in targets:
        try:
            shortcut = wscript.CreateShortcut(link_path)
            shortcut.TargetPath = exe_path
            shortcut.WorkingDirectory = work_dir
            if os.path.exists(icon_path):
                shortcut.IconLocation = f"{icon_path},0"
            shortcut.Description = "GlassTranslate - Windows 实时透视翻译器"
            shortcut.Save()
            print(f"[成功] 快捷方式已更新: {link_path}")
        except Exception as e:
            print(f"[错误] 创建快捷方式失败: {link_path}, 错误: {e}")

if __name__ == "__main__":
    create_shortcuts()
