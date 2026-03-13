# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app\\tray_app.py'],
    pathex=[],
    binaries=[],
    datas=[('config.py', '.'), ('assets', 'assets')],
    hiddenimports=['win32api', 'win32con', 'win32security', 'core', 'core.file_monitor', 'core.behavior_analyzer', 'core.decision_engine', 'core.response_manager', 'core.backup_manager', 'watchdog', 'psutil', 'pystray', 'PIL', 'watchdog.observers.winapi'],
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
    name='RansomGuard',
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
    version='assets\\version_info.txt',
    icon=['assets\\shield_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RansomGuard',
)
