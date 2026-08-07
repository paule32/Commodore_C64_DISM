# C64 HiRes graphics target fix

## Problem

The shared C graphics demo compiled for both Amiga and C64, but the C64 build
showed random coloured 8x8 blocks instead of the expected primitives.

Three independent causes were present:

1. `InitGraphics()` enabled bitmap mode before the 8000-byte bitmap and the
   1000-byte colour matrix had been cleared.  The old C implementation then
   cleared the visible random RAM through thousands of compiled `poke()` calls.
2. The previous `SetPixel()` replaced the foreground nibble of a complete
   HiRes colour cell for every differently coloured pixel.  One pixel could
   therefore recolour all pixels already present in the same 8x8 cell.
3. Program code and static data were not checked against the VIC-II bank
   `$8000-$BFFF`.  A sufficiently large generated program could overwrite its
   bitmap or screen matrix.

## New target layout

The public API and the common primitive source remain unchanged.  Only the
C64 hardware target is now implemented separately in MOS-6510 assembler:

```text
runtime/graphics/common/graphics_api.c
runtime/graphics/c64/graphics_c64.asm
```

The C and Pascal frontends both select this same target module.

```text
$4000-$57FF  reserved part of VIC-II bank
$9800-$9BE7  colour owner for 1000 HiRes cells
$9C00-$9FE7  HiRes screen/colour matrix
$A000-$BF3F  320x200 bitmap
$8000-$9FFF  C64 target assembler runtime
```

The generated program and common C algorithms must finish below `$4000`.
The assembler reports a clear overlap error instead of producing a damaged
screen.

## InitGraphics

`InitGraphics()` now performs these operations in this order:

1. save the previous VIC-II/CIA2 registers;
2. blank the display;
3. clear bitmap, screen matrix and cell-owner map using page-wide assembler
   loops;
4. configure CIA2 bank 2;
5. select bitmap `$A000` and screen matrix `$9C00`;
6. select 320x200 standard HiRes mode;
7. enable the display.

The uninitialised colourful screen is never made visible.

## C64 colour-cell policy

A standard 320x200 C64 HiRes cell contains eight bitmap bytes and one screen
byte.  Its screen byte supplies one foreground and one background colour for
all 64 pixels.

The target therefore uses a deterministic first-colour policy:

- the first non-background pixel assigns the cell foreground colour;
- subsequent non-background pixels in that cell keep the existing colour;
- clearing the final pixel releases the cell so a later primitive can assign
  a new colour.

This avoids whole-cell recolouring.  It cannot create Amiga-style independent
16-colour pixels because that is not representable in the VIC-II 320x200
HiRes memory format.  Coordinates and primitive geometry remain the same.

## Program termination

A C64 C program that links `graphics_c64.asm` now stays in a generated end
loop after `main()` returns.  BASIC and the KERNAL screen editor therefore do
not resume behind the active bitmap display.  Programs without the graphics
target still return normally with `RTS`.
