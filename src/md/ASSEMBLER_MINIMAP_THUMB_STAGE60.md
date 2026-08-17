# Stage 60 – Assembler-Mini-Map: 120-px-Viewport-Griff

## Änderung

Für Assembler-Editoren besitzt der klick- und verschiebbare Viewport-Griff der Mini-Map jetzt eine Mindesthöhe von **120 Pixeln**.

Betroffen sind:

- Rohdaten-Editor für `.asm`, `.s`, `.a65`, `.m68k`, `.inc`
- erzeugter ASM-Tab

Andere Mini-Maps (z. B. Markdown und nicht-Assembler-Rohdaten) behalten die bisherige Mindesthöhe von 18 px.

## Scroll-/Drag-Logik

Die Abbildung zwischen Editor-QScrollBar und Mini-Map wurde nicht verändert. Weiter verwendet werden:

- `QStyle.sliderPositionFromValue()` für Editor -> Mini-Map
- `QStyle.sliderValueFromPosition()` für Mini-Map -> Editor
- derselbe Drag-Offset
- Klick außerhalb des Griffes zentriert den Griff auf die Klickposition
- Mausrad verändert weiterhin direkt die vertikale Editor-QScrollBar

Die Griffhöhe wird weiterhin auf die reale Mini-Map-Höhe begrenzt. Ist das Widget kleiner als 120 px, belegt der Griff deshalb maximal die vorhandene Höhe.

## Dynamische Dateitypen

Nach `Speichern unter` oder Umbenennen wird die Mindesthöhe neu gesetzt:

- Assembler-Datei: 120 px
- anderer Quelltext: 18 px

## Tests

- Stage-60-spezifisch: 5/5
- relevante Mini-Map-/ASM-Tests: 31/31
- Gesamtprojekt: 620/620
