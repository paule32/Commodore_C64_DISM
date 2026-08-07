# C64 Character-Editor

Der Qt5-Dateiexplorer enthält nun einen eigenen Editor für die 255 frei
editierbaren C64-Zeichen `$01` bis `$FF`. Zeichen `$00` bleibt als reserviertes
Leerzeichen Bestandteil der Datei, wird jedoch nicht in der Auswahlliste
angeboten.

## Öffnen

Der Editor kann über folgende Wege geöffnet werden:

- `Werkzeuge -> C64 Character-Editor ...`
- Tastenkürzel `Strg+Alt+C`
- Toolbar-Schaltfläche des Character-Editors
- Doppelklick auf eine Datei mit der Erweiterung `.chr` oder `.charset`

## Bearbeiten

Links werden alle 255 Zeichen als Vorschau angezeigt. Rechts befindet sich das
8×8-Pixelraster des ausgewählten Zeichens.

- Linke Maustaste: Pixel setzen
- Rechte Maustaste: Pixel löschen
- Ziehen mit gedrückter Maustaste: mehrere Pixel bearbeiten
- Pfeiltasten: Rastercursor bewegen
- Leertaste oder Eingabetaste: aktuelles Pixel umschalten
- Entf oder Rücktaste: aktuelles Pixel löschen

Zusätzliche Operationen:

- Leeren
- Invertieren
- horizontal oder vertikal spiegeln
- nach links, rechts, oben oder unten verschieben
- Zeichen als acht Hexbytes kopieren und einfügen
- Zeichen direkt über Hex- oder Dezimalcode anspringen

Die Vorder- und Hintergrundfarbe beeinflussen nur die Editorvorschau. Die
Zeichensatzdatei selbst enthält pro Zeichen acht reine Bitmapbytes.

## Dateiformate

Beim Laden werden zwei Rohformate akzeptiert:

- 2048 Bytes: 256 Zeichen `$00` bis `$FF`
- 2040 Bytes: 255 Zeichen `$01` bis `$FF`; Zeichen `$00` wird automatisch mit
  acht Nullbytes ergänzt

Beim Speichern wird immer ein vollständiger 2048-Byte-Zeichensatz geschrieben.

## Quellcodeexport

Der Editor exportiert denselben Zeichensatz als:

- MOS-6510-Assembler mit `.byte`
- C als `const unsigned char C64CustomCharset[256][8]`
- Pascal als `array[0..255, 0..7] of Byte`

Unter `examples/characters` befindet sich ein selbst erstellter kleiner
Beispielzeichensatz in allen unterstützten Exportformaten. Ein C64-ROM-Abbild
wird nicht mitgeliefert.

## Sprachabhängiges Speichern

Rechts befindet sich jetzt die Gruppe `Ausgabe Format` mit Assembler, Pascal,
C und BASIC. Der darunter liegende Button `Speichern als...` schreibt die
Charmap direkt in der gewählten Sprache. BASIC wird als zweidimensionales
Array mit 256 `DATA`-Zeilen exportiert.

## Paletten-Editor

Unter `Werkzeuge -> C64 Paletten-Editor ...` steht ein eigener Editor für die
16 RGB-Darstellungen der C64-Farbnummern zur Verfügung. Er unterstützt ein
48-Byte-Rohformat und Quellcodeexport für Assembler, Pascal, C und BASIC.
Weitere Einzelheiten stehen in `C64_CHARACTER_PALETTE_EDITOR.md`.
