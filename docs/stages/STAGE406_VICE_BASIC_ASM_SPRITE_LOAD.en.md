[Deutsch](STAGE406_VICE_BASIC_ASM_SPRITE_LOAD.md) | [English](STAGE406_VICE_BASIC_ASM_SPRITE_LOAD.en.md)

# Stage 406 – Sprite LOAD from BASIC → Generated Assembly → VICE

**Basis:** `d64_dism_asm_405.zip`.

## Findings from user-provided files

`Sprite_A.bas` contains `50 LOAD "sprites.spr",8,1`. The generated assembly passes the eleven-character filename to KERNAL `SETNAM` (`$FFBD`), device 8 and secondary address 1 to `SETLFS` (`$FFBA`), and then calls `LOAD` (`$FFD5`). `Sprite_A.prg` loads at `$0801` and contains a SYS-2061 startup stub. KERNAL error 4 is **file not found**, not a MOS6510 assembler error.

The actual `sprites.spr` was not uploaded, so its availability, binary content, and VICE drive settings could not be confirmed.

## Corrected start path

The Stage-402 sprite staging was only invoked when the active editor document was BASIC. Starting an independently opened `*.generated.asm` therefore launched its PRG without attaching the related sprite file. Stage 406 connects the generated assembler/PRG path to the same dependency preparation as the BASIC path, so a source-generated executable can find its required asset on drive 8.

## Verification and constraints

The PRG header, KERNAL call sequence, host sprite asset detection, and separate BASIC and generated-ASM start paths must be tested together. This does not prove that every `LOAD ERROR 4` under arbitrary VICE configurations is fixed, and does not invent results for an absent sprite file.
