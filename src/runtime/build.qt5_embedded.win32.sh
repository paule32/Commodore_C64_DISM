#!/usr/bin/env bash
# Stage 678: embed freestanding PE32 JIT runtime in libd64_qt5.dll.
# Run from MSYS2 MINGW32; does not build or depend on libd64_runtime.dll.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
[[ "${MSYSTEM:-}" == 'MINGW32' ]] || { echo 'FEHLER: MSYS2 MINGW32 benoetigt.' >&2; exit 1; }
[[ "$(g++ -dumpmachine)" == i686-w64-mingw32 ]] || { echo 'FEHLER: i686-w64-mingw32 erforderlich.' >&2; exit 1; }
for tool in g++ nasm ar; do command -v "$tool" >/dev/null || { echo "FEHLER: $tool fehlt." >&2; exit 1; }; done
out=win32/qt5_embedded
mkdir -p "$out"
modules=(dbase_runtime_merged jitObject args error exception print locale windows qt5_embedded_misc)
objs=()
for name in "${modules[@]}"; do
    g++ -O1 -m32 -std=c++20 -fPIC -DDLL_BUILD -DD64_QT5_EMBEDDED \
       -nostdinc -fno-exceptions -fno-rtti -fno-threadsafe-statics \
       -fno-builtin-memset -fno-builtin-memcpy -fno-builtin-memmove \
       -fno-stack-protector -I. -c "$name.cc" -o "$out/$name.o"
    objs+=("$out/$name.o")
done
nasm -Ox -f win32 -dD64_QT5_EMBEDDED=1 -dDYNSTRING_MAGIC=0x44535452 \
    -dJIT_RUNTIME_ERROR=5 -dJIT_RESOLVE_AUX=1 memory_nt32.asm -o "$out/memory.o"
nasm -f win32 -o "$out/setjmp32.o" setjmp32.asm
nasm -Ox -f win32 -dJIT_PASCAL_RUNTIME_INTERNAL=1 -o "$out/pas_inttostr.o" pascal/inttostr.asm
nasm -Ox -f win32 -o "$out/pas_strtoint.o" pascal/strtoint.asm
nasm -Ox -f win32 -o "$out/pas_cookie32.o" pascal/cookie32.asm
objs+=("$out/memory.o" "$out/setjmp32.o" "$out/pas_inttostr.o" "$out/pas_strtoint.o" "$out/pas_cookie32.o")
rm -f win32/libd64_qt5_native.a
ar rcs win32/libd64_qt5_native.a "${objs[@]}"
echo "Qt5 embedded runtime: $(pwd)/win32/libd64_qt5_native.a"
