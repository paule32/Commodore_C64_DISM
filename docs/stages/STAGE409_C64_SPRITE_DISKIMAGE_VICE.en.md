[Deutsch](STAGE409_C64_SPRITE_DISKIMAGE_VICE.md) | [English](STAGE409_C64_SPRITE_DISKIMAGE_VICE.en.md)

# Stage 409 – Sprite Loading via a Real D64 Disk Image

**Basis:** `d64_dism_asm_408.zip`.

## Requested behavior

For BASIC such as `50 LOAD "sprites.spr",8,1`, d64_dism creates an actual 1541 D64 disk image **before launching the program**, inserts the referenced sprite file under the matching Commodore filename, and mounts that image as VICE drive 8. Subsequent BASIC loads use the same mounted disk.

## Implementation

The new `c64_d64_disk.py` writes a standard 35-track, 174,848-byte D64 image with a block availability map (BAM) at track 18/sector 0, a Commodore DOS 2A directory starting at track 18/sector 1, and linked file sectors containing 254 bytes of payload each.

Raw sprite bytes are turned into a valid PRG with a two-byte load address and placed in the D64 directory with the expected CBM name. The executable PRG is also included so VICE can boot/start it from the same disk. Disk metadata and sector chains must be consistent with 1541 conventions.

## Constraints and tests

Original host sprite files are preserved. The disk image is created for the target runtime and may need VICE drive settings adjusted. Unit tests should examine BAM, directory entries, sector links, PRG load addresses, and the VICE attach/start command; a real emulator boot remains a separate integration check.

## Source code and command examples (unchanged)

```text
0 "DBASE2MANY" D4 2A
6 "SPRITE_A" PRG
1 "SPRITES.SPR" PRG
...
```

