[Deutsch](STAGE412_VICE_D64_AUTOSTART_PETSCII.md) | [English](STAGE412_VICE_D64_AUTOSTART_PETSCII.en.md)

# Stage 412 – D64 Autostart without Host Filename Conversion

**Basis:** `d64_dism_asm_411.zip`.

## Trigger

The user's VICE screenshot showed an immediate BASIC `LOAD "<graphic characters>",8,1` followed by `?FILE NOT FOUND ERROR`, `RUN`, and `READY.`. This happened during **VICE autostart of the compiled PRG**, before the program's own `LOAD "sprites.spr",8,1` had executed.

Stage 411 used `-autostart <image>.d64:SPRITE_A`. VICE converts that ASCII command argument to PETSCII, producing a mismatch with the filename bytes taken directly from the D64 directory.

## Fix

- `d64_dism.py` now obtains launch arguments from `c64_vice_d64_autostart_options(sprite_disk)` in `c64_d64_disk.py`.
- VICE launches using `x64sc ... -8 <absolute-image>.d64 -autostart <absolute-image>.d64`, **without** a `:SPRITE_A` suffix.
- The D64 writer already places the executable PRG in the first directory entry, with `SPRITES.SPR` second; autostart selects the first program.
- Generated PRG alias names in the disk image use PETSCII-safe names: an underscore `_` is changed to `-`, since PETSCII `$5F` denotes a left arrow.
- The BASIC direct/debug transfer still attaches the D64 with `-8` and sends BASIC lines separately through the Binary Monitor.

## Verification

The directory order and file bytes are compared with the generated program and staged sprite. Manual VICE verification should mount drive 8 and run `LOAD "*",8,1` followed by `RUN`. Actual VICE execution on Windows was not available. This fix targets the autostart filename issue, not an unproven new diagnosis of the program's own sprite LOAD.
