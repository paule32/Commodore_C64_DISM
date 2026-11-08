#!/usr/bin/env bash
set -euo pipefail
# Run from MSYS2 MINGW32; standalone DLL shared by PE32 Pascal applications.
cd "$(dirname "$0")"
[[ "${MSYSTEM:-}" == MINGW32 ]] || { echo 'Use MSYS2 MINGW32' >&2; exit 1; }
mkdir -p win32
"${CXX:-g++}" -O2 -std=c++17 -shared -static -o win32/libd64_console.dll \
    console_runtime.cc libd64_console.def -Wl,--out-implib,win32/libd64_console.dll.a
