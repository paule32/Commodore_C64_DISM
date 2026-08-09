# PROLOG Fließkomma-Runtime für d64_dism

## Ziele

Der PROLOG-Compiler unterstützt jetzt IEEE-754 Double-Werte auf Windows PE32 und PE32+ (AMD64).
Die Assembler- und Link-Schritte erfolgen weiterhin vollständig über die internen Komponenten von `d64_dism`.

## Literale

Unterstützt werden unter anderem:

```prolog
0.33
-1.25
2.0
2e-3
1.25e+4
```

Ein Punkt gehört nur dann zu einem Float-Literal, wenn danach mindestens eine Ziffer folgt. Dadurch bleibt `1.` weiterhin der Integer-Term `1` plus PROLOG-Abschlusspunkt.

## Arithmetik

```prolog
?- X is 0.33.
?- X is 1/3.
?- X is 2 + 0.5.
?- X is 2.5 * 4.
?- X is 5.0 - 0.25.
```

Regeln:

- `+`, `-`, `*` liefern einen Integer, wenn beide Operanden Integer sind.
- Sobald ein Operand Float ist, liefern `+`, `-`, `*` einen Float.
- `/` liefert immer einen Float. `1/3` wird also nicht mehr ganzzahlig zu `0` abgeschnitten.
- `mod` bleibt eine Integer-Operation.
- Division durch Null schlägt weiterhin als arithmetischer Fehler/fehlgeschlagene Auswertung fehl.

## Runtime-Term

Ein Float ist ein eigener Termtyp `NODE_FLOAT`. Die 16-Byte-Termzelle speichert das IEEE-754-binary64-Bitmuster in den Bytes +4 bis +11.
Damit können Float-Werte wie andere PROLOG-Terme unifiziert, kopiert, über `assert/retract` gespeichert und durch die GC bewegt werden.

## Typprädikate

Neu:

```prolog
float(X).
number(X).
```

`integer(X)` akzeptiert nur Integer. `float(X)` akzeptiert nur Double. `number(X)` akzeptiert beide.

## Ausgabe

`write/1`, `writeln/1` und die normale Top-Level-Lösungsanzeige können Float-Terme ausgeben. Die Runtime verwendet dafür `_gcvt` aus `msvcrt.dll` mit 15 signifikanten Ziffern.

Beispiel:

```prolog
?- X is 1/3, writeln(X).
0.333333333333333
```

## Interaktiver Parser

Der Console-REPL erkennt Float-Literale zur Laufzeit. Die Token-Grenze wird vom eigenen PROLOG-Parser bestimmt; die reine Dezimal-zu-binary64-Konvertierung erfolgt anschließend über `strtod` aus `msvcrt.dll`.

## Interner Assembler

Für die Float-Runtime wurde der interne IA-32-/AMD64-Assembler um einen kleinen x87-Satz erweitert:

- `fld`
- `fild`
- `fstp`
- `faddp`
- `fsubp`
- `fmulp`
- `fdivp`
- `fchs`
- `fldz`
- `fucomip`

PE32+ unterstützt zusätzlich das für die Win64-C-Runtime-Rückgabe benötigte `movsd xmm0, qword ptr [...]` bzw. die Gegenrichtung.

## Beispiel

```prolog
main :-
    A is 0.33,
    writeln(A),
    B is 1/3,
    writeln(B),
    C is 2 + 0.5,
    writeln(C),
    repl.
```
