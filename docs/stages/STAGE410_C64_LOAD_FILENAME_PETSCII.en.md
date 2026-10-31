[Deutsch](STAGE410_C64_LOAD_FILENAME_PETSCII.md) | [English](STAGE410_C64_LOAD_FILENAME_PETSCII.en.md)

# Stage 410 – PETSCII Encoding for C64 BASIC LOAD Filenames

**Basis:** `d64_dism_asm_409.zip`.

## Verified mismatch

The compiler previously encoded `LOAD "sprites.spr",8,1` as the lowercase ASCII bytes:

```text
73 70 72 69 74 65 73 2E 73 70 72     sprites.spr
```

However, the Stage-409 D64 writer stored the file in uppercase Commodore/PETSCII form:

```text
53 50 52 49 54 45 53 2E 53 50 52     SPRITES.SPR
```

These names differ at the byte level, so KERNAL file lookup can fail even when the disk image contains the file.

## Fix

BASIC `LOAD` filenames now follow Commodore/PETSCII rules consistent with the D64 directory. The conversion is confined to the filename parameter: source text, host filenames, and unrelated string operations must not be accidentally changed.

## Verification

Tests should compare the exact SETNAM byte string to the D64 directory filename and verify existing `LOAD` forms. The corrected encoding is necessary but not proof that all VICE runtime or pointer-related errors have been fixed.

## Source code and command examples (unchanged)

```
73 70 72 69 74 65 73 2E 73 70 72     sprites.spr
```


```
53 50 52 49 54 45 53 2E 53 50 52     SPRITES.SPR
```

