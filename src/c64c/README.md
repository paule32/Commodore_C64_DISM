# C64 C

Die Pipeline besteht aus zwei Stufen:

1. `C64CLexer.g4` und `C64CParser.g4` parsen C mit ANTLR 4.13.2.
2. `compiler.py` erzeugt lesbaren MOS-6510-Assembler. Der in
   `d64_dism(5).py` integrierte Assembler erzeugt daraus das C64-PRG.

## Installation

```powershell
py -m pip install antlr4-python3-runtime==4.13.2
```

Die Ordner `c64c` und `c64pascal` muessen neben `d64_dism(5).py` liegen. Das
C-Frontend verwendet das gemeinsame 16-Bit-C64-Backend aus `c64pascal`.

## Aktueller Sprachumfang

- rekursive `#include "..."`- und `#include <...>`-Verarbeitung
- objektartige und funktionsartige `#define`-Makros
- verschachtelte `#ifdef`, `#ifndef`, `#else` und `#endif`
- `#undef`, `#pragma once`, `#note`, `#warning` und `#error`
- `__FILE__` und `__LINE__`
- skalare `typedef`-Aliase, flache `typedef struct`-Datensaetze und `.`-Zugriffe
- Funktionsprototypen einschliesslich Zeigern und `...`
- `int main(void)` und `void main(void)`
- globale und lokale `int`-, `char`-, `unsigned char`- und `bool`-Variablen
- `const`, Initialisierungen und Ganzzahlausdruecke
- `+`, `-`, `*`, `/`, `%`, `&`, `|`, `^`, `!`, `~`, `&&`, `||`
- `==`, `!=`, `<`, `<=`, `>`, `>=`
- `if/else`, `while`, `do/while` und kanonische `for`-Schleifen
- `break`, `continue`, `return`, `++`, `--` und kombinierte Zuweisungen
- `printf` mit `%d`, `%i`, `%u`, `%c`, `%s` und `%%`
- `puts`, `putchar`, `clrscr`, `poke`, `peek`, `lo`, `hi` und `halt`
- gleichwertige `c64_...`-Namen wie `c64_poke` und `c64_clrscr`
- Dezimal-, Hex- (`0x`) und Binärliterale (`0b`)

## Includes und Suchpfade

Bei `#include "datei.h"` wird zuerst relativ zur einbindenden Datei gesucht.
Danach folgen die vom Aufrufer angegebenen Include-Pfade und der mitgelieferte
Ordner `c64c/include`. Bei `<datei.h>` werden zuerst die Include-Pfade und die
mitgelieferten Header durchsucht. In der Anwendung kommen ausserdem das
aktuelle Arbeitsverzeichnis und das Projektverzeichnis hinzu.

Mitgeliefert werden `stdbool.h`, `stdint.h`, `stddef.h`, `stdio.h` und `c64.h`.
Eine nicht vorhandene oder nicht lesbare Datei beendet die Kompilierung mit
Datei, Zeile, Include-Kette und den geprueften Suchpfaden.

Beispiel:

```c
#include <stdint.h>
#include <stdio.h>
#include <c64.h>

#define COUNT 26
#define SCREEN_CELL(i) (C64_SCREEN + (i))

typedef struct Cursor {
    uint8_t x;
    uint8_t y;
} Cursor;

int main(void)
{
    Cursor cursor;
    cursor.x = 0;
    cursor.y = 0;
    poke(SCREEN_CELL(cursor.x), 1);
    printf("A");
    return 0;
}
```

`int` und Zeiger sind 16 Bit breit. Division und Modulo arbeiten in dieser
Stufe vorzeichenlos. Flache Strukturen mit skalaren Feldern sind verwendbar.
Verschachtelte Strukturen, Arrays, Zeigerdereferenzierung und die
Codeerzeugung fuer benutzerdefinierte Funktionen folgen spaeter. Deren
Prototypen duerfen bereits in Headern stehen. Makro-Stringisierung (`#`) und
Token-Verkettung (`##`) werden noch nicht unterstuetzt.

## Parser neu erzeugen

```powershell
py c64c\generate_parser.py T:\Tools\antlr-4.13.2-complete.jar
```
