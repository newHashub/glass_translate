@echo off
setlocal
cd /d "%~dp0"

echo [1/4] 正在检查与安装打包依赖 PyInstaller...
py -3 -m pip install --quiet pyinstaller pillow

echo [2/4] 准备应用图标与打包配置...

echo [3/4] 正在编译极速秒开版原生应用 (dist\GlassTranslate\，免解压即开)...
taskkill /f /im GlassTranslate.exe >nul 2>nul
py -3 -m PyInstaller --onedir --noconsole --name "GlassTranslate" --icon="app_icon.ico" --add-data="app_icon.ico;." --clean -y main.py

echo [4/4] 正在创建/更新极速秒开快捷方式 (GlassTranslate.lnk)...
powershell -NoProfile -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut((Resolve-Path 'GlassTranslate.lnk' -ErrorAction SilentlyContinue)); if(!$s){$s=(New-Object -COM WScript.Shell).CreateShortcut((Join-Path (Get-Location) 'GlassTranslate.lnk'))}; $s.TargetPath=(Join-Path (Get-Location) 'dist\GlassTranslate\GlassTranslate.exe'); $s.WorkingDirectory=(Join-Path (Get-Location) 'dist\GlassTranslate'); $s.IconLocation=(Join-Path (Get-Location) 'app_icon.ico'); $s.Description='Windows 实时透视翻译器 (秒开版)'; $s.Save()"

echo.
if exist "dist\GlassTranslate\GlassTranslate.exe" (
    echo ========================================================
    echo  打包成功！极速秒开版应用位于: dist\GlassTranslate\GlassTranslate.exe
    echo  根目录快捷方式已生成: GlassTranslate.lnk (双击 0.7 秒秒开)
    echo ========================================================
) else (
    echo [错误] 打包失败，请检查上方控制台输出信息。
)
pause
