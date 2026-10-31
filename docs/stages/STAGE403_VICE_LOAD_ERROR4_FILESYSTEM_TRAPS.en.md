[Deutsch](STAGE403_VICE_LOAD_ERROR4_FILESYSTEM_TRAPS.md) | [English](STAGE403_VICE_LOAD_ERROR4_FILESYSTEM_TRAPS.en.md)

# Stage 403 – VICE LOAD ERROR 4 (File Not Found)

**Basis:** `d64_dism_asm_402.zip`.

## Diagnosis

KERNAL `?LOAD ERROR 4` means **file not found**. Stage 402 configured host filesystem drive 8, but enabled `-busdevice8` / `BusDevice8` instead of the KERNAL traps required to load from a host directory.

## Correction

For a new VICE process, use `-fs8 <staging-path>`, `-devicebackend8 1`, `+drive8truedrive`, `+fs8hidecbm`, and either `-trapdevice8` (VICE 3.10+) or `-virtualdev8` (older VICE). The available option is selected by examining and caching `VICE -help` output.

For an existing VICE session, the binary monitor sets `FSDevice8Dir`, `FileSystemDevice8=1`, `FSDevice8HideCBMFiles=0`, `Drive8TrueEmulation=0`, and either `TrapDevice8=1` or fallback `VirtualDevice8=1`. If both trap resources fail, an error is shown instead of silently choosing the wrong bus configuration.

Both BASIC→VICE routes and the Stage-402 `$3000` sprite preparation are retained. Neither actual drive data nor D64 disk images are changed.

## Remaining limitations and tests

An already mounted D64 or manually overridden VICE configuration can still interfere. For older VICE builds without usable `-help`, `-trapdevice8` is the fallback and may require local verification. Tests validate options and monitor commands, not actual C64 loading; VICE was unavailable.

```cmd
python -m unittest -v test_stage403_vice_load_error4.py test_stage402_c64_vice_sprites.py test_stage401_c64_basic_load.py
```

All 24 targeted tests passed; Python syntax was verified.
