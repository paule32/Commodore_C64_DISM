[Deutsch](STAGE486_LINUX_ELF32_ELF64.md) | [English](STAGE486_LINUX_ELF32_ELF64.en.md)

# Stage 486 – Ubuntu 22.04: First Internal ELF32 and ELF64 Toolchain

Adds initial Linux Ubuntu 22.04 32-bit/64-bit target selections in the **Build** menu alongside Windows PE32/PE64. The internal toolchain can emit i386 ELF32 and AMD64 ELF64 code/objects and perform limited native ELF linking. UI target choices are mutually exclusive, and compile/assemble/start routes use the selected architecture. The initial implementation is explicitly a **subset**, not a complete Linux port of every language/runtime. The documentation describes supported ELF headers, relocations, basic sample programs, and test boundaries.
