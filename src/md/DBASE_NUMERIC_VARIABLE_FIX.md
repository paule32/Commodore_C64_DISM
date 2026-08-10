# dBase numeric variable output fix

This patch fixes the PE32 runtime case:

```dbase
X = 2 + 3 * 4
? "Wert von X = " + X
```

Expected output:

```text
Wert von X = 14
```

## Root cause

The dBase runtime converts numeric doubles with `_gcvt`. On PE32 it passes the
64-bit double as two 32-bit stack words. The previous generated code used
`[__dbase_temp_number+4]` for the high word. The internal PE32 assembler
recognized the expression but discarded the `+4` addend for a DIR32 symbol
relocation. Both pushes therefore read the low dword. For values such as 14.0
the low dword is zero, so `_gcvt` received 0.0.

## Fix

1. PE32 DIR32 symbol relocations now preserve the encoded displacement addend.
2. The dBase compiler also gives the high dword its own label
   `__dbase_temp_number_hi`, avoiding an unnecessary symbol+4 dependency in
   the numeric formatting ABI.
3. Regression tests verify the exact user case, the PE32 relocation addend,
   and PE32/PE32+ linking.

All existing tests plus the new regression tests pass.
