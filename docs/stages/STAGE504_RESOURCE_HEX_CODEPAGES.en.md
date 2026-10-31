[Deutsch](STAGE504_RESOURCE_HEX_CODEPAGES.md) | [English](STAGE504_RESOURCE_HEX_CODEPAGES.en.md)

# Stage 504 – Resource Editor Hex Viewer and Codepages

Fixes a mismatch between displayed codepage and actual compiled RC bytes. Before Stage 504, the right-hand hex text column always used a static ASCII-like byte view, while `RCDATA` and `DLGINCLUDE` narrow string literals were compiled as CP1252 even with `#pragma code_page(65001)` (UTF-8) or `#pragma code_page(1200)` (Unicode). Selecting another codepage could update only metadata, leaving the hex bytes unchanged.

The RC compiler and hex preview now distinguish ASCII, UTF-8, and Unicode payloads where the Windows resource format permits that distinction. Native Windows resource types that mandate UTF-16LE remain standards-compliant. Tests include raw byte and codepage preview checks; `python -m py_compile d64_dism.py` passed.

## Source code and command examples (unchanged)

```rc
#pragma code_page(65001)
101 RCDATA
BEGIN
    "Grüße"
END
```

