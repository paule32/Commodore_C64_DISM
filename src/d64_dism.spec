# -*- mode: python ; coding: utf-8 -*-
# Stage ASM 9: PyInstaller/QtWebEngine deployment fix.
# Build from this directory with:
#     py -m PyInstaller --clean --noconfirm d64_dism.spec

from pathlib import Path
import shutil

ROOT = Path(SPECPATH).resolve()
BUNDLE_NAME = "d64_dism"

# PyInstaller 6 stores normal datas/binaries inside the onedir contents
# directory ("_internal" by default). The following user-facing resources
# must stay next to d64_dism.exe instead, so they are intentionally NOT added
# to Analysis(datas=...). They are copied to the bundle root after COLLECT.
external_root_items = (
    (ROOT / "start.exe", "start.exe"),
    (ROOT / "help", "help"),
    (ROOT / "locales", "locales"),
    (ROOT / "examples", "examples"),
)

for source, _target in external_root_items:
    if not source.exists():
        raise FileNotFoundError(
            f"Required external bundle item is missing: {source}"
        )

# Remaining bundled resources are PyInstaller-managed and therefore live
# below _internal in an onedir build.
datas = []
for source, target in (
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

# Stage ASM 53: Wenn der Benutzer eine lizenzierte C64-Pro-Mono-Datei lokal
# neben das Projekt legt, wird sie automatisch in den PyInstaller-Build
# uebernommen. Das Projekt selbst verteilt keine Fontdatei.
for mono_name in (
    "C64ProMono.ttf",
    "C64 Pro Mono.ttf",
    "C64ProMono.otf",
    "C64 Pro Mono.otf",
):
    mono_font = ROOT / mono_name
    if mono_font.is_file():
        datas.append((str(mono_font), "."))
        break

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
    # Stage ASM 50: optional at runtime from the C64 final image stage.
    "c64packer",
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
    name=BUNDLE_NAME,
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
    name=BUNDLE_NAME,
)

# PyInstaller 6 deliberately places Analysis datas in the contents directory
# (_internal by default). These four items are meant to be user-visible and
# editable next to d64_dism.exe, so mirror them into the outer onedir folder
# only after COLLECT has finished creating the bundle.
bundle_root = Path(DISTPATH).resolve() / BUNDLE_NAME


def _copy_external_root_item(source: Path, relative_target: str) -> None:
    target = bundle_root / relative_target

    if source.is_dir():
        # Mirror exactly; remove stale files from an older build first.
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


for source, relative_target in external_root_items:
    _copy_external_root_item(source, relative_target)

