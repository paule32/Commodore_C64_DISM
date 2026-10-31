[Deutsch](STAGE393_C64_HEX_BUILD_PETSCII_JSON.md) | [English](STAGE393_C64_HEX_BUILD_PETSCII_JSON.en.md)

# Stage 393 – C64 Hex Viewer: Build Refresh and JSON PETSCII Mapping

**Authoritative starting point:** `d64_dism_asm_392(1).zip` (user upload).  
**Changed files:** `d64_dism.py`, `d64_dism.spec`, new `C64Pro.petscii.json`, and a new regression test.

## Hex refresh after a successful build

Following successful assembly by `assemble_document()` (C64 assembler sources) or `assemble_generated_document()` (ASM tabs generated from BASIC, Pascal, C, etc.):

1. The output file is written completely.
2. `_refresh_assembled_hex_view(document, output_path)` reads the **final file** from disk.
3. `DocumentEditor.show_assembled_hex_bytes(...)` refreshes the hex viewer and activates its tab.
4. The bytes are shown as **eight bytes per line**, arranged in two groups of four, with a PETSCII column.
5. For C64 `.prg` files, both header bytes (little-endian load address) remain visible. The address column displays **file offsets**, not CPU runtime addresses.
6. When source code changes, the hex viewer returns to the source representation. Rebuilding reloads the new output bytes.

The build snapshot is read-only (navigation and copying are allowed). Editing remains available in the normal hex editor for actual binary documents. The byte view and source-saving path are separate, preventing Ctrl+S from accidentally saving a generated PRG as source code. Reassembly of an existing PRG document is also handled.

## PETSCII / C64Pro.ttf

- `C64Pro.petscii.json` contains all **256** PETSCII byte values (`0x00`–`0xFF`) and their Unicode code points (`U+XXXX`).
- Initially, it deliberately preserves the internal Stage-392 mapping: **no silent glyph changes**.
- Loader: `load_c64_petscii_unicode_map()` in `d64_dism.py`.
- The hex viewer renders the right-hand character column using the **existing C64Pro.ttf font**. This font must be supplied locally and is not included in the archive.
- After editing the JSON file, **restart the IDE** to reload the mapping.
- A missing, invalid, or incomplete mapping falls back to the internal table and prints a diagnostic to stdout.
- Normal Python startup looks for the JSON file beside `d64_dism.py`; the PyInstaller specification copies it beside `d64_dism.exe`.
- Some PETSCII control mappings intentionally use Unicode control characters such as CR/LF; actual glyph rendering depends on the font. Adjust code points to suit the installed C64Pro.ttf version.

## Tests

```cmd
py -m py_compile d64_dism.py
py -m unittest -v test_stage393_hex_refresh.py
```

Coverage includes the completeness and compatibility of all 256 mappings, custom and corrupted JSON, final file bytes, safe build snapshots, repeated builds, PRG input protection, read-only mutations, and both assembly paths.

A complete interactive Windows/PyQt5 test was not possible because PyQt5 was unavailable in the test environment. Recommended manual sequence: C64 BASIC → Compile → ASM tab → Assemble → Hex tab; edit the source and rebuild. Also assemble a separate `.asm` file and compare the PRG header bytes.
