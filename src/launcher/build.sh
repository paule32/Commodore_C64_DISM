#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CXX="${CXX:-g++}"
TARGET="$($CXX -dumpmachine 2>/dev/null || true)"
ARCH_FLAG="${ARCH_FLAG:-}"

if [[ -z "$ARCH_FLAG" ]]; then
    case "$TARGET" in
        i?86-w64-mingw32*) ARCH_FLAG="-m32" ;;
        x86_64-w64-mingw32*) ARCH_FLAG="-m64" ;;
        *)
            case "${MSYSTEM:-}" in
                MINGW32|CLANG32) ARCH_FLAG="-m32" ;;
                MINGW64|UCRT64|CLANG64) ARCH_FLAG="-m64" ;;
                *)
                    echo "Kein MinGW-Windows-Compiler erkannt: $TARGET" >&2
                    echo "Bitte in einer MSYS2 MINGW32/MINGW64/UCRT64 Shell ausfuehren oder CXX/ARCH_FLAG setzen." >&2
                    exit 2
                    ;;
            esac
            ;;
    esac
fi

echo "Compiler : $CXX"
echo "Target   : $TARGET"
echo "Arch     : $ARCH_FLAG"

"$CXX" "$ARCH_FLAG" -std=c++17 -O2 -s -Wall -Wextra -static-libgcc -static-libstdc++ \
    -fno-rtti \
    -ffunction-sections \
    -fdata-sections \
    -Wl,--gc-sections \
    -Wl,--strip-all \
    -municode \
    -mwindows \
    "$HERE/d64_dism_launcher.cpp" \
    -o "$HERE/../start.exe" \
    -lshell32

echo "Erzeugt: $HERE/../start.exe"
