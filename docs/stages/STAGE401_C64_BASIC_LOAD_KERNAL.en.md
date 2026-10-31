[Deutsch](STAGE401_C64_BASIC_LOAD_KERNAL.md) | [English](STAGE401_C64_BASIC_LOAD_KERNAL.en.md)

# Stage 401 – C64 BASIC V2: LOAD via KERNAL

**Basis:** `d64_dism_asm_400.zip` (no changes from unrelated branches).

## Fix

Previously, compiling `LOAD` produced the diagnostic `BASIC statement not supported: LOAD`; only the unrelated `LOAD SCREEN` extension was recognized. The `_BasicCompiler` now provides `compile_load()` and translates statements such as:

```basic
10 LOAD "SPRITES",8,1
```

into KERNAL calls to `SETNAM` (`$FFBD`), `SETLFS` (`$FFBA`), and `LOAD` (`$FFD5`). `A=0` means load rather than verify; with secondary address 0, `X/Y=$0801` is used. With secondary address 1, the load address comes from the PRG's first two bytes (for example `$3000`).

The compiler supports `LOAD "NAME"`, `LOAD "NAME",8`, `LOAD "NAME",8,1`, string expressions or variables for the filename, and numeric expressions for device and secondary address. KERNAL carry-set failures print `?LOAD ERROR <number>` and terminate the compiled program rather than continuing with missing data. `LOAD SCREEN` remains unchanged.

## C64/VICE requirements

A raw `.spr` file has **no PRG load header**, so the disk must contain a correctly prepared `SPRITES.PRG`. The VICE binary-monitor start still lets KERNAL read from drive 8 at runtime; no host file is embedded at compilation. The destination RAM region (such as `$3000`) must not collide with the program. Missing GOTO targets remain separate compiler errors. The BASIC context-menu **Execute** uses the interpreter and is distinct from compiled output.

## Tests

`python -m unittest -v test_stage401_c64_basic_load.py`: seven tests passed, covering syntax variants, default arguments, KERNAL sequences, multiple LOAD statements, assembly, error reporting, and unchanged `LOAD SCREEN`. Real VICE/hardware runtime was not tested.
