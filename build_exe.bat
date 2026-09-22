@echo off
setlocal
cd /d "%~dp0"

echo [1/4] 正在检查与安装打包依赖 PyInstaller...
py -3 -m pip install --quiet pyinstaller pillow

echo [2/4] 正在准备专属高清玻璃质感应用图标 (app_icon.ico)...
if not exist "app_icon.ico" (
    py -3 -c "from PIL import Image, ImageDraw, ImageFont; img = Image.new('RGBA', (256, 256), (0, 0, 0, 0)); draw = ImageDraw.Draw(img); draw.rounded_rectangle([(16, 16), (240, 240)], radius=64, fill=(2, 132, 199, 245), outline=(56, 189, 248, 255), width=8); font = ImageFont.truetype('msyh.ttc', 130); bbox = draw.textbbox((0, 0), '译', font=font); w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]; draw.text(((256 - w) // 2 - bbox[0], (256 - h) // 2 - bbox[1] - 8), '译', fill=(255, 255, 255), font=font); img.save('app_icon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])"
)

echo [3/4] 正在编译极速秒开版原生应用 (dist\GlassTranslate\，免解压即开)...
taskkill /f /im GlassTranslate.exe >nul 2>nul
py -3 -m PyInstaller --onedir --noconsole --name "GlassTranslate" --icon="app_icon.ico" --add-data="app_icon.ico;." --clean -y main.py

echo [4/4] 正在创建/更新极速秒开快捷方式 (GlassTranslate.lnk)...
py -3 -c "import win32com.client, os; w = win32com.client.Dispatch('WScript.Shell'); s = w.CreateShortcut(os.path.abspath('GlassTranslate.lnk')); s.TargetPath = os.path.abspath('dist/GlassTranslate/GlassTranslate.exe'); s.WorkingDirectory = os.path.abspath('dist/GlassTranslate'); s.IconLocation = os.path.abspath('app_icon.ico'); s.Description = 'Windows 实时透视翻译器 (0.7s 秒开版)'; s.Save()"

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
