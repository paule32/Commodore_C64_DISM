[Deutsch](STAGE493_WFM_LINUX_TARGET_ASM_ROUTING.md) | [English](STAGE493_WFM_LINUX_TARGET_ASM_ROUTING.en.md)

# Stage 493 – WFM Target Architecture and Assembly Output Names

Corrects dispatch when assembling generated WFM files for different target systems. The selected target maps to the corresponding source and object path: `Form2.generated.pe32.asm` → PE32 COFF, `.pe64.asm` → PE64 COFF, `.linux32.asm` → i386 ELF32, and `.linux64.asm` → AMD64 ELF64. Compile, Assemble, and Start must not silently use a stale Windows target when the form is set to Linux. Tests inspect path, backend, and architecture routing; live Windows/Linux verification remains distinct.
