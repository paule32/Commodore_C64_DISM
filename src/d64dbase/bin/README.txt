Stage 446 - d64_dbase_console.dll

pe32/d64_dbase_console.dll = 32-bit i386
pe64/d64_dbase_console.dll = 64-bit AMD64

Do NOT put both binaries into one executable directory. The dBASE compiler
selects and validates the correct binary and copies it next to the linked EXE.
It can also rebuild the binaries using its own internal assembler and PE linker
if the prebuilt files are missing. No external make/gcc is used at build time.
