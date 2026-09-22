@echo off
setlocal
cd /d "%~dp0"

:: 1. 优先检查项目本地虚拟环境
if exist "venv\Scripts\pythonw.exe" (
    start "" "venv\Scripts\pythonw.exe" "main.py"
    exit /b
)
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "main.py"
    exit /b
)

:: 2. 检查系统 PATH 中的 pythonw.exe (完全无控制台黑框)
where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    start "" pythonw "main.py"
    exit /b
)

:: 3. 检查系统 PATH 中的 python.exe
where python >nul 2>nul
if %errorlevel% equ 0 (
    start "" python "main.py"
    exit /b
)

:: 4. 检查 Python Launcher py.exe
where py >nul 2>nul
if %errorlevel% equ 0 (
    start "" py -3 "main.py"
    exit /b
)

echo [错误] 未检测到 Python 运行环境，请先安装 Python 3.10+ 并勾选 "Add Python to PATH"。
pause
