[Deutsch](STAGE417_C64_SOFTWARE_BITMAP_SPRITES.md) | [English](STAGE417_C64_SOFTWARE_BITMAP_SPRITES.en.md)

# Stage 417 – C64 BASIC Commands for Bitmap and Software Sprites

**Basis:** `d64_dism_asm_416.zip` (see the German release notes for the exact baseline).

Builds on Stage 416 without replacing existing functionality. The BASIC compiler accepts `LOAD SPRITE "name.bmsprite"`/`.bmspr`, preserving the native binary pixel data (palette indices 0–15, transparent = 255). Existing `LOAD SPRITE "name.spr"` continues to support hardware sprites.

`SCREEN ON` saves VIC-II screen mode/bank and color state and enables a multicolor bitmap; `SCREEN OFF` restores it. `SPRITE SOFTWARE ON/OFF` enables the generated drawing runtime. `SPRITE DRAW N,X,Y` blits transparent software sprites; `SPRITE ERASE N` removes a sprite and recomposes the scene; `SCREEN WAIT` pauses until a key is pressed. Rendering respects the VIC-II restriction of four colors per 8×8 multicolor cell. The compiler initially prepares scenes with mostly constant coordinates; dynamic movement, full per-pixel 16-color hardware display, and direct BASIC-to-VICE debug support are not promised. Tests cover generated instructions and sprite data.

## Source code and command examples (unchanged)

```basic
10 LOAD SPRITE "figuren.spr"
20 SCREEN ON
30 SPRITE SOFTWARE ON
40 SPRITE DRAW 0,100,80
45 SCREEN WAIT
50 SPRITE DRAW 1,140,80
55 SCREEN WAIT
60 SPRITE ERASE 0
65 SCREEN WAIT
70 SCREEN OFF
80 END
```

