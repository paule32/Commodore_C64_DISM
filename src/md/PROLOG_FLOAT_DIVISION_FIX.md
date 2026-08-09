# PROLOG Float Division / Subtraction Fix

## Fehler

Die native x87-Runtime lud bei binärer Float-Arithmetik den rechten Operand vor dem linken Operand.
Bei den von d64_dism erzeugten no-operand Encodings gilt jedoch:

- `fsubp` = `ST1 := ST1 - ST0`, danach Pop
- `fdivp` = `ST1 := ST1 / ST0`, danach Pop

Dadurch wurde beispielsweise `1/2` als `2/1 = 2` berechnet.

## Korrektur

Die Runtime lädt jetzt den linken Operand zuerst und den rechten Operand danach:

```text
FLD left
FLD right
FDIVP        ; left / right
```

Damit gilt:

```prolog
?- X is 1/2.
X = 0.5.

?- X is 2/1.
X = 2.

?- X is 5.0 - 2.0.
X = 3.

?- X is 2.0 - 5.0.
X = -3.
```

Addition und Multiplikation bleiben unverändert korrekt.

## Prüfung

- 51 gemeinsame LISP/PROLOG Regressionstests: OK
- PE32: ASM -> COFF32 -> PE32 Console EXE: OK
- PE32+: AMD64 ASM -> COFF64 -> PE32+ Console EXE: OK
- Native x87 CPU-Smoke-Prüfung: `1.0 / 2.0 = 0.5`: OK
