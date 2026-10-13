# -*- mode: python ; coding: utf-8 -*-
# 由 build_exe.bat 调用：在项目根目录执行 pyinstaller packaging/GlassTranslate.spec
import os

ROOT = os.path.dirname(SPECPATH)

a = Analysis(
    [os.path.join(ROOT, 'main.py')],
    pathex=[os.path.join(ROOT, 'src')],
    binaries=[],
    datas=[(os.path.join(ROOT, 'resources', 'app_icon.ico'), 'resources')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GlassTranslate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(ROOT, 'resources', 'app_icon.ico')],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GlassTranslate',
)
