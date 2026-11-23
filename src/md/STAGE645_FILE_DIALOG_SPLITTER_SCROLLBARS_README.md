# Stage 645 – Datei-Öffnen-Dialog: Sizer-Cursor und Pfeilscrollleisten

## Verbindliche Basis

`d64_dism_stage644.zip`. Alle bisherigen Funktionen aus Stage 644 bleiben erhalten, einschließlich der eingebetteten Datei-Dialogebene und des benutzerbezogenen virtuellen Dateisystems.

## Änderungen

### Größenänderungs-Cursor

- Der Trennbalken zwischen Verzeichnisliste und Dateiliste bekommt den horizontalen `Qt::SplitHCursor`.
- Die rechten Spaltengrenzen der Dateiansicht **Name / Datum / Größe** bekommen bei einem Abstand von höchstens fünf Pixeln ebenfalls `Qt::SplitHCursor`.
- Außerhalb dieser Trefferzonen bleibt der normale Pfeilcursor bestehen.
- Der Handcursor über tatsächlichen Datei-/Ordnereinträgen sowie den Aktionsbuttons bleibt unverändert.
- Um die zuvor im Stage-644-Konstruktor zurückgesetzten Cursor korrekt zu behandeln, werden die Sizer-Cursor explizit **nach** der allgemeinen Cursorinitialisierung gesetzt.

### Pfeile und Thumb-Grenzen

- Sowohl `QListWidget` (links) als auch `QTreeWidget` (rechts) verwenden nun horizontal und vertikal `D64TurboArrowScrollBar` aus Stage 630.
- Die Scrollleisten haben links/rechts bzw. oben/unten sichtbar gezeichnete Pfeile, ein dunkelgraues Thumb und eine gepunktete Laufbahn.
- Die 15-Pixel-Pfeilfelder bleiben vollständig von der Thumb-Laufbahn getrennt.
- Die gleiche exakte Geometrie berechnet Darstellung, Maushitbox und Scrollposition. Die Thumb-Zeichnung wird zusätzlich auf die zwischen den Pfeilen liegende Laufbahn beschnitten.
- Die Scrollleisten erscheinen wie zuvor, wenn die Inhalte den verfügbaren Platz überschreiten; Mausrad, Tastatur, Pfeilklick, Klick in die Laufbahn und Thumb-Ziehen verwenden weiterhin das Qt-Scrollmodell.

## Geänderte Dateien

- `d64qt5/d64_turbo_editor.hpp`: Dateidialog-Cursor, vier Scrollbars und Header-Hovererkennung.
- `test_stage630.py`: Erwartungswert für die zusätzlich hinzugekommenen Theme-Aufrufe aktualisiert; keine Änderung am ausführbaren Quellcode.
- Neu: `test_stage645.py`, diese Dokumentation und das Build-/Deploy-Skript.

## Build unter Windows / MinGW32

1. Laufende dBASE-EXE und andere Nutzer von `libd64_qt5.dll` schließen.
2. `build_and_deploy_dbase_editor_stage645.bat` aus dem Projektverzeichnis aufrufen.
3. Den Datei-Öffnen-Dialog öffnen, die Listengrößen mit dem Splitter und die Spaltenbreiten ändern, und beide Scrollrichtungen an den Anschlägen testen.

Die neue DLL wird standardmäßig nach `runtime\dbase\pe32` kopiert. Diese reine GUI-Änderung erfordert keine erneute Kompilierung der dBASE-EXE.

## Tests / Grenzen

- **126 automatisierte Tests bestanden**: Stage 628–637, 643–645 (ausgewählte Regressionen), darunter ein tatsächlich mit GCC kompiliertes Programm für Scroll-Geometrie und Endgrenzen.
- Archiv-Integrität und Dateiunterschiede gegenüber Stage 644 werden bei Auslieferung geprüft.
- Es wurde **kein** vollständiger Qt5-/MinGW32-Build und **kein** nativer Windows-GUI-Lauf durchgeführt. Darstellung und Interaktion müssen unter Windows verifiziert werden.
