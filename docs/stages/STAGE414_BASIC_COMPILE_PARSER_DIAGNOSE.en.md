[Deutsch](STAGE414_BASIC_COMPILE_PARSER_DIAGNOSE.md) | [English](STAGE414_BASIC_COMPILE_PARSER_DIAGNOSE.en.md)

# Stage 414 – Expose the C64 BASIC Compiler Path and Actual Parser Statement

**Basis:** `d64_dism_asm_413.zip`.

## Context

A screenshot showed `98 LOAD SPRITE "sprites.spr"` in the editor, but compilation reported `BASIC line 98: Variable or array element expected`. That error originates in assignment-target parsing, whereas the displayed `LOAD SPRITE` statement is supported in Stage 413. The shown test program, including tab characters in REM lines, compiled both directly and after C64 editor wrapping/numbering. **The actual cause of the Windows failure was not demonstrated and is not claimed to be fixed.**

## New diagnostics in `d64_dism.py`

Before compiling C64 BASIC containing a normal `LOAD SPRITE`, the GUI writes diagnostic lines to its existing log, including the compiler module path and an exact `repr` of the source statement:

```text
C64 BASIC COMPILER: T:\...\c64basic\compiler.py; LOAD SPRITE=yes
C64 BASIC INPUT: '98 LOAD SPRITE "sprites.spr"'
```

If the imported compiler lacks `c64_basic_sprite_command`, a specific warning identifies the stale module path rather than reporting misleading generic syntax. On parsing errors, the original parser statement and the actual compiler-input line are shown in the log and error dialog when available. `repr` exposes hidden characters. Successful parser behavior is unchanged.

## Reproduction steps

Run Stage 414 from the extracted folder, open the program with line 98, click Compile, inspect `C64 BASIC COMPILER` and `C64 BASIC INPUT`, and—if it fails—copy the parser-error and failing-line diagnostics along with the dialog.

## Regression tests

The Stage-414/413/411/410 test suite passed 26 tests, and source syntax was checked. Windows/PyQt5 runtime behavior still needs confirmation.
