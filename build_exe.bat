@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

rem 打包 GlassTranslate：生成 dist\GlassTranslate\ 和发布用的 ZIP。
rem 在专用虚拟环境 .venv-build 里打包，避免把本机其他项目的库打进去。

set "VENV=.venv-build"
set "PY=%VENV%\Scripts\python.exe"

echo [1/5] 准备打包环境 (%VENV%)...
if not exist "%PY%" (
    py -3 -m venv "%VENV%"
    if errorlevel 1 goto fail
)
"%PY%" -m pip install --quiet --upgrade pip
"%PY%" -m pip install --quiet -r requirements-dev.txt
if errorlevel 1 goto fail

echo [2/5] 关闭正在运行的 GlassTranslate...
taskkill /f /im GlassTranslate.exe >nul 2>nul

echo [3/5] 用 PyInstaller 打包...
"%PY%" -m PyInstaller --noconfirm --clean --distpath dist --workpath build packaging\GlassTranslate.spec
if errorlevel 1 goto fail

echo [4/5] 更新快捷方式 (桌面和项目目录)...
"%PY%" packaging\create_shortcut.py

echo [5/5] 生成发布用的 ZIP...
"%PY%" packaging\package_release.py
if errorlevel 1 goto fail

echo.
echo ========================================================
echo  打包成功
echo  程序:     dist\GlassTranslate\GlassTranslate.exe
echo  发布包:   dist\GlassTranslate-v*-Windows-x64.zip
echo  上传前请先启动一次上面的 exe，确认能正常运行。
echo ========================================================
pause
exit /b 0

:fail
echo.
echo [错误] 打包失败，请查看上方输出。
pause
exit /b 1
