[Deutsch](STAGE413_C64_LOAD_SPRITE_HOST_MONITOR.md) | [English](STAGE413_C64_LOAD_SPRITE_HOST_MONITOR.en.md)

# Stage 413 – C64 BASIC LOAD SPRITE: Windows Host and VICE Binary Monitor

**Basis:** `d64_dism_asm_412.zip`; prior Stage-412 features remain.

## Two independent load mechanisms

- `LOAD "name.spr",8,1`: standard BASIC V2/KERNAL loading of a **disk PRG entry** called `NAME.SPR` from drive 8. Stages 409–412 can build a D64 with correctly named sprite assets.
- `LOAD SPRITE "name.spr"`: new **d64_dism-specific instruction** that reads a file beside the BASIC source on the Windows host and writes its bytes into C64 RAM at `$3000`. An alternative aligned address, such as `$3040`, may be specified in hexadecimal or decimal. No disk is required.

## Direct BASIC → VICE debugging

The Binary Remote Monitor v2 uses Memory Set to transfer sprite bitmap bytes before `RUN`. Since `LOAD SPRITE` is not a BASIC V2 command, the corresponding numbered line is sent as `REM LOAD SPRITE HOST`; an unnumbered single statement only transfers the data. The REM line **does not reload** host bytes when BASIC executes it again later. For repeatable disk-time loads, use standard `LOAD`.

## Compiled BASIC → ASM → PRG → VICE

At compile time, host sprite bytes are embedded in the PRG. Generated MOS6510 code calls `__basic_sprite_copy` when the BASIC line executes, writing them to the target address. This works without the host monitor or an inserted disk after compilation. Rebuild if the `.spr` file changes.

At `$3000`, sprite pointer 192 is used in VIC bank 0 (`POKE 2040,192`); at `$3040`, pointer 193 is used. VIC-II registers also need configuring; loading alone does not display the sprite.

## Supported data and safety

- Original raw data: 64 bytes per sprite; 63-byte records receive a zero padding byte.
- Prebuilt PRG data: two-byte address header plus sprites. The address must match the requested target; its header is **not copied into RAM**.
- Addresses must be 64-byte aligned and fit in the 64 KiB address space.
- The destination must be free in the active 16 KiB VIC bank and must not collide with executable code, embedded data, or CBSS. The runtime reserves no RAM automatically.

## Example: show sprite 0 in text mode

```basic
10 LOAD SPRITE "sprites.spr"
20 POKE 2040,192
30 POKE 53248,120
40 POKE 53249,100
50 POKE 53264,0
60 POKE 53276,0
70 POKE 53287,1
80 POKE 53269,1
90 END
```

To load from D64 instead, use `10 LOAD "sprites.spr",8,1` and verify the CBM directory entry.

## Tests

Stage-413 tests cover syntax, host lookup, 63/64-byte records, PRG header, embedded data, other addresses, independent disk LOAD, and binary monitor transfer. Stage-410/412 regressions, Python syntax, ZIP integrity, and assembly of a test PRG were checked. Visual execution in a real Windows/VICE environment was not tested.
