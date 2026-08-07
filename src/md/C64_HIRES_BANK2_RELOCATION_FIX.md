# C64 HiRes bank-2 relocation fix

The previous HiRes target reserved VIC-II bank 1 (`$4000-$7FFF`).  The complete
C graphics demo, including the common primitive implementation and static data,
ends at `$61FA`, so the assembler correctly rejected the overlap.

The C64-specific graphics target now uses this non-overlapping layout:

```text
$080D-$61FA  generated C program and common graphics code
$8000-$BFFF  VIC-II bank 2, reserved for graphics
$9800-$9BE7  per-cell foreground-owner table
$9C00-$9FE7  HiRes screen/colour matrix
$A000-$BF3F  320x200 bitmap
$C000-$CFFF  C64 graphics assembly runtime
```

CIA2 port A selects bank 2 with bits `%01`.  `$D018=$78` still selects screen
matrix offset `$1C00` and bitmap offset `$2000` inside that bank.

The runtime remains below `$D000`, so it does not enter the C64 I/O area or the
KERNAL ROM window.  The assembler overlap guard now protects `$8000-$BFFF` and
checks that the runtime stays inside `$C000-$CFFF`.
