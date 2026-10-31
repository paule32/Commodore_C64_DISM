[Deutsch](STAGE404_C64_SPRITES_ORIGINALFORMAT.md) | [English](STAGE404_C64_SPRITES_ORIGINALFORMAT.en.md)

# Stage 404 – C64 Sprites Stored as Original VIC-II Raw Data

**Basis:** `d64_dism_asm_403.zip`, with other components unchanged.

## Problem and correction

The sprite builder previously defaulted to `.c64sprite`, a JSON document containing `data_hex`, palette, colors, mode, and scaling flags. A C64 cannot use this JSON file directly as a hardware sprite. Stage 404 changes the **default output format to `.spr`**.

- **New Sprite** and **Save As** now suggest `.spr`.
- `.spr`, `.sprite`, and `.bin` always contain **raw binary bytes**, never JSON or textual hexadecimal lists.
- One hardware sprite contains **63 image bytes**; the usual 64-byte record has one alignment byte, whose value is preserved when loading/saving.
- Existing 63-byte and 64-byte records are supported; new files use **64 bytes per sprite**. Eight sprites occupy 512 bytes, written consecutively.
- No two-byte PRG load address is prepended. The Stage-402 VICE staging path creates a separate `$3000`-header copy for BASIC `LOAD ...,8,1`.
- Existing `.c64sprite` JSON files remain readable. Saving them proposes a new `.spr` file through **Save As**, leaving the original JSON untouched and adding the new file under **C=64 Sprites**.
- Unsaved tree entries are named `Sprite_1.spr`, `Sprite_2.spr`, etc.; project persistence still saves only actual file references.

## VIC-II limitations

Raw sprite files do **not** store colors, RGB palettes, HiRes/Multicolor settings, or expansion flags. The paint tools still offer all 16 colors, but loading raw `.spr` resets mode/register selections to editor defaults. A C64 BASIC or assembly program must set `$D01C`, `$D025`, `$D026`, `$D027`–`$D02E`, etc. Bitmap data itself is not lost.

## Tests

`test_stage404_sprite_native_storage.py` covers default extension, 64-byte binary output, 63/64-byte round trips, JSON migration, and refusal to export JSON as raw sprite data. Existing pixel-codec, hardware register, project-tree, and VICE staging tests remain applicable. Interactive Windows/PyQt5 validation is outstanding.
