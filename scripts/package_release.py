import os
import sys
import shutil
import zipfile

def make_release():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dist_app_dir = os.path.join(root_dir, "dist", "GlassTranslate")
    dist_dir = os.path.join(root_dir, "dist")
    
    if not os.path.exists(os.path.join(dist_app_dir, "GlassTranslate.exe")):
        print("[错误] 未找到 dist\\GlassTranslate\\GlassTranslate.exe，请先执行 build_exe.bat 打包！")
        return False
        
    # 1. 在分发目录写入快捷方式助手与说明文档
    vbs_path = os.path.join(dist_app_dir, "一键生成桌面快捷方式.vbs")
    vbs_content = (
        'Set WshShell = CreateObject("WScript.Shell")\r\n'
        'Set fso = CreateObject("Scripting.FileSystemObject")\r\n'
        'currentDir = fso.GetParentFolderName(WScript.ScriptFullName)\r\n'
        'desktopDir = WshShell.SpecialFolders("Desktop")\r\n'
        'exePath = currentDir & "\\GlassTranslate.exe"\r\n\r\n'
        'Set link = WshShell.CreateShortcut(desktopDir & "\\GlassTranslate.lnk")\r\n'
        'link.TargetPath = exePath\r\n'
        'link.WorkingDirectory = currentDir\r\n'
        'link.IconLocation = exePath & ",0"\r\n'
        'link.Description = "GlassTranslate - Windows 实时透视翻译器"\r\n'
        'link.Save\r\n\r\n'
        'MsgBox "GlassTranslate 桌面快捷方式已成功创建！" & vbCrLf & vbCrLf & '
        '"您现在可以直接在桌面双击启动应用了。", 64, "GlassTranslate 安装成功"\r\n'
    )
    with open(vbs_path, "w", encoding="gbk", errors="ignore") as f:
        f.write(vbs_content)
        
    readme_dist_path = os.path.join(dist_app_dir, "使用说明.txt")
    readme_dist_content = (
        "======================================================\r\n"
        "         GlassTranslate - Windows 实时透视翻译器\r\n"
        "======================================================\r\n\r\n"
        "【极速上手】\r\n"
        "1. 双击运行《一键生成桌面快捷方式.vbs》，即可在桌面生成图标。\r\n"
        "2. 或者直接双击《GlassTranslate.exe》直接运行！\r\n\r\n"
        "【常用快捷键】\r\n"
        "- Alt + ` (反引号，Esc下方按键)：快速显示 / 隐藏翻译框\r\n"
        "- 右键点击系统右下角托盘图标：可自由切换翻译源语言与目标语言\r\n\r\n"
        "【系统要求】\r\n"
        "- Windows 10 / Windows 11 (64位)\r\n"
        "- 免装 Python，免配环境，解压即用！\r\n"
    )
    with open(readme_dist_path, "w", encoding="gbk", errors="ignore") as f:
        f.write(readme_dist_content)
        
    # 2. 打包生成 ZIP 便携分发包
    zip_name = "GlassTranslate-v1.0.0-Windows-x64.zip"
    zip_dest = os.path.join(dist_dir, zip_name)
    print(f"正在打包制作分发安装包: {zip_dest} ...")
    
    with zipfile.ZipFile(zip_dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(dist_app_dir):
            for file in files:
                file_full = os.path.join(root, file)
                rel_path = os.path.join("GlassTranslate", os.path.relpath(file_full, dist_app_dir))
                zf.write(file_full, rel_path)
                
    zip_size_mb = round(os.path.getsize(zip_dest) / 1024 / 1024, 2)
    print(f"[成功] 分发包制作完成！大小: {zip_size_mb} MB")
    
    # 3. 复制一份到桌面方便用户直接发给朋友
    desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    if os.path.exists(desktop_dir):
        desktop_zip = os.path.join(desktop_dir, zip_name)
        shutil.copy2(zip_dest, desktop_zip)
        print(f"[已放置到桌面] {desktop_zip}")
        
    return True

if __name__ == "__main__":
    make_release()
