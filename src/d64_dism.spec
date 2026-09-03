# -*- mode: python ; coding: utf-8 -*-
# Stage ASM 9: PyInstaller/QtWebEngine deployment fix.
# Build from this directory with:
#     py -m PyInstaller --clean --noconfirm d64_dism.spec

from pathlib import Path

ROOT = Path(SPECPATH).resolve()

# Keep user/project data in their natural paths. If help/c64.chm is present
# before the build it is copied to help/c64.chm inside the onedir bundle.
datas = []
for source, target in (
    (ROOT / "help", "help"),
    (ROOT / "examples", "examples"),
    (ROOT / "runtime" / "graphics", "runtime/graphics"),
    (ROOT / "runtime" / "pascal" / "test", "runtime/pascal/test"),
    (ROOT / "c64c" / "include", "c64c/include"),
):
    if source.exists():
        datas.append((str(source), target))

binaries = []
for filename in (
    "d64qt5.dll",
    "libgcc_s_dw2-1.dll",
    "libstdc++-6.dll",
    "libwinpthread-1.dll",
):
    source = ROOT / filename
    if source.is_file():
        binaries.append((str(source), "."))

odbc_bridge = ROOT / "odbc_bitness_bridge.ps1"
if odbc_bridge.is_file():
    datas.append((str(odbc_bridge), "."))

font_file = ROOT / "C64Pro.ttf"
if font_file.is_file():
    datas.append((str(font_file), "."))

# Explicit imports force PyInstaller's official PyQt5/QtWebEngine hooks to run,
# which collect QtWebEngineProcess.exe, ICU/resources .pak files and locales.
hiddenimports = [
    "PyQt5.QtWebEngineWidgets",
    "PyQt5.QtWebEngineCore",
    "PyQt5.QtWebEngine",
    # Stage ASM 22: pyodbc is imported optionally at runtime. Listing Windows
    # DSNs works without it, but Test/Connect needs the compiled extension in
    # a frozen build.
    "pyodbc",
]

a = Analysis(
    [str(ROOT / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(ROOT / "pyi_rth_d64_qtwebengine.py")],
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
    name="d64_dism",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # Do not UPX-compress Qt/Chromium binaries. Native WebEngine helpers and
    # plugins are particularly sensitive to binary post-processing on Windows.
    upx=False,
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
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=["Qt*.dll", "*QtWebEngineProcess.exe", "PyQt5\\*.pyd"],
    name="d64_dism",
)
