# PE64 Register-/COFF64-Symbol Fix

## Problem

Beim Assemblieren von Windows-PE64-Code konnte z. B. folgende Meldung erscheinen:

```
COFF64-Symbol fehlt: rdx
```

Die Ursache war die Reihenfolge der Operandenerkennung im internen AMD64-Assembler.
AMD64-Registernamen wie `rdx` sind lexikalisch ebenfalls gültige Bezeichner. Bei
`call rdx` bzw. `jmp rdx` wurde deshalb zuerst die generische Symbolprüfung
getroffen und fälschlich eine `IMAGE_REL_AMD64_REL32`-Relocation auf das
angebliche COFF64-Symbol `rdx` erzeugt.

Der PE64-Exception-Unwinder verwendet insbesondere `jmp rdx`, weshalb der Fehler
auch bei von Pascal erzeugtem PE64-Code auftreten konnte.

## Korrektur

- Register- und Speicheroperanden werden bei `CALL`/`JMP` vor generischen
  Symbolen erkannt.
- `_x64_is_symbol()` schließt sämtliche bekannten AMD64-Register explizit aus:
  64-, 32-, 16- und 8-Bit-Register sowie `rip`.
- Indirekte Registeraufrufe/-sprünge erzeugen keine COFF64-Relocation.

Beispiele:

```
call rdx   ; FF D2
jmp  rdx   ; FF E2
jmp  r11   ; 41 FF E3
```

## Regressionstest

`tests/test_pe64_internal.py` prüft nun:

- `call rdx`
- `jmp rdx`
- `jmp r11`
- keine Relocation auf Register
- keine Registererkennung als COFF64-Symbol
- weiterhin korrekte Erkennung normaler Symbole/Labels
