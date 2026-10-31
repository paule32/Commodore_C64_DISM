[Deutsch](STAGE454_FLD1_UND_DLL_PACKER_STATUS.md) | [English](STAGE454_FLD1_UND_DLL_PACKER_STATUS.en.md)

# Stage 454 – FLD1 in the Internal PE32 and PE32+ Assemblers

Repairs `fld1`, the x87 instruction that loads floating-point constant 1.0. The correct machine bytes are **`D9 E8`** and the instruction length is two bytes in PE32 and PE32+; `fldz` (`D9 EE`) is unchanged. The fix adjusts size calculation and byte encoding so later instructions, references, and symbols have correct offsets. The accompanying notes explicitly do **not** claim that an independent or unverified DLL packer has been implemented. Tests cover emitted opcodes and layout.
