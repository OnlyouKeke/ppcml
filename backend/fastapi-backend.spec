# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
BACKEND_DATAS = [
    (str(BASE_DIR / 'HBI.jpg'), 'HBI.jpg'),
]


a = Analysis(
    ['app\\main.py'],
    pathex=[str(BASE_DIR)],
    binaries=[],
    datas=BACKEND_DATAS,
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
    a.binaries,
    a.datas,
    [],
    name='fastapi-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
