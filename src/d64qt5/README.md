# d64qt5.dll Qt5 C++ Bridge

Die dBase-EXE importiert nur die stabile C-ABI aus `d64qt5.dll`. Die Bridge
kapselt Qt5 Widgets und kann getrennt als PE32- oder PE32+-DLL gebaut werden.

Wichtig: `d64_dism.py` baut diese DLL beim Start **nicht** automatisch.

GUI-Struktur Stage 12:
- Kopfzeile mit Lupe + / Lupe - und `QTabBar`
- `Konsole` immer sichtbar
- `DEBUG` nur bei `SET DEBUG ON`
- `QStackedWidget` fuer die beiden Ausgabeseiten
- DEBUG-Seite mit `QPlainTextEdit` und `QLineEdit`

PE32: passende 32-Bit-Qt5-Toolchain verwenden.
PE32+: passende 64-Bit-Qt5-Toolchain verwenden.

## Stage 15

`DBaseQtSetColorNormal()` akzeptiert Windows-Systemfarbnamen sowie `#RRGGBB`.
`DBaseQtSetOutputColor()` setzt die Farben fuer nachfolgende dBase-`?`/`??`-Ausgaben.
Die SET-COLOR-Syntax verwendet `<Hintergrund>/<Vordergrund>`; `W/N` bedeutet
hellgrauer Hintergrund und schwarze Schrift.

## Stage 19: 80x25-Raster

Die Standardgroesse der dBase-Konsole wird aus den realen Fontmetriken fuer
80 Spalten und 25 Zeilen berechnet. Die Zoom-Lupen aendern die logische
Schriftgroesse um genau 1 pt. Falls Qt/Windows nach dem Layout durch
DPI-/Pixelrundung noch abweicht, darf die Textschrift separat um maximal
-1 bzw. +1 Pixel feinjustiert werden.

## Stage 23: CLEAR SCREEN Ausdruck

Zusatzexporte:

- `DBaseQtClearScreenChar(double code)` fuellt das 80x25-Konsolenraster mit einem CP437-Terminalzeichen und den aktuellen `SET COLOR TO`-Farben.
- `DBaseQtClearScreenColor(const char *name, int length)` leert die Konsole und setzt die Flaechenfarbe aus `#RRGGBB`.

Der bestehende Export `DBaseQtClearScreen(void)` bleibt unveraendert erhalten.

## Stage 24: Standardmenue und volle 80x25-Konsole

- Die Konsolen-Scrollbars sind permanent ausgeblendet (`Qt::ScrollBarAlwaysOff`).
- Es wird keine zusaetzliche Leerzeile mehr am unteren Rand reserviert.
- `DBaseQtEnsureDefaultMenu()` erzeugt bei leerem/nicht gesetztem `_app.menuFile` vor dem ersten Show das Standardmenue `=` und `Datei`.
- `Datei` enthaelt `Neu`, `Speichern`, `Speichern unter...`, `Alle Schließen`, Separator und `Beenden`.
- `Beenden` schliesst das Hauptfenster und beendet die Qt-Ereignisschleife.
- Der Datei-Popup behaelt den CP437/Terminal-Zeichenrahmen und die bisherigen Farben.

## Stage 25 – SESSION Login-Dialog

`new SESSION()` öffnet nun den rastergebundenen Windows-Login-Dialog. Der globale Status ist über `DBaseQtGetLoginSession()` verfügbar; solange kein Login besteht, bleiben im Menü nur Login und Beenden aktiv. Der Dialog skaliert mit den Lupen und lässt sich nur in ganzen 80×25-Zeichenzellen-Schritten innerhalb des Konsolenbereichs verschieben.

## Stage 26: Dialograster / CLEAR SCREEN-Zeichen bei Zoom

- Login-Dialog bewegt sich ausschliesslich im realen Konsolen-Viewport zwischen Menue und Statusbar.
- Der untere Dialograhmen darf bis an die letzte Textzeile direkt vor der Statusbar reichen; keine zusaetzliche Leerzeile wird reserviert.
- Dialogposition wird als Zeichenraster-Spalte/-Zeile gespeichert und beim Verschieben des Hauptfensters relativ zum Textbereich wiederhergestellt.
- Ein aktives `CLEAR SCREEN <Zeichen>`-Fuellmuster wird nach Lupen-Zoom mit gleichem CP437-Code und denselben Farben erneut erzeugt.
