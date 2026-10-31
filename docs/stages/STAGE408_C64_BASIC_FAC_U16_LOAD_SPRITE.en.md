[Deutsch](STAGE408_C64_BASIC_FAC_U16_LOAD_SPRITE.md) | [English](STAGE408_C64_BASIC_FAC_U16_LOAD_SPRITE.en.md)

# Stage 408 – KERNAL LOAD, Sprite POKEs, and FAC Integer Conversion

**Basis:** `d64_dism_asm_407.zip`.

## Reproducible conversion bug

The C64 BASIC runtime used this sequence for `__basic_fac_to_int`:

```asm
jsr $B1AA
 tax
 tya
 rts
```

KERNAL/ROM routine FACINX at `$B1AA` returns the low byte in A and the high byte in Y. The old sequence moved the low byte into X, then overwrote A with the high byte, swapping the expected register order in downstream operations.

## Correction

The FAC-to-integer conversion now preserves the actual low/high bytes in the registers expected by generated arithmetic and POKE code. This is particularly important for addresses and values used in sprite setup, alongside KERNAL `LOAD` and target `$3000`.

## Verification

Generated MOS6510 assembly should be inspected at the conversion call site and compared against C64 ROM register conventions. Tests cover compiled numeric expressions and sprite-related POKEs; actual VICE runtime must be confirmed separately.

## Source code and command examples (unchanged)

```
jsr $B1AA
 tax
 tya
 rts
```


```
__basic_fac_to_int:
    jsr $BC9B   ; QINT FAC -> vorzeichenbehafteter 32-bit integer, $62-$65
    lda $65     ; Low-Byte
    ldx $64     ; High-Byte
    rts
```

