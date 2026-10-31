[Deutsch](STAGE395_C64_VICE_ASM_CONTEXT.md) | [English](STAGE395_C64_VICE_ASM_CONTEXT.en.md)

# Stage 395 – VICE Context Menus for C64 BASIC and MOS6510 Assembly

**Authoritative basis:** `d64_dism_asm_394.zip`.

## Editor context menu

The C64 BASIC and C64 assembly source editors present the same VICE command section before the standard Qt menu. The formerly disabled bold **Execute** item is now clickable.

| Command | C64 BASIC | C64 Assembler |
|---|---|---|
| Execute | Send `NEW`, BASIC lines, and `RUN` through keyboard feed | Transfer compiled PRG payload to VICE RAM, set PC to entry, EXIT |
| Execute line in VICE | Keyboard-feed the current BASIC line | Load full program and step one machine instruction at that source line's address |
| Execute selection in VICE | Existing BASIC selection/program behavior | Load full program and step as many instructions as the highlighted MOS6510 instructions |
| Transfer program to VICE | `NEW` plus numbered BASIC lines | Load PRG into C64 RAM **without** changing PC |
| Transfer program + RUN / START | BASIC: `RUN` | Assembly: set PC and EXIT |
| Reset VICE BASIC / Continue VICE Monitor | `NEW` | Leave monitor and resume CPU |

Editing, cut/copy/paste, and the operand calculator are retained. The assembly menu is offered for **C64 sources only**, not Amiga or Windows assembly.

## VICE protocol

- Uses the existing VICE Binary Remote Monitor API v2 at `127.0.0.1:6502`, connecting to a running VICE instance or launching one as required.
- `MEMORY_SET` (`0x02`) transfers **payload bytes** from the generated `.prg`, excluding its two-byte little-endian load-address header.
- `REGISTERS_AVAILABLE` (`0x83`) finds the PC register ID dynamically; `REGISTERS_SET` (`0x32`) sets PC; the register-set response uses `0x31`.
- `EXIT` (`0xAA`) resumes execution following **Execute**.
- `ADVANCE_INSTRUCTIONS` (`0x71`) executes one or several CPU instructions while remaining in the monitor. Stepping follows the **actual CPU control flow**, which can leave the selected source lines after branches.
- Assembly and transfer run outside the GUI thread. Existing Qt signals/dialogs report errors, and the active IDE tab remains in place.

## Safety and errors

Invalid PRG headers, empty payloads, address overflow, and invalid PCs are detected. If no current build exists, the internal assembler runs before transfer (including Save As for new documents). Line/selection operations assemble the **entire program without the image packer** to retain correct symbols and addresses. A source line with no machine instruction produces an error. Existing F2 builds and Start button behavior are unchanged.

## Tests

```cmd
python -m unittest -v test_stage395_vice_context.py test_stage394_c64_new_rename.py test_stage393_hex_refresh.py
```

These tests do not require PyQt. End-to-end verification against a real VICE instance on Windows is still needed.
