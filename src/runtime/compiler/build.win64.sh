#!/bin/bash
# ----------------------------------------------------------------------------
# file: build.sh for 64-bit MingW32
# author: (c) 2026 Jens Kallup - paule32
# all rights reserved.
# ----------------------------------------------------------------------------
export PATH=/mingw64/bin:$PATH
TOOLSYS=$(echo $MSYSTEM)
TARGET=$(gcc -dumpmachine)

# ----------------------------------------------------------------------------
# first, we check if we under mingw32, else - abort ...
# ----------------------------------------------------------------------------
if [ "$TOOLSYS" = "MINGW64" ]; then
  echo "MingW64: ok."
else
  echo "Not in MingW64 Shell - aborted."
  exit 1
fi
      
# ----------------------------------------------------------------------------
# next, we check if we have gcc 32-bit toolchain, else - abort ...
# ----------------------------------------------------------------------------
if [ "$TARGET" = "x86_64-w64-mingw32" ]; then
   echo "Toolchain: 64-bit - ok."
   mkdir -p win64/obj

  g++ -O2 -m64 -std=c++20 -shared -IT:/GitHub/asmjit -DASMJIT_STATIC=OFF -DDLL_EXPORT -fPIC -c -o win64/obj/error.o   error.cc
  g++ -O2 -m64 -std=c++20 -shared -IT:/GitHub/asmjit -DASMJIT_STATIC=OFF -DDLL_EXPORT -fPIC -c -o win64/obj/print.o   print.cc
  g++ -O2 -m64 -std=c++20 -shared -IT:/GitHub/asmjit -DASMJIT_STATIC=OFF -DDLL_EXPORT -fPIC -c -o win64/obj/mapping.o mapping.cc
  g++ -O2 -m64 -std=c++20 -shared -IT:/GitHub/asmjit -DASMJIT_STATIC=OFF -DDLL_EXPORT -fPIC -c -o win64/obj/misc.o    misc.cc
  g++ -O2 -m64 -std=c++20 -shared -IT:/GitHub/asmjit -DASMJIT_STATIC=OFF -DDLL_EXPORT -fPIC -c -o win64/obj/memory.o  memory.cc
  g++ -O2 -m64 -std=c++20 -shared -IT:/GitHub/asmjit -DASMJIT_STATIC=OFF -DDLL_EXPORT -fPIC -c -o win64/obj/windows.o windows.cc

  ar rcs win64/libdbase2many.64.a win64/obj/*.o

  g++ -O2 -m64 -std=c++20 -shared -IT:/GitHub/asmjit -DASMJIT_STATIC=OFF -DDLL_EXPORT -fPIC win64/obj/*.o -L. -lkernel32 -o libdbase2many.64.dll

  gendef     libdbase2many.64.dll
  dlltool -d libdbase2many.64.def -l libdbase2many.64.dll.a
  
  strip libdbase2many.32.dll

  cp libdbase2many.64.def   win64/libdbase2many.64.def
  cp libdbase2many.64.dll   win64/libdbase2many.64.dll
  cp libdbase2many.64.dll.a win64/libdbase2many.64.dll.a

  rm libdbase2many.64*
else
  echo "No MingW64 Toolchain - aborted."
  exit 2
fi
