[Deutsch](STAGE402_C64_VICE_SPRITE_LOAD_BEIDE_STARTWEGE.md) | [English](STAGE402_C64_VICE_SPRITE_LOAD_BEIDE_STARTWEGE.en.md)

# Stage 402 – Loading Raw Sprite Files in Both BASIC-to-VICE Launch Paths

**Basis:** `d64_dism_asm_401.zip`.

## Background

Both the VICE BASIC V2 interpreter and the compiled Stage-401 `LOAD "sprites.spr",8,1` use C64 drive semantics. A host file next to the source is not automatically a drive file, and raw `.spr` files have no two-byte PRG header.

## Implementation

The new `c64_vice_assets.py` detects literal `LOAD "*.spr",8,1` or `LOAD "*.sprite",8,1`. It looks next to the BASIC source, in the build directory, and among referenced project sprites. Raw 63/64-byte sprites are aligned to 64-byte records, prefixed with the little-endian `$3000` load address (`00 30`), and copied under the requested name into a dedicated temporary drive-8 staging directory. Original files are not modified. Missing or invalid source data yield diagnostics before starting VICE.

For the BASIC editor context menu, a new VICE process receives `-fs8`, `-devicebackend8 1`, and `-busdevice8`; an existing binary monitor receives Resource Set (`0x52`) requests for `FSDevice8Dir`/`FileSystemDevice8`. The compiled BASIC→VICE start uses the same preparation. The original BASIC statement and Stage-401 KERNAL LOAD implementation remain unchanged; actual loading occurs at runtime.

## Constraints

Only literal drive-8, secondary-address-1 raw sprite loads are staged. Dynamic filenames and files already inside a `.d64` are not rewritten. A mounted D64 can take precedence over the virtual host directory; in that case unmount or restart. The sprite destination at `$3000` must be free; programs must configure sprite pointers and colors. This helper is VICE-specific; actual hardware requires a PRG on physical disk. VICE version/settings may alter behavior, and no end-to-end VICE run was performed.

## Tests

`test_stage402_c64_vice_sprites.py` checks detection, comments, padding, header, case-insensitive lookup, bad input, both launch routes, and Remote Monitor Resource Set encoding. Stage-401 and other sprite/VICE regressions plus syntax checks were also run.
