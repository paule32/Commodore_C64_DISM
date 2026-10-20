# Stage 427 – Anordnung der Zahlen-Mengen korrigiert

## Verbindliche Basis
`d64_dism_asm_426.zip`

## Ursache in Stage 425/426
Die bisherigen farbigen Kacheln waren teilweise versetzt und überlappend.
Dadurch entstanden falsche optische Zugehörigkeiten und unruhige,
teilweise überlappende Beschriftungen. „imaginärer Teil“ wurde außerdem
einmal horizontal und einmal vertikal ausgegeben.

## Korrektur

Nur `number_sets_fact.py` wurde verändert:

- **Geometrie neu aufgebaut**: gemeinsame feste Spaltengrenzen (`COLUMN_EDGES`).
- **Drei Bänder nach der Bildreferenz**:
  - oben der grüne Bereich der komplexen Zahlen;
  - mittig die türkisfarbene Überlagerung der algebraischen Zahlen;
  - unten fünf klar getrennte blau/türkisfarbene Beispielspalten und rechts die grüne Spalte für reelle Zahlen.
- **Spalten von links nach rechts**: `0`, `natürliche Zahlen` (ℕ),
  `ganze Zahlen` (ℤ), `rationale Zahlen` (ℚ),
  `reelle algebraische Zahlen` (Aᵣ), `reelle Zahlen` (ℝ).
- Beispiele und Mengensymbole sind spaltengebunden und nicht mehr frei verschoben.
- Rationaler Zahlentext „¾“ kollidiert nicht mehr mit „-15,7889“.
- „imaginärer Teil“ wird nur noch einmal, vertikal, dargestellt.
- Dark-Mode und Light-Mode bleiben erhalten.
- `QPainterPath` / `fillPath` / `fillRect` für Flächen und
  `QPainter.drawText` für alle Beschriftungen; **keine Bitmap-Kopie**.

Die Referenz stellt Kategorien und Beispiele in nebeneinanderliegenden
Bereichen dar. Die Grafik ist ausdrücklich ein **didaktisches Schema**,
kein strenges Mengeneinschluss-/Venn-Diagramm. Die Einträge und Beispiele
wurden nicht durch andere Lehrinhalte ersetzt.

## Dateien
- `number_sets_fact.py` – korrigiert
- `test_stage427_number_sets_arrangement.py` – neu
- `STAGE427_ZAHLEN_MENGEN_ANORDNUNG.md` – neu

## Prüfungen
- 5 neue Stage-427-Tests bestanden: Spaltengeometrie, Beispiele,
  Mal-Aufrufe, Navigation und Headless-Dark/Light/Dark-Roundtrip.
- 4 Stage-425-Tests bestanden.
- 4 Stage-426-Tests bestanden.
- 4 Stage-424-Tests bestanden.
- Syntaxprüfung (`py_compile`) erfolgreich.
- Reale Windows-/PyQt5-Sichtprüfung steht noch aus.
