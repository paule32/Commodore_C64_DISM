# -*- mode: python ; coding: utf-8 -*-
"""Stage 528: portable Windows ONEFILE GUI, bootstrapped from src/__main__.py.

Use at the REPOSITORY ROOT:
    python.exe -m PyInstaller --noconfirm --clean d64_dism.spec

The separate native watchdog is compiled for the INTERPRETER architecture,
then embedded in the onefile EXE and extracted by PyInstaller at runtime.
"""
from pathlib import Path
import os
import shutil
import struct
import subprocess
import sys
import uuid

ROOT = Path(SPECPATH).resolve()
SRC = ROOT / "src"
if os.name != "nt":
    raise RuntimeError("d64_dism.spec builds a Windows PE executable; run PyInstaller on Windows.")
if not (SRC / "__main__.py").is_file():
    raise FileNotFoundError(f"Missing GUI entry point: {SRC / '__main__.py'}")

ARCH = "x64" if struct.calcsize("P") == 8 else "x86"
MACHINE = 0x8664 if ARCH == "x64" else 0x014c


def _native_machine(executable):
    """Verify a pre-existing executable is a PE with correct architecture."""
    try:
        with open(executable, "rb") as f:
            header = f.read(64)
            if len(header) < 64 or header[:2] != b"MZ":
                return None
            pe_offset = struct.unpack_from("<I", header, 0x3c)[0]
            f.seek(pe_offset)
            signature = f.read(6)
            if signature[:4] != b"PE\x00\x00":
                return None
            return struct.unpack_from("<H", signature, 4)[0]
    except (OSError, ValueError, struct.error):
        return None


def _compiler():
    env_compiler = os.getenv("D64_WATCHDOG_CXX", "").strip()
    options = ([env_compiler] if env_compiler else [])
    options += (["x86_64-w64-mingw32-g++", "g++"] if ARCH == "x64"
                else ["i686-w64-mingw32-g++", "g++"])
    for name in options:
        exe = shutil.which(name)
        if not exe:
            continue
        try:
            result = subprocess.run([exe, "-dumpmachine"], capture_output=True,
                                    text=True, timeout=10, check=True)
            target = result.stdout.casefold()
            arch_ok = ("x86_64" in target if ARCH == "x64"
                       else any(i in target for i in ("i686", "i586", "i386")))
            if arch_ok and ("mingw" in target or "w64" in target or "windows" in target):
                return exe
        except (OSError, subprocess.SubprocessError):
            pass
    return None


def _compile_watchdog():
    source = SRC / "watchdog" / "watchdog.cpp"
    destination = SRC / "watchdog" / "bin" / f"d64_watchdog_{ARCH}.exe"
    if not source.is_file():
        raise FileNotFoundError(f"Native watchdog source not found: {source}")

    if (destination.is_file() and destination.stat().st_mtime >= source.stat().st_mtime
            and _native_machine(destination) == MACHINE):
        return destination

    compiler = _compiler()
    if not compiler:
        raise RuntimeError(
            f"No suitable MinGW {ARCH} g++ compiler found. "
            "Install MSYS2 MinGW64/MinGW32, add its bin directory to PATH, "
            "or set D64_WATCHDOG_CXX to the matching g++.exe. "
            "The build intentionally does not silently omit the watchdog."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_name(f".watchdog_{ARCH}_{uuid.uuid4().hex}.exe")
    command = [
        compiler, "-std=c++17", "-O2", "-municode", "-mwindows",
        "-D_WIN32_WINNT=0x0601", "-static", "-static-libgcc",
        "-static-libstdc++", "-o", str(temp), str(source),
        "-lshell32", "-luser32",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                errors="replace", timeout=180, check=False)
        if result.returncode != 0:
            raise RuntimeError(
                "Watchdog C++ build failed:\n" +
                (result.stderr or result.stdout or f"Exit {result.returncode}")[-9000:]
            )
        if _native_machine(temp) != MACHINE:
            raise RuntimeError(f"Compiled watchdog PE machine does not match {ARCH}")
        os.replace(temp, destination)
    finally:
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass
    print(f"[D64] Including native watchdog ({ARCH}): {destination}")
    return destination


watchdog_binary = _compile_watchdog()

datas = []
for name, output in (
    ("C64Pro.ttf", "."),
    ("C64Pro.petscii.json", "."),
    ("periodic_elements.json", "."),
    ("odbc_bitness_bridge.ps1", "."),
    ("help", "help"),
    ("locales", "locales"),
    ("examples", "examples"),
    ("runtime/graphics", "runtime/graphics"),
    ("runtime/pascal/test", "runtime/pascal/test"),
    ("c64c/include", "c64c/include"),
):
    path = SRC / name
    if path.exists():
        datas.append((str(path), output))

binaries = [(str(watchdog_binary), "watchdog/bin")]
for filename in (
    "d64qt5.dll", "libd64_qt5.dll", "libgcc_s_dw2-1.dll",
    "libstdc++-6.dll", "libwinpthread-1.dll",
    "d64_workstation_runner.exe",
):
    path = SRC / filename
    if path.is_file():
        binaries.append((str(path), "."))

# Licensed C64Pro Mono font is optional and only copied when locally present.
for filename in ("C64ProMono.ttf", "C64 Pro Mono.ttf",
                 "C64ProMono.otf", "C64 Pro Mono.otf"):
    path = SRC / filename
    if path.is_file():
        datas.append((str(path), "."))
        break

hiddenimports = [
    "watchdog.gui_errors", "watchdog.native_watchdog",
    "PyQt5.QtWebEngineWidgets", "PyQt5.QtWebEngineCore", "PyQt5.QtWebEngine",
    "pyodbc", "c64packer", "c64_d64_disk", "c64_vice_assets",
    "c64_software_sprite", "c64_bitmap_sprite",
    "c64_bitmap_sprite_editor", "resource_multilang",
    "resource_multilang_integration",
]

a = Analysis(
    [str(SRC / "__main__.py")],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(SRC / "pyi_rth_d64_qtwebengine.py")],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="d64_dism",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # Keep diagnostics visible during initial Windows smoke tests.
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
