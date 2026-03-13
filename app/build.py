"""
RANSOMGUARD – Build Script
Compiles the Python project into a standalone Windows .exe using PyInstaller,
then optionally invokes Inno Setup to produce the installer.

Usage:
  python build.py              # compile exe only
  python build.py --installer  # compile exe + build installer .exe
  python build.py --clean      # remove build artifacts

Requirements:
  pip install pyinstaller pillow pystray psutil watchdog pywin32
"""

import os
import sys
import shutil
import argparse
import subprocess

# ─────────────────────────────────────────────
APP_NAME    = "RansomGuard"
VERSION     = "1.0.0"
ENTRY_POINT = "tray_app.py"          # main entry after install
ICON_FILE   = "assets/shield_icon.ico"
DIST_DIR    = "dist"
BUILD_DIR   = "build"
# ─────────────────────────────────────────────

PYINSTALLER_ARGS = [
    "pyinstaller",
    ENTRY_POINT,
    f"--name={APP_NAME}",
    "--onedir",                       # folder mode (faster startup)
    "--windowed",                     # no console window
    f"--icon={ICON_FILE}",
    "--add-data=config.py;.",
    "--add-data=assets;assets",
    "--hidden-import=win32api",
    "--hidden-import=win32con",
    "--hidden-import=win32security",
    "--hidden-import=pystray",
    "--hidden-import=PIL",
    "--hidden-import=watchdog.observers.winapi",
    f"--distpath={DIST_DIR}",
    f"--workpath={BUILD_DIR}",
    "--noconfirm",
    "--clean",
    # Version info embedded into exe
    "--version-file=assets/version_info.txt",
]

INNO_SETUP_PATHS = [
    r"C:\Program Files (x86)\Inno Setup 6\iscc.exe",
    r"C:\Program Files\Inno Setup 6\iscc.exe",
]


def clean():
    for d in (DIST_DIR, BUILD_DIR, "__pycache__"):
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"  Removed: {d}/")
    for f in os.listdir("."):
        if f.endswith(".spec"):
            os.remove(f)
            print(f"  Removed: {f}")
    print("Clean complete.")


def build_exe():
    print(f"\n{'='*55}")
    print(f"  Building {APP_NAME} v{VERSION} executable…")
    print(f"{'='*55}\n")

    # Ensure assets dir exists
    os.makedirs("assets", exist_ok=True)
    _create_placeholder_icon()
    _create_version_file()

    result = subprocess.run(PYINSTALLER_ARGS, capture_output=False)
    if result.returncode != 0:
        print("\n❌ PyInstaller build failed.")
        sys.exit(1)

    exe = os.path.join(DIST_DIR, APP_NAME, f"{APP_NAME}.exe")
    if os.path.exists(exe):
        print(f"\n✅ Executable built: {exe}")
    else:
        print("\n⚠ Build may have issues — check output above.")

    return exe


def build_installer():
    iscc = None
    for path in INNO_SETUP_PATHS:
        if os.path.exists(path):
            iscc = path
            break

    if not iscc:
        print("\n⚠ Inno Setup not found. Install from: https://jrsoftware.org/isinfo.php")
        print("  Then run: iscc RansomGuard_Setup.iss")
        return

    print(f"\n{'='*55}")
    print(f"  Building installer with Inno Setup…")
    print(f"{'='*55}\n")

    result = subprocess.run([iscc, "RansomGuard_Setup.iss"])
    if result.returncode == 0:
        installer = os.path.join("Output", f"RansomGuard_Setup_v{VERSION}.exe")
        print(f"\n✅ Installer ready: {installer}")
        print(f"   File size: {os.path.getsize(installer) / 1024 / 1024:.1f} MB")
    else:
        print("\n❌ Inno Setup failed.")


def _create_placeholder_icon():
    """Create a minimal .ico if none exists (requires Pillow)."""
    if os.path.exists(ICON_FILE):
        return
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d   = ImageDraw.Draw(img)
        d.polygon([(32, 2), (62, 18), (62, 40), (32, 62), (2, 40), (2, 18)],
                  fill="#E84545")
        img.save(ICON_FILE, format="ICO", sizes=[(64, 64), (32, 32), (16, 16)])
        print(f"  Created placeholder icon: {ICON_FILE}")
    except ImportError:
        print("  ⚠ Pillow not installed — using no icon. Run: pip install pillow")


def _create_version_file():
    """Generate PyInstaller version info file."""
    v = VERSION.split(".")
    content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({v[0]}, {v[1]}, {v[2]}, 0),
    prodvers=({v[0]}, {v[1]}, {v[2]}, 0),
    mask=0x3f, flags=0x0, OS=0x4, fileType=0x1,
    subtype=0x0, date=(0, 0)
  ),
  kids=[
    StringFileInfo([StringTable(u'040904B0', [
      StringStruct(u'CompanyName',      u'RansomGuard Security'),
      StringStruct(u'FileDescription',  u'RansomGuard Early Warning System'),
      StringStruct(u'FileVersion',      u'{VERSION}'),
      StringStruct(u'InternalName',     u'RansomGuard'),
      StringStruct(u'LegalCopyright',   u'Copyright 2024 RansomGuard Security'),
      StringStruct(u'OriginalFilename', u'RansomGuard.exe'),
      StringStruct(u'ProductName',      u'RansomGuard'),
      StringStruct(u'ProductVersion',   u'{VERSION}'),
    ])]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    os.makedirs("assets", exist_ok=True)
    with open("assets/version_info.txt", "w") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description=f"Build {APP_NAME}")
    parser.add_argument("--installer", action="store_true",
                        help="Also build the Inno Setup installer .exe")
    parser.add_argument("--clean", action="store_true",
                        help="Remove build artifacts and exit")
    args = parser.parse_args()

    if args.clean:
        clean()
        return

    build_exe()

    if args.installer:
        build_installer()

    print(f"\n{'='*55}")
    print(f"  Done!  {APP_NAME} v{VERSION}")
    print(f"{'='*55}")
    print(f"  Exe:       dist/{APP_NAME}/{APP_NAME}.exe")
    if args.installer:
        print(f"  Installer: Output/RansomGuard_Setup_v{VERSION}.exe")
    print()


if __name__ == "__main__":
    main()
