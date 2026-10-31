[Deutsch](STAGE398_SPRITE_FARBEN_LIVE_REFRESH.md) | [English](STAGE398_SPRITE_FARBEN_LIVE_REFRESH.en.md)

# Stage 398 – C64 Sprite Builder: Live Colors and Correct Brush Preview

**Authoritative basis:** `d64_dism_asm_397.zip`.

## Cause of the bug

`C64SpriteCanvas.set_data()` and `set_meta()` call `normalize_meta(meta)`, so the canvas holds its **own copy** of sprite metadata. Hardware color selection (`$D025`, `$D026`, `$D027+n`) updated `C64SpriteEditorDialog.metas`, but `_update_palette_buttons()` only refreshed `canvas.palette_entries`. Consequently, `C64SpriteCanvas.paintEvent()` still used stale register values in `canvas.meta`.

## Changes in `d64_dism.py`

1. `C64SpriteCanvas.set_color_registers(meta)` copies all three actual register-color indices into canvas metadata and calls `update()` without altering bitmap bytes or dimensions.
2. `_update_palette_buttons()` now synchronizes **both palette and hardware color registers**.
3. Every pixel code in the existing **Draw with** combo box has a preview swatch (`Qt.DecorationRole`) and tooltip showing its effective register color. HiRes permits transparent/sprite; Multicolor permits transparent/MC1/sprite/MC2.
4. Selecting a palette swatch automatically changes a transparent HiRes brush to the sprite color, matching existing Multicolor behavior.
5. When a HiRes brush is transparent, a color swatch is no longer incorrectly highlighted as the active drawing color.

## Hardware behavior

- HiRes: pixel 0 = transparent; pixel 1 = `$D027+n`.
- Multicolor: pixel 0 = transparent; pixel 1 = `$D025`; pixel 2 = `$D027+n`; pixel 3 = `$D026`.
- All three registers can select any of the 16 C64 palette values; MC1/MC2 remain shared across sprites.
- Changing a color does **not change a single bitmap byte**. `.spr` and `.bin` compatibility is preserved; `.c64sprite` stores register details.

## Test evidence

`test_stage398_sprite_live_colors.py` contains six isolated AST-based tests of real canvas/editor methods without PyQt5. They include MC1=yellow, sprite=blue, MC2=gray, changing colors on already-drawn pixels, brush values 0–3, and unchanged file bytes. Forty additional Stage-393–397 regression tests passed. No interactive Windows/PyQt5 GUI test was run.
