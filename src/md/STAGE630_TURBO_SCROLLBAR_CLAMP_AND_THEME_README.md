# Stage 630 – Scrollbar-Grenzen und gemeinsamer grauer DOS-Stil

Verbindliche Grundlage: `d64_dism_stage629.zip`.

## Problem

In Stage 629 wurden die Qt5-Scrollleisten von `QStyleSheetStyle` layoutet. Gleichzeitig
zeichnete `D64TurboArrowScrollBar::paintEvent` die Pfeile nachträglich. Die von
Qt ermittelte Slider-Geometrie konnte dadurch über den oberen/unteren bzw.
linken/rechten Pfeilbereich ragen. Ein nur optisches Übermalen der Endfelder
beseitigt nicht die abweichende Maushitbox.

## Umsetzung

- `d64qt5/d64_turbo_scroll_geometry.hpp`: gemeinsame, eigenständige
  Intervallrechnung für beide Scrollrichtungen (halb offene Intervalle).
  Pfeile `[0, B)` und `[L-B, L)`; Laufbahn `[B, L-B)`; Slider vollständig
  in dieser Laufbahn. Auch bei kurzer Laufbahn, großen Bereichen und
  Endpositionen bleibt der Slider begrenzt.
- `d64qt5/d64_turbo_scrollbar.hpp`: zeichnet und bedient Pfeile, punktierte
  Laufbahn und Thumb mit **derselben** Geometrie. Kein `subControlRect`
  oder nachträglich überlagerter nativer Thumb mehr. Native QScrollBar-Ranges,
  Value-Signale, Tastatur und Mausrad bleiben; die Pfeil- und Bahnsteuerung
  sowie das Ziehen des Thumbs verwenden dieselbe feste Geometrie.
- `d64qt5/d64_turbo_editor.hpp`: vertikale und horizontale Scrollleisten
  verwenden dieselbe `setTurboEditorTheme()`-Konfiguration:
  vollblauer Pfeilhintergrund `#0000AA`, gelbe Pfeile und Umrandung,
  dunkelgrauer Thumb `#686868` mit Kanten, dunkelblaue punktierte
  Laufbahn `#000080` / `#9999AD`.
- Das grüne Ausgabefenster verwendet die neue korrekte Geometrie, behält
  jedoch seine grüne Farbpalette. Die Editor-/VFS-/Fensterlogik ist nicht
  verändert.

## Test

`python -m pytest -q test_stage628.py test_stage629.py test_stage630.py`

`test_stage630.py` kompiliert einen echten C++-Grenzwerttest für die Geometrie
mit `g++` und prüft tausende Kombinationen einschließlich beider Slider-
Endpositionen. Der vollständige Qt5-/MinGW32-Lauf wurde in der
Linux-Entwicklungsumgebung nicht durchgeführt.

## Windows: DLL bauen und installieren

1. Alle laufenden dBASE-EXE-Programme beenden.
2. `build_and_deploy_dbase_editor_stage630.bat` im Projektverzeichnis ausführen.
3. dBASE-EXE erneut starten und Vertikal-/Horizontal-Scrolling prüfen.

Für diese reine GUI-Erweiterung muss die bestehende dBASE-EXE nicht neu
kompiliert werden.
