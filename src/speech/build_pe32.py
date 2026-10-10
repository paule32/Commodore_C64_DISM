#!/usr/bin/env python3
"""Standalone Windows 10 PE32 build via MSYS2/MINGW32 gcc; no make required.

Run from any directory: python speech/build_pe32.py
"""
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "bin"
OUT.mkdir(parents=True, exist_ok=True)
CC = os.environ.get("CC", "gcc")
if not shutil.which(CC):
    raise SystemExit(f"GCC nicht gefunden: {CC}. Bitte MSYS2 MINGW32 starten.")
target = subprocess.run([CC, "-dumpmachine"], capture_output=True, text=True,
                        check=True).stdout.strip().lower()
if not (target.startswith(("i686-", "i586-", "i386-")) and "mingw" in target):
    raise SystemExit(f"Falscher GCC-Target: {target}. Windows PE32 braucht MSYS2 MINGW32 (i686-w64-mingw32).")


def run(*args):
    print("+", " ".join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), check=True, cwd=ROOT)


run(CC, "-m32", "-O2", "-std=c99", "-Wall", "-Wextra", "-fno-ident", "-fno-record-gcc-switches",
    "-DRETRO_SPEECH_BUILD", "-shared", "retro_speech.c", "-o", OUT / "retro_speech.dll",
    # Keep the stdcall-decorated aliases needed by gcc (e.g.
    # __imp__SpeechInitialize@4), and also export undecorated aliases
    # (SpeechInitialize) for d64_dism PE32 import-by-name.
    # --kill-at alone breaks the auto-generated MinGW import library.
    "-Wl,--add-stdcall-alias", f"-Wl,--out-implib,{OUT / 'libretro_speech.dll.a'}", "-lwinmm", "-lm")
run(CC, "-m32", "-O2", "-std=c99", "-Wall", "-Wextra", "-fno-ident", "retro_speech_demo.c",
    "-o", OUT / "retro_speech_demo.exe", "-L" + str(OUT), "-lretro_speech")
print("Fertig: retro_speech.dll, libretro_speech.dll.a, retro_speech_demo.exe")
print("Die Demo laedt retro_speech.dll dynamisch. Test: speech\\bin\\retro_speech_demo.exe")
