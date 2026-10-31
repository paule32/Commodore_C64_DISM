[Deutsch](STAGE445_PE32_BYTE_ASSEMBLER_STRING_TRIM.md) | [English](STAGE445_PE32_BYTE_ASSEMBLER_STRING_TRIM.en.md)

# Stage 445 – Internal PE32 Assembler: Eight-Bit Memory Instructions

Corrects missing or incorrect encoding support for eight-bit register/memory operations required by the native runtime. Supported encodings include `MOV r8, BYTE PTR [base(+disp)]` (`8A /r`), `CMP AL, imm8` (`3C ib`), other 8-bit-register comparisons (`80 /7 ib`), and `MOV BYTE PTR [base(+disp)], imm8` (`C6 /0 ib`). Instruction size calculations, symbol offsets, displacements, and relocations are updated consistently. Invalid register/operand widths or nonrepresentable byte immediates produce explicit errors. Regression tests compare generated machine bytes and offsets rather than source strings alone.

## Source code and command examples (unchanged)

```asm
mov al, byte ptr [esi]
cmp al, 32
mov byte ptr [edi], 0
```

