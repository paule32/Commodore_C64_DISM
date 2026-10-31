[Deutsch](STAGE415_VICE_BASIC_TAB_HOST_SPRITE.md) | [English](STAGE415_VICE_BASIC_TAB_HOST_SPRITE.en.md)

# Stage 415 – C64 BASIC Debugging: Tabs and Sprite Source

**Basis:** `d64_dism_asm_414.zip`.

## Reported error

During VICE BASIC debug transfer, a Unicode TAB from the editor (`U+0009`, for example in long REM lines) could trigger: `Character cannot be encoded as PETSCII for VICE BASIC debug transfer`. This is **not an error in the sprite file** and does not necessarily mean `LOAD SPRITE` failed earlier.

## Correction

`c64_basic_text_to_petscii` replaces each Unicode TAB with a PETSCII space (`$20`) **only when encoding VICE keyboard-feed text**. Source code, editor contents, and saved `.bas` files are not rewritten. C64Pro private-use PETSCII characters `U+E000`–`U+E0FF` retain their mappings, and unrelated unrepresentable characters still produce explicit errors. A TAB within a BASIC string also becomes a space during direct debug transfer; use care with character-exact data.

## Distinguishing the load paths

- `LOAD SPRITE "sprites.spr"` during direct BASIC→VICE debugging reads the **Windows host file** relative to the source and sends its bitmap bytes via the VICE Binary Monitor to RAM (default `$3000`). The log indicates `HOST/WINDOWS -> VICE BINARY MONITOR` and the transfer size.
- `LOAD "sprites.spr",8,1` is a **C64 KERNAL disk load** from drive 8 and its mounted D64; logs may include `VICE D64 ATTACH: -8 ...`.
- Compiled `LOAD SPRITE` embeds bytes into the PRG at compile time and copies them into RAM during execution.

Merely mounting a disk does **not** mean the special `LOAD SPRITE` command reads from that disk.

## Tests

The Stage-415, 413, 414, 410, and 412 suites passed 31 tests. GUI/compiler/asset/D64 syntax checks passed. A complete real Windows/VICE GUI run remains outstanding.
