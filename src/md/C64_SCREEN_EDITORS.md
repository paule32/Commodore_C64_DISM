# C64 Character-, Text- und Pixelbildschirm-Editoren

## Character-Editor

Der Character-Editor besitzt oberhalb des Zeichenrasters nur noch die Funktionen fuer die binaere Zeichensatzdatei:

- Neu
- Laden
- Speichern
- Speichern unter

Der fruehere obere Quellcode-Button wurde entfernt. Rechts neben dem 8x8-Char-Grid befinden sich unter der Vorschau:

- die Gruppe **Ausgabe Format**
- Assembler
- Pascal
- C
- BASIC
- der Button **Quellcode speichern unter...**

Die binaere Zeichensatzdatei bleibt 2048 Bytes gross. Die sprachabhaengige Ausgabe wird ausschliesslich ueber die rechte Ausgabegruppe gespeichert.

## Text-Bildschirm-Editor

Aufruf:

- `Werkzeuge -> C64 Text-Bildschirm-Editor ...`
- `Ctrl+Alt+T`
- Toolbar-Schaltflaeche
- Doppelklick auf `.scr` oder `.screen`

Die Bildschirmseite besteht aus:

- 40 Spalten
- 25 Zeilen
- 1000 Zeichenbytes
- 1000 Farbbytes

Das binaere `.scr`-Format speichert zuerst die 1000 Zeichenbytes und anschliessend die 1000 Farbbytes. Beim Laden einer 1000-Byte-Datei wird Weiss als Standardfarbe eingesetzt.

Bedienung:

- linke Maustaste: aktuelles Zeichen und aktuelle Farbe setzen
- rechte Maustaste: Leerzeichen mit schwarzer Farbe setzen
- Ziehen: mehrere Zellen bearbeiten
- Pfeiltasten: Cursor bewegen
- Leertaste/Eingabe: aktuelle Auswahl setzen
- Entf/Backspace: Zelle loeschen
- Seite leeren
- gesamte Seite mit dem ausgewaehlten Zeichen und der ausgewaehlten Farbe fuellen

Quellcodeausgabe:

- Assembler: `C64TextScreenCharacters` und `C64TextScreenColors`
- Pascal: zwei `array[0..24, 0..39] of Byte`
- C: zwei `unsigned char [25][40]`
- BASIC: `SC(999)` und `CO(999)` mit DATA-Zeilen

## Pixel-Bildschirm-Editor

Aufruf:

- `Werkzeuge -> C64 Pixel-Bildschirm-Editor ...`
- `Ctrl+Alt+X`
- Toolbar-Schaltflaeche
- Doppelklick auf `.px16`, `.pixel` oder `.pix`

Die Arbeitsflaeche ist plattformneutral:

- 320 Pixel breit
- 200 Pixel hoch
- 16 Farbindizes

Das Rohformat umfasst 32000 Bytes. Je zwei Pixel werden in einem Byte gespeichert:

- oberes Nibble: linkes Pixel
- unteres Nibble: rechtes Pixel

Werkzeuge:

- Stift
- Radierer
- Linie
- Rechteck
- gefuelltes Rechteck
- Kreis
- gefuellter Kreis
- Flaeche fuellen

Die rechte Maustaste zeichnet mit Farbe 0. Formen werden beim Ziehen vorab angezeigt und beim Loslassen in die Pixelmatrix uebernommen.

Quellcodeausgabe:

- Assembler: gepackte `.byte`-Daten
- Pascal: `array[0..31999] of Byte`
- C: `unsigned char C64PixelScreenData[32000]`
- BASIC: `PX(31999)` mit DATA-Zeilen

## Beispielverzeichnisse

- `examples/screens`
- `examples/pixel_screens`
