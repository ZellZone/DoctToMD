# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for DocxToMD desktop app.

Uses onedir + no UPX to reduce antivirus false positives.
"""

from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

a = Analysis(
    ["app.py"],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "assets" / "icon.ico"), "assets"),
        (str(root / "assets" / "icon.png"), "assets"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "markdown",
        "html2docx",
        "docx",
        "lxml",
        "PIL",
        "pytest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DocxToMD",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / "assets" / "icon.ico"),
    version=str(root / "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DocxToMD",
)
