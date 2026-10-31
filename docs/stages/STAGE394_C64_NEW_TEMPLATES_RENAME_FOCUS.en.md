[Deutsch](STAGE394_C64_NEW_TEMPLATES_RENAME_FOCUS.md) | [English](STAGE394_C64_NEW_TEMPLATES_RENAME_FOCUS.en.md)

# Stage 394 – New C64 Programs, Renaming, and Hex Focus

**Authoritative starting point:** `d64_dism_asm_393.zip`.

## 1. Hex viewer

Successful assembly continues to load the actual output bytes into the hex buffer. However, `show_assembled_hex_bytes()` **no longer forces a switch to the Hex tab**. The active assembler/BASIC editor and its input focus remain unchanged until the user selects another tab.

## 2. File → New → C= 64 m68k

- **BASIC Program:** Creates an in-memory, numbered BASIC template and an unsaved leaf under **BASIC Programs**.
- **Assembler Program:** Creates an in-memory MOS6510 template containing `.org`, `.entry`, and `start:`/`rts`, with an unsaved leaf under **Assembler Programs → Commodore C= 64**.
- Both leaf and document have an explicit **new-file flag** (`Qt.UserRole + 307` and `_is_new_c64_project_file`). Until the first successful save, `document.path` is `None`. Templates are not silently written into the project directory.
- First Ctrl+S or Save opens **Save As**, with file/directory selection and type-specific extensions. This first save must not overwrite existing files.
- On success, the leaf name and path are updated, the new-file flag is cleared, and the entry is saved to the existing project INI. A canceled or failed save changes neither the flag nor the path.
- Closing an unsaved template always offers Save/Discard/Cancel, even if the default template has not been edited. Discard removes its nonpersistent leaf.

## 3. Project Information → Rename

The **Rename** context command is available for source leaves under BASIC (including Commodore C= 64) and Assembler Programs (including the C64 branch).

It reuses the Stage-338 rename dialog in **dark and light themes**. Validation covers the suggested filename, extension, existing files and case-insensitive collisions, write permission, and the actual filesystem rename. On conflict, an error dialog appears without changing the source, destination, or leaf. On success, all project references and open editor tabs are updated and the project INI is saved.

## 4. Verification

- `python -m py_compile d64_dism.py` – passed.
- `python -m unittest -v test_stage393_hex_refresh.py test_stage394_c64_new_rename.py` – 15 isolated tests passed without PyQt5.
- ZIP integrity checked.
- Full interactive Windows/PyQt5 testing remains necessary.
