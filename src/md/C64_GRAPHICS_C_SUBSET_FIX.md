# C64 Pascal Graphics: C-Untermodul-Korrektur

## Fehler

Beim Kompilieren einer Pascal-Datei mit `uses System.Graphics` im C64-Ziel
wurde die getrennte C-Implementierung abgebrochen:

```text
graphics_target.c:16:35: mismatched input '(' expecting ';'
```

Die betreffende Quellzeile enthielt einen skalaren C-Cast:

```c
C64TextColor = (GraphicsColor)(foreground & 15u);
```

## Ursache

Die C-Frontend-Absenkung fuer skalare Casts befand sich versehentlich hinter
einem Fruehausstieg fuer Translation Units ohne Array-Deklaration. Da
`graphics_target.c` keine eigenen C-Arrays deklarierte, wurde der Cast nicht
entfernt und gelangte in die aeltere ANTLR-Grammar, die Cast-Ausdruecke noch
nicht direkt enthaelt.

Danach waeren in derselben Datei ausserdem die als Pointer-Makros formulierten
Bitmapzugriffe an `[...]` gescheitert.

## Korrektur

- skalare Cast- und Shift-Absenkung laeuft jetzt auch ohne Arrays;
- die C64-Hardwaredatei verwendet `peek()` und `poke()` statt Pointer-Casts;
- der schnelle horizontale Linienpfad bleibt erhalten;
- bedingte `?:`-Ausdruecke in den gemeinsamen Grafikalgorithmen wurden durch
  normale `if/else`-Anweisungen ersetzt;
- `System.Graphics` bleibt eine getrennt kompilierte Pascal-Unit mit PUI und
  separaten C-Translation-Units.

Es wurden keine Grafik-Intrinsics eingefuehrt.
