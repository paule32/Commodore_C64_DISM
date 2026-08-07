# C64-/Amiga-C

Die Pipeline besteht aus zwei Stufen:

1. `C64CLexer.g4` und `C64CParser.g4` parsen C mit ANTLR 4.13.2.
2. `compiler.py` erzeugt je nach Ziel lesbaren MOS-6510- oder
   Motorola-68000-Assembler. Die internen Assembler erzeugen daraus ein
   C64-PRG beziehungsweise ein eigenständig bootfähiges Amiga-ADF.

## Installation

```powershell
py -m pip install antlr4-python3-runtime==4.13.2
```

Die Ordner `c64c` und `c64pascal` muessen neben `d64_dism.py` liegen. Beide
Frontends verwenden kompatible AST-Datentypen; anschließend wählen C64 und
Amiga jedoch getrennte Codegeneratoren und vollständig getrennte Laufzeiten.

In der Oberfläche wird das Ziel mit den RadioButtons `C-64` und `Amiga`
gewählt. Die Python-Schnittstelle verwendet entsprechend
`compile_c_to_assembly(..., target="c64")` oder `target="amiga"`.

## Aktueller Sprachumfang

- rekursive `#include "..."`- und `#include <...>`-Verarbeitung
- objektartige und funktionsartige `#define`-Makros
- verschachtelte `#if`, `#ifdef`, `#ifndef`, `#elif`, `#else` und `#endif`
- Makroausdrücke in `#if` mit `==`, `!=`, `>=`, `<=`, `<`, `>`,
  `defined(...)`, `&&`, `||` und arithmetischen Operatoren
- Stringisierung (`#parameter`) und Token-Verkettung (`##`)
- `#undef`, `#pragma once`, `#pragma link`, `#pragma d64_link_asm`,
  `#note`/`#info`, `#warn`/`#warning` und `#error`
- `__FILE__` und `__LINE__`
- skalare `typedef`-Aliase, `enum`, 16-Bit-`set`-Typen sowie getaggte und per `typedef struct` definierte Strukturen
- Funktionsprototypen einschliesslich Zeigern und `...`
- `int main(void)` und `void main(void)`
- getrennte C-Funktionsdefinitionen über `#pragma link "module.c"`
- rekursionsfeste skalare Wertparameter und Rückgabewerte für normale C-Funktionen
- modulinterne `static`-Funktionen
- globale, automatische lokale und persistente lokale `static`-Variablen
- lexikalische Block-Scopes mit Shadowing sowie `const`, Initialisierungen und Ganzzahlausdruecke
- `+`, `-`, `*`, `/`, `%`, `&`, `|`, `^`, `!`, `~`, `&&`, `||`
- `==`, `!=`, `<`, `<=`, `>`, `>=`
- `if/else`, `while`, `do/while` und kanonische `for`-Schleifen
- `break`, `continue`, `return`, `++`, `--` und kombinierte Zuweisungen
- `printf` mit `%d`, `%i`, `%u`, `%c`, `%s` und `%%`
- `puts`, `putchar`, `clrscr`, `amiga_set_text_color`, `poke`, `peek`, `lo`,
  `hi` und `halt`
- gleichwertige `c64_...`-Namen wie `c64_poke` und `c64_clrscr`
- Dezimal-, Hex- (`0x`) und Binärliterale (`0b`)

## Includes und Suchpfade

Bei `#include "datei.h"` wird zuerst relativ zur einbindenden Datei gesucht.
Danach folgen die vom Aufrufer angegebenen Include-Pfade und der mitgelieferte
Ordner `c64c/include`. Bei `<datei.h>` werden zuerst die Include-Pfade und die
mitgelieferten Header durchsucht. In der Anwendung kommen ausserdem das
aktuelle Arbeitsverzeichnis und das Projektverzeichnis hinzu.

Mitgeliefert werden `stdbool.h`, `stdint.h`, `stddef.h`, `stdio.h`, `c64.h`
und `amiga.h`. Für 16-Bit-Mengen kommen `set.h` und das getrennt kompilierte `runtime/set_runtime.c` hinzu.
Eine nicht vorhandene oder nicht lesbare Datei beendet die Kompilierung mit
Datei, Zeile, Include-Kette und den geprueften Suchpfaden.
Klassische Include-Guards mit `#ifndef`/`#define` verhindern auch direkte und
indirekte Selbst-Includes. Der rekursive Guard-Block wird vollständig inaktiv
bis zu seinem `#endif`; ein Include-Zyklus ohne wirksamen Guard wird unmittelbar
mit der Include-Kette gemeldet.

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
Funktionsprototypen aus Headern werden als normale externe Symbole aufgerufen.
Ein Header kann getrennte C- oder ASM-Module anfordern:

```c
#pragma link "../runtime/algorithms.c"
#pragma d64_link_asm "../runtime/hardware.amiga.asm"
```

Jede mit `#pragma link` angeforderte `.c`-Datei wird als eigene Translation Unit
präprozessiert, geparst und in ein eigenes ASM-Modul übersetzt. Anschließend
werden Hauptprogramm, C-Module und ASM-Module statisch zusammengeführt. Der
Aufruf bleibt ein normaler `bsr`/`jsr`; es werden keine Intrinsics erzeugt.

Parameter und automatische lokale Variablen liegen in echten Funktions-
Stackframes. Reguläre Funktionen sind damit reentrant und rekursionsfest.
Explizit als `static` deklarierte lokale Variablen liegen dagegen im globalen
Datensegment und behalten ihren Wert zwischen Aufrufen. Jeder `{ ... }`-Block
bildet einen lexikalischen Scope; gleichnamige innere Variablen werden getrennt
verwaltet. Enums, Set-Typen, getaggte Strukturen und `typedef struct` sind
ebenfalls verfügbar. Details und Beispiele stehen in
`C_ADVANCED_FEATURES.md`.

Beim Amiga-Ziel schreiben `printf`, `puts` und `putchar` die Zeichen über den
eingebetteten 8x8-Bitmapfont direkt in eine OCS-Bitplane. Mit
`amiga_set_text_color(vorne, hinten)` werden `COLOR01` und `COLOR00` gesetzt;
die Werte verwenden das 12-Bit-Format `0xRGB`. Es werden keine Workbench-,
DOS- oder Graphics-Libraries aufgerufen. `peek`, `poke` und die
gleichwertigen `c64_...`-Namen bleiben C64-spezifisch und werden beim
Amiga-Ziel mit einer klaren Diagnose abgelehnt.

## Parser neu erzeugen

```powershell
py c64c\generate_parser.py T:\Tools\antlr-4.13.2-complete.jar
```
