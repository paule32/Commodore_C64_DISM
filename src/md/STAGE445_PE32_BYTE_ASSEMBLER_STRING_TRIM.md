# Stage 445 – Interner PE32-Assembler: 8-Bit-Speicherbefehle

**Verbindliche Basis:** `d64_dism_asm_444.zip`

## Fehlerursache

Der dBASE-Compiler erzeugt seit Stage 441 innerhalb der nativen LTRIM-/RTRIM-/TRIM-Routinen unter anderem:

```asm
mov al, byte ptr [esi]
cmp al, 32
mov byte ptr [edi], 0
```

Der interne PE32-Assembler unterstützte bislang weder den 8-Bit-Load in AL noch den 8-Bit-Vergleich mit unmittelbarem Wert oder `MOV r/m8, imm8` korrekt. Eine Änderung ausschließlich am Compiler hätte nur den ersten Fehler verdeckt.

## Korrektur

Die zwei Phasen des internen IA-32-Assemblers (Offset-/Labelberechnung und echte COFF-Byteausgabe) unterstützen jetzt:

- `MOV r8, BYTE PTR [base(+disp)]` → `8A /r`
- `CMP AL, imm8` → `3C ib`, für andere 8-Bit-Register `80 /7 ib`
- `MOV BYTE PTR [base(+disp)], imm8` → `C6 /0 ib`
- korrekte Instruktionsgrößen, Symbolverschiebungen und Relocations
- Fehler bei 8-Bit-Zielen mit abweichender Speicherbreite oder ungültiger 8-Bit-Konstante

Die dBASE-TRIM-Runtime wird nicht durch weniger aussagekräftige, alternative Assemblerbefehle ersetzt.

## Testnachweise

`test_stage445_pe32_byte_assembler.py` enthält Byte-für-Byte-Opcode-Tests, reale COFF-Assemblierung für alle drei TRIM-Generatorfunktionen sowie die Assemblierung vollständiger WFM-Event- und dBASE-PRG-Ausgaben.

**Verifizierte Tests:** 8 neue Stage-445-Tests, 34 Tests aus Stage 441–444, 70 Tests aus Stage 431–440; zusammen 112 bestanden.

**Einschränkung:** Das Starten einer erzeugten Windows-EXE wird in dieser Linux-Testumgebung nicht geprüft.
