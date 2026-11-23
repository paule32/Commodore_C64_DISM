# Stage 656 – Scrollleisten und Fensteraktivierung für Turbo Vision

Verbindliche Grundlage: `d64_dism_stage655.zip`.

## 1. Konsole ohne eigene Scrollleisten

In `d64qt5/d64qt5_bridge.cpp` verwenden nur die beiden Scrollbar-Policies
von `g_console` nun `Qt::ScrollBarAlwaysOff`. Das Konsolen-Dokument und seine
internen Scrollwerte bleiben verfügbar; es werden nur **keine Scrollbalken
am äußeren Konsolen-Hauptfenster** dargestellt. Die Scrollleisten der
untergeordneten Turbo-Vision-Fenster sind davon unabhängig.

## 2. Hilfe-Fenster aktivieren

`d64qt5/d64_turbo_help_window.hpp` hebt `D64TurboHelpWindow` per `raise()`
beim Linksklick auf die Titelleiste, Textansicht, deren Viewport, beide
Scrollleisten, Resize-Griff und freie Fensterfläche an. Klicks werden nicht
verschluckt, sodass Links, Maus-Drag, Resize und Scrollen weiter funktionieren.
Das Hilfe-Fenster bleibt ein Child-Widget von `g_console->viewport()`; es
wird weder in DEBUG verschoben noch als eigenes Host-EXE geöffnet.

## 3. Scrollleisten mit Pfeilen und begrenzter Thumb-Fahrt

Die Hilfe verwendet in **beiden Richtungen** die vorhandene Klasse
`D64TurboArrowScrollBar` aus `d64qt5/d64_turbo_scrollbar.hpp` mit einem
neuen cyanfarbenen Theme. Die Scrollbars sind unabhängig vom tatsächlichen
Scrollbedarf immer sichtbar (`Qt::ScrollBarAlwaysOn`). Pfeile lösen
`SliderSingleStepSub` bzw. `SliderSingleStepAdd` aus, Gedrückthalten
wiederholt diese Aktion. Der DEBUG-Tab verwendet dieselbe Klasse, aber
mit einem dunkelgrauen Theme; seine bislang helle Textfarbe bleibt.

Geometrie: `d64_turbo_scroll_geometry.hpp` trennt Anfangspfeil,
Scrollrille und Endpfeil. Es gilt für beide Richtungen:

```text
  [Pfeil zurück][Rille: Thumb bewegt sich nur hier][Pfeil vorwärts]
```

Die Half-Open-Grenzen `grooveStart`, `grooveEnd`, `thumbStart`, `thumbEnd`
werden sowohl beim Zeichnen als auch beim Dragging verwendet. Damit kann
der Thumb **nicht** über die obere/untere bzw. linke/rechte Kante der
Pfeilfelder hinausgeschoben werden. Ein Resize ändert die Berechnung
auf Basis der neuen Fenstergröße.

## Geänderte Dateien

- `d64qt5/d64qt5_bridge.cpp`: Konsole ohne Scrollleisten, DEBUG-Pfeilbars.
- `d64qt5/d64_turbo_help_window.hpp`: Klick-Aktivierung, eigene Pfeilbars.
- `d64qt5/d64_turbo_scrollbar.hpp`: Hilfe- und DEBUG-Themes (bestehende Geometrie).
- `test_stage655.py`: ab Stage 656 geänderte Konsolen-Erwartung.
- `test_stage654.py`: Test-Dummy an Stage-655-Projektnamen-Callback angepasst.
- `test_stage656.py`: neue Regressionstests für Scrollleisten/Fensteraktivierung.
- `build_and_deploy_dbase_editor_stage656.bat`: nur DLL-Build, kein Help-Host.

## Tests

- `test_stage651.py`, `test_stage652.py`, `test_stage653.py`,
  `test_stage629.py`, `test_stage630.py`, `test_stage631.py`,
  `test_stage654.py`, `test_stage655.py`, `test_stage656.py`:
  **73 bestanden**.
- Die Scrollbar-Grenzen wurden in nativen C++-Geometrietests mit `g++`
  geprüft; ein natives Windows-/Qt5-GUI-Build und ein interaktiver Test der
  Tastatureingabe/Mausfenster stehen noch aus (keine Qt5-Toolchain hier).

## Windows-Bridge neu bauen

```bat
build_and_deploy_dbase_editor_stage656.bat
```

Alternativ im selben Verzeichnis das bereits vorhandene
`build_and_deploy_dbase_editor_stage655.bat` verwenden; es baut ebenfalls
nur die DLL. Auf dem Zielsystem muss die aktualisierte `libd64_qt5.dll`
verwendet werden; dBASE-Quellen, `.thlp` und `.hlp` bleiben unverändert.
