@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo [1/5] 检查并安装打包依赖...
py -3 -m pip install --quiet pyinstaller pillow

echo [2/5] 关闭已运行的进程...
taskkill /f /im GlassTranslate.exe >nul 2>nul

echo [3/5] 正在编译原生应用 (PyInstaller onedir)...
py -3 -m PyInstaller --onedir --noconsole --name "GlassTranslate" --icon="resources/app_icon.ico" --add-data="resources/app_icon.ico;resources" --clean -y main.py

echo [4/5] 正在更新桌面快捷方式...
py -3 scripts/create_shortcut.py

echo [5/5] 正在生成免配环境分发安装包 (ZIP)...
py -3 scripts/package_release.py

echo.
if exist "dist\GlassTranslate\GlassTranslate.exe" (
    echo ========================================================
    echo  打包成功！
    echo  1. 原生免解压应用: dist\GlassTranslate\GlassTranslate.exe
    echo  2. 本地快捷方式: 桌面\GlassTranslate.lnk (双击秒开)
    echo  3. 分发给朋友的安装包: 桌面\GlassTranslate-v1.0.0-Windows-x64.zip
    echo ========================================================
) else (
    echo [错误] 打包失败，请检查上方控制台输出信息。
)
pause
