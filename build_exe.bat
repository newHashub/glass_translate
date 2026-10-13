@echo off
setlocal
cd /d "%~dp0"

rem Build GlassTranslate: dist\GlassTranslate\ and the release ZIP.
rem Builds inside a dedicated venv (.venv-build) so packages from the
rem global Python are not bundled.
rem This file is ASCII-only on purpose: cmd mis-parses UTF-8 batch files.
rem Slow downloads? Set a mirror first, e.g.
rem   set PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

set "VENV=.venv-build"
set "PY=%VENV%\Scripts\python.exe"

echo [1/5] Preparing build environment (%VENV%)...
if not exist "%PY%" (
    echo       Creating virtual environment...
    py -3 -m venv "%VENV%"
    if errorlevel 1 goto fail
)
echo       Installing dependencies (first run downloads about 100 MB)...
"%PY%" -m pip install --disable-pip-version-check --progress-bar on -r requirements-dev.txt
if errorlevel 1 goto fail

echo [2/5] Closing running GlassTranslate...
taskkill /f /im GlassTranslate.exe >nul 2>nul

echo [3/5] Running PyInstaller...
"%PY%" -m PyInstaller --noconfirm --clean --distpath dist --workpath build packaging\GlassTranslate.spec
if errorlevel 1 goto fail

echo [4/5] Updating shortcuts (desktop and project folder)...
"%PY%" packaging\create_shortcut.py

echo [5/5] Creating release ZIP...
"%PY%" packaging\package_release.py
if errorlevel 1 goto fail

echo.
echo ========================================================
echo  BUILD OK
echo  App:      dist\GlassTranslate\GlassTranslate.exe
echo  Release:  dist\GlassTranslate-v*-Windows-x64.zip
echo  Launch the exe once before uploading the ZIP.
echo ========================================================
pause
exit /b 0

:fail
echo.
echo [ERROR] Build failed. See the output above.
pause
exit /b 1
