[Deutsch](STAGE397_VICII_SPRITE_HARDWARE_FARBEN.md) | [English](STAGE397_VICII_SPRITE_HARDWARE_FARBEN.en.md)

# Stage 397 – C64 Sprite Builder: Real VIC-II Hardware Colors

**Authoritative basis:** `d64_dism_asm_396.zip`.

## Background

C64 VIC-II sprites are **not arbitrary 16-color bitmaps**:

- HiRes: 24 × 21 pixels, either transparent or exactly **one** sprite color (registers `$D027`–`$D02E`).
- Multicolor: 12 × 21 double-width pixels, transparent or three visible colors: **MC1** (`$D025`), the individual **sprite color** (`$D027 + index`), and **MC2** (`$D026`).
- Color registers hold a C64 palette **index from 0 to 15**. MC1 and MC2 are shared by all eight simultaneously visible sprites.
- The screen background is **not a fourth sprite color**. Pixel value zero is transparent.
- The VIC-II expansion registers `$D01D` and `$D017` double width/height without adding bitmap pixels.

## GUI additions

Within `C64SpriteEditorDialog`, below the **16 C64 palette colors**:

1. **Draw with**: Transparent / MC1 / Sprite / MC2, as supported by the current mode.
2. Three clearly labeled register-color selectors with all 16 palette indices and previews.
3. Existing palette swatches select the active drawing value.
4. Multicolor registers are not editable in HiRes mode, while the sprite color is.
5. Editing `$D025` or `$D026` synchronizes metadata for **all sprites** in the document.
6. The editor explains the one/three-color hardware constraints and what `.spr`/`.bin` preserve.

## Saving

- `.c64sprite` stores bitmap, selected hardware color registers, palette, mode, and expansion attributes.
- `.spr`, `.sprite`, and `.bin` still save **only 63/64 raw hardware bitmap bytes**. The C64 program must configure the color and Multicolor registers itself.
- If old `.c64sprite` files contain inconsistent global MC colors, the **first sprite record** determines `$D025`/`$D026`; remaining metadata is normalized to match the hardware.
- The editor intentionally does **not** emulate 16 independent colors within one hardware sprite.

## Tests

`test_stage397_sprite_hardware_colors.py` covers indices 0–15, register addresses, shared MC synchronization, HiRes/Multicolor pixel codes, file I/O, and GUI methods without Qt5. Stage-396 tests are retained. An interactive Windows/PyQt5 test was not possible.
