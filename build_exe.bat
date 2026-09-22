@echo off
setlocal
cd /d "%~dp0"

echo [1/3] 正在检查与安装打包依赖 PyInstaller...
py -3 -m pip install --quiet pyinstaller pillow

echo [2/3] 正在生成专属高清玻璃质感应用图标 (app_icon.ico)...
py -3 -c "from PIL import Image, ImageDraw, ImageFont; img = Image.new('RGBA', (256, 256), (0, 0, 0, 0)); draw = ImageDraw.Draw(img); draw.rounded_rectangle([(16, 16), (240, 240)], radius=64, fill=(2, 132, 199, 245), outline=(56, 189, 248, 255), width=8); font = ImageFont.truetype('msyh.ttc', 130); bbox = draw.textbbox((0, 0), '译', font=font); w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]; draw.text(((256 - w) // 2 - bbox[0], (256 - h) // 2 - bbox[1] - 8), '译', fill=(255, 255, 255), font=font); img.save('app_icon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])"

echo [3/3] 正在使用 PyInstaller 编译 GlassTranslate.exe (纯原生 GUI，零黑框)...
py -3 -m PyInstaller --onefile --noconsole --name "GlassTranslate" --icon="app_icon.ico" --clean main.py

echo.
if exist "dist\GlassTranslate.exe" (
    echo ========================================================
    echo  打包成功！可执行文件位于: dist\GlassTranslate.exe
    echo  您可以直接将其发送至桌面快捷方式或任意文件夹双击秒开。
    echo ========================================================
) else (
    echo [错误] 打包失败，请检查上方控制台输出信息。
)
pause
