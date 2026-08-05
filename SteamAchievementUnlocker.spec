# -*- mode: python ; coding: utf-8 -*-
# Build: python3 -m PyInstaller --noconfirm SteamAchievementUnlocker.spec

from pathlib import Path

block_cipher = None
ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "rich.console",
        "rich.table",
        "rich.panel",
        "rich.prompt",
        "rich.progress",
        "rich.rule",
        "src",
        "src.api",
        "src.api.steam_web_api",
        "src.config",
        "src.constants",
        "src.errors",
        "src.exit_codes",
        "src.logging_utils",
        "src.preflight",
        "src.steamworks",
        "src.steamworks.ctypes_wrapper",
        "src.steamworks.dylib_manager",
        "src.ui",
        "src.ui.achievement_menu",
        "src.ui.credentials",
        "src.ui.game_selector",
        "src.ui.header",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "IPython",
        "ipython",
        "jupyter",
        "notebook",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "PIL",
        "cv2",
        "pytest",
        "py",
        "jedi",
        "parso",
        "torch",
        "tensorflow",
        "tkinter",
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
    name="SteamAchievementUnlocker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SteamAchievementUnlocker",
)
