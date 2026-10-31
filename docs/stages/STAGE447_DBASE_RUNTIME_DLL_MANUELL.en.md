[Deutsch](STAGE447_DBASE_RUNTIME_DLL_MANUELL.md) | [English](STAGE447_DBASE_RUNTIME_DLL_MANUELL.en.md)

# Stage 447 – Manually Build dBASE Runtime DLLs

Adds Tools-menu entries **Build dBASE Runtime PE32 DLL** and **Build dBASE Runtime PE32+ DLL**, together with corresponding Windows 32-/64-bit environment configuration. The actions use the project's **internal COFF assembler and PE linker**, not an external compiler or `make`. Selected architecture-specific output directories determine where the DLL is written; build failures are reported through the normal UI. Existing runtime-related behavior remains in place. The source notes describe modified files and current validation limits.
