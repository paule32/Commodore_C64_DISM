# C64 bitmap RAM below BASIC ROM

## Symptom

The VIC-II entered HiRes bitmap mode, but drawing produced coloured 8x8 blocks
and apparently random patterns instead of clean primitives.

## Cause

The bank-2 bitmap occupies `$A000-$BF3F`.  With the normal CPU memory map,
BASIC ROM is visible at `$A000-$BFFF`.  Writes still reach the RAM below the
ROM, so clearing the bitmap appeared to work.  Reads performed by the
read/modify/write pixel routines came from BASIC ROM, however.  Those ROM
bytes were ORed or ANDed with pixel masks and then written into bitmap RAM.

## Fix

`InitGraphics` saves processor port `$01` and clears only bit 0 (`LORAM`).
This exposes RAM at `$A000-$BFFF` while leaving I/O and KERNAL ROM visible.
`DoneGraphics` restores the saved processor-port value.

The public C and Pascal graphics API remains identical on C64 and Amiga; only
the C64 target assembler contains this memory-mapping operation.
