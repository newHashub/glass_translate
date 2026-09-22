@echo off
setlocal
cd /d "%~dp0"

:: 1. 优先直接启动秒开版原生应用 (0.7秒极速秒显、零黑框、免临时解压)
if exist "dist\GlassTranslate\GlassTranslate.exe" (
    start "" "dist\GlassTranslate\GlassTranslate.exe"
    exit /b
)
if exist "dist\GlassTranslate.exe" (
    start "" "dist\GlassTranslate.exe"
    exit /b
)

:: 2. 检查本地专用虚拟环境
if exist "venv\Scripts\pythonw.exe" (
    start "" "venv\Scripts\pythonw.exe" "main.py"
    exit /b
)
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "main.py"
    exit /b
)

:: 3. 优先使用 Windows 官方 Python 启动器 pyw -3 (自动定位包含完整环境的主 Python)
where pyw >nul 2>nul
if %errorlevel% equ 0 (
    py -3 -c "import PyQt6" >nul 2>nul
    if %errorlevel% equ 0 (
        start "" pyw -3 "main.py"
        exit /b
    )
)

:: 4. 智能遍历 PATH 中所有 pythonw，校验是否装有 PyQt6
for /f "delims=" %%p in ('where pythonw 2^>nul') do (
    "%%p" -c "import PyQt6" >nul 2>nul
    if not errorlevel 1 (
        start "" "%%p" "main.py"
        exit /b
    )
)

:: 5. 智能遍历 PATH 中所有 python，校验是否装有 PyQt6
for /f "delims=" %%p in ('where python 2^>nul') do (
    "%%p" -c "import PyQt6" >nul 2>nul
    if not errorlevel 1 (
        start "" "%%p" "main.py"
        exit /b
    )
)

echo =======================================================
echo [错误] 未检测到安装了完整依赖 (PyQt6 等) 的 Python 运行环境！
echo 请在命令行中执行以下命令安装依赖：
echo     pip install -r requirements.txt
echo =======================================================
pause
