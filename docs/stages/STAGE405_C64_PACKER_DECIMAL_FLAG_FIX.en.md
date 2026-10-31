[Deutsch](STAGE405_C64_PACKER_DECIMAL_FLAG_FIX.md) | [English](STAGE405_C64_PACKER_DECIMAL_FLAG_FIX.en.md)

# Stage 405 – D64PACK: Decimal Flag in the 6510 Decruncher

**Authoritative basis:** `d64_dism_asm_404.zip`.

## Reported issue

When compiling C64 BASIC to a packed MOS6510 PRG, execution could reportedly end with `?ILLEGAL QUANTITY ERROR IN 10` or other unexpected behavior. That exact message was not reproduced in VICE, but a defect in the packed machine-code bootstrap was reproduced.

## Root cause and fix

The D64PACK bootstrap saved the processor flags with `PHP` and set interrupts with `SEI`, but failed to clear the Decimal flag. The RLE/LZ decruncher uses `ADC` when counting decoded bytes. With `D=1`, decimal BCD arithmetic corrupts address or length calculations. The bootstrap now uses **`CLD` before arithmetic/decompression**, and the original flags are restored afterward, preserving the caller's CPU state. The fix does not change the compressed file format or unrelated optimizations.

## Verification

Tests cover the bootstrap instruction sequence, decimal-safe address arithmetic, and unmodified existing packer behavior. This is a proven bootstrap-level correction, not a claim that every previously reported runtime failure has been reproduced and resolved on actual C64 hardware.

## Source code and command examples (unchanged)

```asm
    php
    pha
    txa
    pha
    tya
    pha
    sei
    cld         ; D64PACK immer binär rechnen lassen
    lda $01
    pha
```


```
python -m unittest -v test_stage405_packer_decimal.py
```

