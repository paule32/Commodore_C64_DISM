# Direkte C64-Grafikprimitive

## Problem

Der VIC-II-HiRes-Modus und die Speicheraufteilung waren bereits korrekt, aber
mehrere komplexe Primitive wurden weiterhin aus
`runtime/graphics/common/graphics_api.c` durch den C64-C-Compiler in 6510-Code
übersetzt. Die dabei entstehende 16-Bit-Arithmetik und die vielen verschachtelten
Funktionsaufrufe führten zu falschen Koordinaten. Besonders betroffen waren
`FillRect`, `DrawCircle`, `FillCircle`, `FillTriangle` und
`DrawTriangleAngles`.

## Lösung

Für das C64-Ziel werden sämtliche öffentlichen Grafikprimitive nun direkt in
`runtime/graphics/c64/graphics_c64.asm` implementiert. Der Amiga verwendet
weiterhin sein getrenntes Motorola-68000-Modul. Die öffentliche C- und
Pascal-API bleibt unverändert.

Der C64-Block in `graphics.h` bindet nur noch das Assemblermodul ein:

```c
#if defined(__D64_TARGET_C64__) && !defined(D64_GRAPHICS_IMPLEMENTATION)
#pragma d64_link_asm "../../runtime/graphics/c64/graphics_c64.asm"
#endif
```

Die gemeinsame C-Datei `graphics_api.c` bleibt im Projekt erhalten, wird beim
C64-Grafikziel aber nicht mehr automatisch kompiliert.

## Direkte Routinen

Das 6510-Modul enthält nun direkte Implementierungen für:

- `DrawLine`
- `DrawRect`
- `FillRect`
- `DrawCircle`
- `FillCircle`
- `FloodFill`
- `DrawTriangle`
- `FillTriangle`
- `DrawTriangleAngles`

`DrawLine` verwendet eine 16-Bit-Bresenham-Variante. Rechtecke und gefüllte
Kreise verwenden horizontale Spannweiten. `FillTriangle` sortiert die Eckpunkte
nach Y und rastert beide Dreieckshälften zeilenweise. Dadurch entstehen keine
Lücken innerhalb der Füllung.

## Speicheraufteilung

```text
$080D-$3FFF  Hauptprogramm und normale C/Pascal-Runtime
$4000-$7FFF  direkte C64-Grafikroutinen
$8000-$BFFF  VIC-II-Bank 2
$8800-$8BE7  interne Zellfarbzuordnung
$8C00-$8FE7  HiRes-Screenmatrix
$9000-$92FF  FloodFill-Arbeitsstack im CPU-RAM
$A000-$BF3F  320x200-HiRes-Bitmap
```

Der Bereich `$9000-$9FFF` wird vom VIC-II in Bank 2 als Character-ROM gesehen.
Er eignet sich deshalb nicht für sichtbare Grafikdaten, kann aber als
CPU-Arbeitsspeicher für den FloodFill-Stack verwendet werden.

## C64-Farbgrenze

Der 320x200-HiRes-Modus besitzt pro 8x8-Zelle nur eine Vordergrund- und eine
Hintergrundfarbe. Die Geometrie der Primitive wird vollständig gezeichnet.
Treffen jedoch mehrere unterschiedliche Farben innerhalb derselben 8x8-Zelle
zusammen, kann der C64 nicht dieselbe unabhängige Pixelfarbigkeit wie der Amiga
darstellen. Das Zielmodul behält deshalb die erste Nicht-Hintergrundfarbe einer
Zelle bei. Diese Einschränkung betrifft die Farbe, nicht die Form oder Füllung.

## Superseded colour-cell strategy

The direct primitive geometry remains in use. The original HiRes
"first colour owns the cell" strategy has been superseded by
`C64_MULTICOLOR_PRIMITIVES_FIX.md`, because the shared demo requires more than
one non-background colour inside several 8x8 cells.
