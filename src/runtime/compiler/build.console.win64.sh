#!/usr/bin/env bash
set -euo pipefail
# Run from MSYS2 MINGW64; matches the PE32+ import ABI.
cd "$(dirname "$0")"
[[ "${MSYSTEM:-}" == MINGW64 ]] || { echo 'Use MSYS2 MINGW64' >&2; exit 1; }
mkdir -p win64
"${CXX:-g++}" -O2 -std=c++17 -shared -o win64/libd64_console.dll \
    console_runtime.cc libd64_console.def -Wl,--out-implib,win64/libd64_console.dll.a
