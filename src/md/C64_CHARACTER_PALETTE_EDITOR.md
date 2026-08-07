# C64 Character- und Paletten-Editor

## Ausgabeformat im Character-Editor

Auf der rechten Seite des Character-Editors befindet sich die Gruppe
`Ausgabe Format` mit diesen RadioButtons:

- Assembler
- Pascal
- C
- BASIC

Der unmittelbar darunter liegende Button `Speichern als...` verwendet genau
das gewählte Format. Die vorgeschlagene Dateiendung wird automatisch gesetzt:

| Format | Dateiendung | Datenform |
|---|---:|---|
| Assembler | `.asm` | 256 Blöcke mit je acht `.byte`-Werten |
| Pascal | `.pas` | `array[0..255, 0..7] of Byte` |
| C | `.h` | `unsigned char [256][8]` |
| BASIC | `.bas` | `DIM CS(255,7)` und 256 `DATA`-Zeilen |

Die bestehenden Buttons zum binären Speichern bleiben erhalten. Ein binärer
Zeichensatz umfasst weiterhin 2048 Bytes. Der frühere Quellcodeexport verwendet
nun ebenfalls das in der rechten Gruppe gewählte Format.

## Paletten-Editor

Der neue Editor wird geöffnet über:

- `Werkzeuge -> C64 Paletten-Editor ...`
- `Strg+Alt+P`
- die neue Toolbar-Schaltfläche
- Doppelklick auf `.pal`- oder `.palette`-Dateien

Er zeigt alle 16 C64-Farben. Für jeden Eintrag können geändert werden:

- Farbname
- RGB-Wert als `#RRGGBB`
- Farbe über den Qt-Farbauswahldialog

Einzelne Farben oder die komplette Palette können auf die eingebaute
Standardpalette zurückgesetzt werden.

### Rohformat

Das Rohformat enthält 16 RGB-Tripel:

```text
16 Farben * 3 Bytes = 48 Bytes
```

Dateien werden als `.pal`, `.palette` oder `.bin` geladen. Beim Speichern wird
eine 48-Byte-Datei erzeugt.

### Quellcodeausgabe

Auch der Paletten-Editor besitzt die Gruppe `Ausgabe Format` mit Assembler,
Pascal, C und BASIC. Der Button `Speichern als...` exportiert die aktuelle
Palette entsprechend:

- Assembler: 16 `.byte R,G,B`-Zeilen
- Pascal: `array[0..15, 0..2] of Byte`
- C: `unsigned char [16][3]`
- BASIC: `DIM CP(15,2)` und 16 `DATA`-Zeilen

## Hardwarehinweis

Die 16 Farbnummern des VIC-II sind fest verdrahtet. Der Paletten-Editor ändert
nicht die elektrische Farberzeugung eines realen C64. Er bearbeitet die
RGB-Darstellung dieser Farbnummern für Vorschauen, Emulator-Konfigurationen,
Dokumentation und Quellcodeexport.

## Beispiele

Unter `examples/characters` befindet sich zusätzlich ein BASIC-Export des
Beispielzeichensatzes. Unter `examples/palettes` liegen die Standardpalette als
48-Byte-Datei sowie Exporte für alle vier Sprachen.

## Layout-Aenderung des Character-Editors

Der obere Quellcode-Button wurde entfernt. Die Gruppe `Ausgabe Format` befindet sich nun rechts neben dem Char-Grid direkt unter der Vorschau. Darunter liegt der Button `Quellcode speichern unter...`.
