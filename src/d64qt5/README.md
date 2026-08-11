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
