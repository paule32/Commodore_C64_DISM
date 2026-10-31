#!/usr/bin/env bash
# Run in MSYS2 MINGW32 or MINGW64 shell (zlib development package needed).
set -euo pipefail
cd "$(dirname "$0")"
case "$(gcc -dumpmachine)" in
  i686-w64-mingw32) bits=win32 ;;
  x86_64-w64-mingw32) bits=win64 ;;
  *) echo 'Bitte MSYS2 MINGW32 oder MINGW64 verwenden.' >&2; exit 2 ;;
esac
mkdir -p "$bits"
gcc -O2 -std=c11 -Wall -Wextra -DD64RESOURCE_BUILD -shared \
  -o "$bits/d64resource.dll" d64resource.c -lz \
  -Wl,--out-implib,"$bits/libd64resource.dll.a"
gcc -O2 -std=c11 -Wall -Wextra -DD64RESOURCE_STATIC -c \
  d64resource.c -o "$bits/d64resource.o"
echo "Fertig: $bits/d64resource.dll (Runtime), $bits/d64resource.o (EXE statisch linkbar)"
echo 'Hinweis: mit -lz dynamisch gelinkt kann zlib1.dll benötigt werden.'
gcc -O2 -std=c11 -Wall -Wextra -municode -DD64RESOURCE_STATIC \
  -o "$bits/demo_standalone.exe" demo_win.c d64resource.c -lz
gcc -O2 -std=c11 -Wall -Wextra -municode -DD64_DYNAMIC_LOADER \
  -o "$bits/demo_external_dll.exe" demo_win.c
