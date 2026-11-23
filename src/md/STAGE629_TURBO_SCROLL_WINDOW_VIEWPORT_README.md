# Stage 629 – Turbo-Vision-Scrollleisten und Fenster-/Viewport-Verhalten

**Verbindliche Basis:** `d64_dism_stage628.zip`.

## Änderungen

### 1. Blaue Editor-Scrollleisten

- Der horizontale Scrollbalken verwendet nun dieselbe gelbe Thumb- und Konturfarbe wie der vertikale Scrollbalken.
- Beide Scrollbalken reservieren für die Pfeilflächen feste 15-Pixel-Endbereiche per Qt-Stylesheet-Margin. Der normale Thumb läuft nur in der Rille zwischen den Pfeilen.
- `D64TurboArrowScrollBar::paintEvent()` ermittelt die beiden echten Qt-Subcontrol-Rechtecke (`SC_ScrollBarSubLine` und `SC_ScrollBarAddLine`) und zeichnet die Pfeile **innerhalb dieser Rechtecke** statt über den ganzen Scrollbalken.
- Die Pfeil-Hintergründe sind vollflächig im Editor-Blau `#0000aa`, die gelben Dreiecke bleiben sichtbar. Die Rille bleibt dunkelblau und der Thumb gelb.
- Die vertikale und horizontale Scrollfunktion, Textcursor-Positionsanzeige und Größenmarkierung rechts unten bleiben erhalten.

### 2. Grünes Ausgabefenster

- Auch dessen beide Scrollleisten verwenden nun reservierte Endfelder, sodass der Thumb nicht über die Pfeilschaltflächen gleiten soll.
- Die Styles gelten sowohl im Standardzustand als auch nach der vorhandenen Hintergrund-Füllfunktion.

### 3. Verschieben außerhalb des 80×25-Viewports

- Die Editoren werden beim Verschieben und Vergrößern **nicht mehr auf die Restfläche des Parent-Viewports verkleinert**. Herausstehende Fensterteile werden durch den Qt-Viewport geclippt.
- Die linke Titelleistenregion bleibt erreichbar: Für einen 80-Spalten-Viewport dürfen Fenster links bis zu Spalte 70 beginnen; damit bleiben zehn Spalten der linken Titelregion zugänglich. Bei anderen Zoom-/Viewportgrößen wird der Grenzwert dynamisch angepasst.
- Die obere Fensterecke darf bis zur **DOS-Reihe 24** (nullbasiert, in einem 25-Zeilen-Viewport) bewegt werden. Damit bleibt ein Teil der Titelleiste sichtbar, der Fensterinhalt darf unten weiter herausragen.
- Der Zustand beim Maximieren/Wiederherstellen sowie das Zeichenraster werden erhalten.

### 4. Vordergrund und Fokus

- Ein linker Mausklick auf die Titelleiste hebt das entsprechende Editorfenster über seine Geschwister (`raise()`), markiert es als aktiven Editor für die Menüaktionen und setzt den Texteingabefokus.
- Bei Klicks auf eine frei gezeichnete Stelle der Titelleiste verhält sich das Fenster ebenso wie beim Klick auf die Titelbeschriftung.
- Das grüne Ausgabefenster wird beim Klicken auf seine Titelleiste ebenfalls in den Vordergrund geholt (auch maximiert).

## Betroffene Dateien

- `d64qt5/d64_turbo_editor.hpp`
- `d64qt5/d64_turbo_output.hpp`
- `d64qt5/d64_turbo_scrollbar.hpp`
- `test_stage629.py` (neu)
- `build_and_deploy_dbase_editor_stage629.bat` (neu)

Die Compiler-, Linker-, VFS- und Dateimenü-Implementierungen bleiben unverändert.

## Windows-Build

Alle betroffenen Programme vor einem DLL-Austausch beenden und im entpackten Projektordner ausführen:

```bat
build_and_deploy_dbase_editor_stage629.bat
```

Optional lässt sich ein abweichendes Zielverzeichnis übergeben:

```bat
build_and_deploy_dbase_editor_stage629.bat "C:\\pfad\\zur\\runtime\\dbase\\pe32"
```

Das Skript baut `libd64_qt5.dll` mit der vorhandenen MinGW32-/Qt5-Toolchain und kopiert sie nach `runtime\dbase\pe32`. Eine bereits mit Stage 628 gelinkte dBASE-EXE muss für diese reine GUI-Änderung nicht erneut gelinkt werden.

## Tests und offene Prüfung

- `pytest -q test_stage620.py test_stage621.py test_stage622.py test_stage628.py test_stage629.py`
- Ergebnis: **63 Tests erfolgreich** (statische Integrations-, Compiler- und Regressionsprüfungen).
- Vollständiges ZIP wird separat auf Integrität geprüft.
- Die **native Qt5-/MinGW32-Kompilierung und visuelle Maus-/Scrollprüfung** unter Windows konnten in dieser Linux-Umgebung nicht ausgeführt werden. Insbesondere sollte die tatsächliche Scrollbar-Zeichnung mit der dort installierten Qt5-Version überprüft werden.
