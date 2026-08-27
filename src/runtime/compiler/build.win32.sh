#!/bin/bash
# ----------------------------------------------------------------------------
# file: build.sh for 32-bit MingW32
# author: (c) 2026 Jens Kallup - paule32
# all rights reserved.
# ----------------------------------------------------------------------------
export PATH=/mingw32/bin:$PATH
TOOLSYS=$(echo $MSYSTEM)
TARGET=$(gcc -dumpmachine)

# ----------------------------------------------------------------------------
# first, we check if we under mingw32, else - abort ...
# ----------------------------------------------------------------------------
if [ "$TOOLSYS" = "MINGW32" ]; then
  echo "MingW32: ok"
else
  echo "Not in MingW32 Shell - aborted."
  exit 1
fi

# ----------------------------------------------------------------------------
# next, we check if we have gcc 32-bit toolchain, else - abort ...
# ----------------------------------------------------------------------------
if [ "$TARGET" = "i686-w64-mingw32" ]; then
  echo "Toolchain: 32-bit - ok."
  BASEDIR=$(pwd)
echo "123"
  # ------------------------------
  # compile crypto modules ...
  # ------------------------------
  CRYPTO_FILES=(
    blake2 blake3
    crc16  crc32  crc32c crc64 md5
    sha1   sha3   sha224
    sha256 sha384 sha512
  )
  for dir in "${CRYPTO_FILES[@]}"; do
    mkdir -p "win32/obj/crypto/$dir"
    echo "assemble: crypto/$dir/$dir.cc"
    if ! g++ -O1 -m32 -std=c++20 -shared -fPIC -DDLL_BUILD -I$BASEDIR -I. \
       -nostdinc -fno-exceptions -fno-rtti -nostdlib++ \
       -fno-threadsafe-statics \
       -Wno-write-strings   \
       -fno-builtin-memset  \
       -fno-builtin-memcpy  \
       -fno-builtin-memmove \
       -S -o win32/obj/crypto/$dir/$dir.s crypto/$dir/$dir.cc ; then
       echo "assemble run error."
       exit 1
    fi
    echo "sed:      win32/obj/crypto/$dir/$dir.s"
    if ! sed -i \
       -e '/^[[:space:]]*\.ident/d'     \
       -e '/^[[:space:]]*\.file/d'      \
       -e '/^[[:space:]]*\.linkonce/d'  \
       -e '/^[[:space:]]*\.def/d'       \
       -e '/^[[:space:]]*\.cfi_/d'      \
       -e 's/\(\.section[[:space:]]*\.text\)\$.*/\1/' \
       -e '/^[[:space:]]*\.section[[:space:]]*\.note\.GNU\-stack/d' \
       win32/obj/crypto/$dir/$dir.s ; then
       echo "sed error."
       exit 1
    fi
    echo "compile:  win32/obj/crypto/$dir/$dir.s"
    if ! g++ -o win32/obj/crypto/$dir/$dir.o -c win32/obj/crypto/$dir/$dir.s ; then
       echo "compile time error."
       exit 1
    fi
    # tiny
    if ! nasm -Ox -f win32 -o win32/obj/crypto/$dir/$dir.o crypto/$dir/$dir.asm ; then
       echo "nasm assembler error."
       exit 1
    fi
  done
  
  nasm -f win32 -Ox \
    -dDYNSTRING_MAGIC=0x44535452 \
    -dJIT_RUNTIME_ERROR=5 \
    -dJIT_RESOLVE_AUX=1 \
    memory_nt32.asm \
    -o win32/obj/memory.o
    
  ###args loader allocator diskio/diskio error exception iostream memory
  RUNTIME_FILES=( jitObject
    args loader allocator error exception iostream
    print string vector locale windows
    dllmain
  )
  if ! mkdir -p win32/obj/diskio ; then
     echo "could not create directory: win32/obj/diskio."
     exit 1
  fi
  for file in "${RUNTIME_FILES[@]}"; do
    echo "assemble: $file.cc"
    if ! g++ -O1 -m32 -std=c++20 -shared -fPIC -DDLL_BUILD -I$BASEDIR -I. \
       -nostdinc -fno-exceptions -fno-rtti -nostdlib++ \
       -fno-threadsafe-statics \
       -Wno-write-strings   \
       -fno-builtin-memset  \
       -fno-builtin-memcpy  \
       -fno-builtin-memmove \
       -S -o win32/obj/$file.s $file.cc ; then
       echo "assemble run error."
       exit 1
    fi
    echo "sed:      $file.s"
    if ! sed -i \
       -e '/^[[:space:]]*\.ident/d'     \
       -e '/^[[:space:]]*\.file/d'      \
       -e '/^[[:space:]]*\.linkonce/d'  \
       -e '/^[[:space:]]*\.def/d'       \
       -e '/^[[:space:]]*\.cfi_/d'      \
       -e 's/\(\.section[[:space:]]*\.text\)\$.*/\1/' \
       -e '/^[[:space:]]*\.section[[:space:]]*\.note\.GNU\-stack/d' win32/obj/$file.s ; then
       echo "sed error."
       exit 1
    fi
    echo "compile:  $file.s"
    if ! g++ -o win32/obj/$file.o -c win32/obj/$file.s ; then
       echo "compile time error."
       exit 1
    fi
  done
  
  nasm -fwin32 -o win32/obj/setjmp32.o setjmp32.asm
  
  RUNTIME_OBJECTS=("${RUNTIME_FILES[@]/#/win32/obj/}")
  RUNTIME_OBJECTS=("${RUNTIME_OBJECTS[@]/%/.o}")
  
  if ! nasm -Ox -f win32 -o win32/obj/crypto/sha512/sha512.o crypto/sha512/sha512.asm ; then
       echo "assemlber could not create object file: sha512.o."
       exit 1
  fi
  ar rcs win32/libcrypto.a win32/obj/crypto/sha512/sha512.o
  
  nasm -f win32 -f win32 -o win32/obj/crypto/blake2/blake2.o crypto/blake2/blake2s.asm
  
  echo "create ALL in One DLL..."
  if ! gcc -m32 -fPIC -shared -nostdlib -o win32/libd64_runtime.dll \
     win32/obj/allocator.o \
     win32/obj/args.o      \
     win32/obj/dllmain.o   \
     win32/obj/error.o     \
     win32/obj/exception.o \
     win32/obj/iostream.o  \
     win32/obj/jitObject.o \
     win32/obj/loader.o    \
     win32/obj/locale.o    \
     win32/obj/memory.o    \
     win32/obj/print.o     \
     win32/obj/setjmp32.o  \
     win32/obj/string.o    \
     win32/obj/vector.o    \
     win32/obj/windows.o   \
     \
     \
     win32/libd64_runtime.def    \
     -Wl,--out-implib,win32/libd64_runtime.dll.a; then
     echo "relocation link error."
     exit 1
  fi
  #win32/obj/diskio/diskio.o        
  strip win32/libd64_runtime.dll
  exit 0
fi
