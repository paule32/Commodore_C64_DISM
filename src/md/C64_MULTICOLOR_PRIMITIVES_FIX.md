# C64 multicolor primitive rendering fix

## Problem

The direct 6510 primitive implementations fixed the geometry, but the standard
VIC-II 320x200 HiRes bitmap still allowed only two colours per 8x8 cell:

- one background colour;
- one foreground colour.

The shared demo needs several colours in the same cell. Examples are the white
diagonal crossing the red rectangle, the green circle with a white border, and
the overlapping blue, yellow and white triangles. The former "first colour
owns the cell" strategy therefore produced white rectangle fragments, an
uneven circle interior and coloured blocks inside the triangle.

## Target-specific solution

The public C and Pascal API remains unchanged and still accepts coordinates in
this range:

```text
X = 0..319
Y = 0..199
```

The C64 backend now uses the VIC-II multicolor bitmap format. The displayed
screen remains 320x200, but one multicolor pixel is two hardware pixels wide.
Therefore `X` and `X xor 1` address the same two-bit bitmap field. Positions and
object dimensions remain in the same 320x200 coordinate system; horizontal
colour detail has two-pixel granularity.

Each 8x8 display cell now has four usable colours:

```text
code 0  global background from $D021
code 1  high nibble of screen RAM
code 2  low nibble of screen RAM
code 3  colour RAM
```

This is sufficient for all colour combinations in `graphics_demo.c`.

## Memory layout

```text
$8800-$8BE7  palette-slot usage flags for 1000 cells
$8C00-$8FE7  screen RAM: local colours 1 and 2
$9000-$92FF  FloodFill work stack
$A000-$BF3F  8000-byte multicolor bitmap
$D800-$DBE7  colour RAM: local colour 3
$4000-$5B0F  direct MOS-6510 graphics runtime
```

VIC-II bank 2 remains selected. `$D018 = $38` selects screen RAM at `$8C00`
and bitmap RAM at `$A000`. `$D016` is programmed with bit 4 set to enable
multicolor bitmap rendering.

## Per-cell palette allocator

`SetPixel` first checks whether the requested colour already exists in one of
the three local palette slots. If not, it allocates the first free slot. The
bitmap pair receives the corresponding two-bit code without changing colours
already used by other pixels in the cell.

A diagnostic byte named `__gfx_palette_overflow` is incremented only if a cell
needs more than three non-background colours. The complete graphics demo ends
with a value of zero, so every requested demo colour is represented directly.

## Result

The C64 version now preserves:

- the uninterrupted red `DrawRect` border;
- the solid cyan `FillRect` interior and white border;
- the solid green `FillCircle` interior and white border;
- the purple circle;
- the blue outline, yellow fill and white border of the overlapping triangles;
- the white lines drawn by `DrawLine` and `DrawTriangleAngles`.

The Amiga backend remains unchanged and continues to use its four 320x200
bitplanes.

## Hardware limitation

A stock VIC-II cannot provide arbitrary 16-colour pixels at true 320-pixel
horizontal colour resolution. The selected multicolor format is the stable,
non-interlaced hardware mode that can represent the demo's overlapping colours.
It keeps the same API and physical screen placement at the cost of two-pixel
horizontal colour granularity.
