# C64 C array declaration mask fix

## Symptom

Compiling `runtime/graphics/common/graphics_api.c` failed at the return
expression in `gfx_flood_load_x` with:

```text
__c_array_global_0_GfxFloodXLow kann nicht als skalarer Ausdruck geladen werden.
```

## Root cause

The source-level array lowering used one permissive declaration regular
expression. It accepted arbitrary identifiers as type names and searched
comments as well as ordinary code. Consequently this valid expression:

```c
return GfxFloodXLow[index] |
       (GfxFloodXHigh[index] << 8);
```

was interpreted as if `return` were a user-defined type and
`GfxFloodXLow[index]` were an array declaration. The lowering removed the
first `[index]`, leaving the array object itself as a scalar operand.

Array examples inside block comments were also registered as real arrays.

## Correction

`_mask_c_comments_and_literals()` now produces a length- and line-preserving
view of the source. Array declarations are detected only in that masked view,
while replacements are applied to the original source in reverse offset
order. Control-flow keywords, especially `return`, are excluded from the
user-defined type alternative.

The corrected lowering keeps both accesses in `gfx_flood_load_x`:

```c
return __d64_arr_get_1(GfxFloodXLow, index) |
       __d64_shl(__d64_arr_get_1(GfxFloodXHigh, index), 8);
```
