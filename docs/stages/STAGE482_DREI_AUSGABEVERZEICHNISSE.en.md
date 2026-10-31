[Deutsch](STAGE482_DREI_AUSGABEVERZEICHNISSE.md) | [English](STAGE482_DREI_AUSGABEVERZEICHNISSE.en.md)

# Stage 482 – Three Separate Windows Compiler Output Directories

Expands Windows PE32/PE32+ settings to three independent output locations: assembler cache/intermediate files, object and Pascal unit files, and final executable output. Generated `.asm` and `.extern.inc`/`.payload.inc` use the configured assembler cache; `.o`/`.obj` and Pascal `.pui` use the third directory when set, falling back to the legacy object path; `.exe`/`.dll` use the executable destination. Pascal-specific project keys include `__windows_pe32_pascal_unit_output__` and `__windows_pe64_pascal_unit_output__`. Relative paths resolve against the active project; tests check save/reload and compiler routing.
