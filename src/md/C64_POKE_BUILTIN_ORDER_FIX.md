# C64 `poke()` Builtin-Priorität

## Fehler

Ein C-Programm mit:

```c
#include <c64.h>

poke(0x0400 + i, 1 + i);
```

konnte im erzeugten 6510-Assembler enden mit:

```asm
jsr poke
```

Der interne Assembler meldete anschließend:

```text
Unbekanntes Symbol: poke
```

## Ursache

`c64.h` deklariert `poke()` absichtlich als normalen C-Prototyp, damit der
Frontend-Parser Anzahl und Typen der Argumente kennt. In der gemeinsamen
6510-Codeerzeugung wurde jedoch die Tabelle externer Routinen vor der direkten
Builtin-Absenkung geprüft.

Der C-Codegenerator erkannte `poke` bereits als Builtin, delegierte danach aber
an genau diese gemeinsame Routine. Dort gewann wieder der Header-Prototyp.

## Korrektur

Die direkten C64-Builtins werden nun vor der externen Symbolauflösung behandelt:

1. `write` / `writeln`
2. `clrscr`
3. `poke`
4. `inc` / `dec`
5. `halt`
6. echte externe Unit- oder C-Routinen

`poke(address, value)` erzeugt direkt einen indirekten 6510-Speicherzugriff:

```asm
lda value
ldy #$00
sta ($FB),y
```

Es wird kein Symbol `poke` benötigt und kein Runtime-Modul dafür gelinkt.

Die Aliasfunktion `c64_poke()` wird bereits im C-AST auf denselben internen
Builtin-Namen `poke` abgebildet und verwendet damit automatisch denselben Pfad.
