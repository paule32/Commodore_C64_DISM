# C-Compiler: externe Grafikfunktionen

## Ursache des bisherigen Fehlers

Der Parser speicherte Funktionsprototypen aus `graphics.h`, aber
`_AstBuilder._call_statement()` und `_call_expression()` brachen bei jedem
Aufruf eines solchen Prototyps absichtlich ab.

## Neue Verarbeitung

Ein Prototyp wird jetzt als normale externe Routine mit folgenden Angaben in
die gemeinsame Zwischenform übernommen:

- Name
- Parameterzahl
- Parametertypen
- Rückgabetyp
- Linkersymbol

Für Amiga werden Wertparameter von links nach rechts als 16-Bit-Wörter auf den
68000-Stack gelegt. Der Rückgabewert einer Funktion liegt in `D0.W`.

Beispiel:

```c
SetPixel(10, 20, 5);
```

erzeugt sinngemäß:

```asm
move.w #10,-(sp)
move.w #20,-(sp)
move.w #5,-(sp)
bsr SetPixel
adda.w #6,sp
```

## Getrenntes Modul

`graphics.h` enthält für das Amiga-Ziel:

```c
#pragma d64_link_asm "../../runtime/graphics/amiga/graphics_amiga.asm"
```

Der Präprozessor löst den Pfad relativ zum Header auf. Der Compiler hängt das
Modul erst nach der C-Codeerzeugung statisch an. Das Modul wird vom normalen
Amiga-Assembler verarbeitet. Die Grafikfunktionen sind daher weder Intrinsics
noch fest im C-Codegenerator verdrahtet.

Das Modul exportiert sowohl Pascal- als auch C-Symbole, zum Beispiel:

```asm
xdef SetPixel
xdef __pas_System_Graphics_SetPixel

SetPixel:
__pas_System_Graphics_SetPixel:
    ; Implementierung
```

## Zielmakros

Der Compiler definiert automatisch genau eines der Makros:

```c
__D64_TARGET_C64__
__D64_TARGET_AMIGA__
```

Dadurch können Header zielabhängige Module auswählen.

## C-Quelldateien verlinken

Zusätzlich zu ASM-Modulen können nun reguläre C-Dateien eingebunden werden:

```c
#pragma link "graphics_algorithms.c"
```

Die referenzierte Datei wird separat präprozessiert und kompiliert. Öffentliche
Funktionen werden als normale C-Linkersymbole ausgegeben; `static`-Funktionen
erhalten modulbezogene interne Namen. Einzelheiten und Grenzen stehen in
`C_PRAGMA_LINK.md`.

Die hardwareabhängige Amiga-Grafikimplementierung bleibt derzeit als ASM-Modul
bestehen, weil sie direkte OCS-/Copper-Registerzugriffe verwendet. Gemeinsame
Algorithmen können schrittweise in getrennte `.c`-Module verschoben und mit
`#pragma link` eingebunden werden.
