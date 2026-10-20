# Stage 419 – kompakte Bildschirm-Initialisierung mit STA reducer

Verbindliche Basis: `d64_dism_asm_418.zip`.

## Änderung

Bisher generierte `__basic_soft_zero_loop` bei `SCREEN ON` pro X-Wert
32 `STA $6000,x ... $7F00,x` (Bitmap) sowie vier `STA $4400,x ... $4700,x`
und vier `STA $D800,x ... $DB00,x` (Bildschirm-Farbattribute und Farb-RAM).
Mit der vorhandenen Checkbox `STA reducer` wird jetzt ein kompaktes Verfahren
genutzt: drei Aufrufe derselben Seite-Löschroutine mit `(High-Byte, Seitenzahl)`
`($60,32)`, `($44,4)` und `($D8,4)`.

Innerhalb der Routine wird bei `STA $6000,x` nur das obere Operandenbyte
(`__basic_soft_zero_store+2`) verändert, sodass alle 256 Bytes der aktuellen
Seite mit `$00` beschrieben werden. Die Routine verändert eigenen Maschinencode
(**Self-Modifying Code**) und benötigt deshalb schreibbaren C64-RAM.
Vor jedem Aufruf wird das Zielseiten-Byte ausdrücklich zurückgesetzt; mehrmaliges
`SCREEN ON` funktioniert daher genauso wie bisher. Sie berührt keinen Bitmap-
Speicher außerhalb `$6000..$7FFF` und keinen Bildschirm-/Farb-RAM außerhalb
`$4400..$47FF` beziehungsweise `$D800..$DBFF`.

- `STA reducer` **AUS**: Stage-418-Schleife unverändert (40 direkte `STA abs,X`).
- `STA reducer` **AN**: eine einzige `STA abs,X`-Anweisung, drei Speicherbereiche,
  keine Lookup-Datentabelle für diesen speziellen Nullfüllfall notwendig.
- Die bisherigen RLE-/Literal-Tabellen des Stage-418-Reducers für
  `SPRITE DRAW` und `SPRITE ERASE` bleiben unverändert.
- Optimierung zugunsten der Programmgröße: Die neue Schleife ist bei
  der Speicherinitialisierung langsamer als die vollständig entrollte Variante.
- Die Speicherschreiboperationen werden nach wie vor zur Laufzeit ausgeführt;
  sie können nicht durch bloße Datentabellen ersetzt werden.

## Messung

Kleines BASIC-Programm mit `SCREEN ON`, `SPRITE SOFTWARE ON` und `SCREEN OFF`:
- Ohne STA reducer: **1214 Bytes** PRG.
- Mit STA reducer: **1132 Bytes** PRG.
- **82 Bytes**, ca. 6,8 %, eingespart.

Für das Sprite-Demoprogramm im Vergleichs-ZIP sind die tatsächlichen
Dateigrößen gesondert angegeben (weitere Stage-418-Tabellen können greifen).

## Testnachweis

- `python -m unittest -v test_stage419_sta_reducer_screen_clear` – vier Tests.
- Unabhängiger 6510-CPU-Lauf: genau 32+4+4 Seiten vollständig auf Null;
  angrenzende Guard-Bytes unverändert; zweimaliger Aufruf ohne Neuladen.
- Direkter Vergleich kompakter/normaler PRG-Länge nach interner MOS6510-Assemblierung.
- `python -m unittest -v test_stage418_sta_reducer test_stage417_software_sprites`
  – zwölf Regressionstests.
- Echte Windows-/VICE-Darstellung hier nicht ausführbar, bleibt offen.
