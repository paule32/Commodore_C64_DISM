# Stage 440 – C64 Textbildschirm-Zellhintergrund und GroupBox-Titel

Verbindliche Basis: `d64_dism_asm_439.zip`.

## Text-Bildschirm-Editor

- Jede der 40 × 25 Positionen enthält nun drei unabhängig gespeicherte Werte:
  - `character` (0–255, ein Byte)
  - `background` (0–15, ein Byte)
  - `color` / Vordergrund (0–15, ein Byte)
- **Nur Farbe zeichnen** verändert ausschließlich das Hintergrundfarb-Byte der gewählten Zelle. Zeichencode und Vordergrundfarbe bleiben erhalten. Rechtsklick im Farbmodus setzt ausschließlich den Zellhintergrund auf C64-Schwarz zurück.
- Im normalen Zeichenmodus werden Zeichen und Vordergrundfarbe gesetzt, ohne eine vorhandene Zellhintergrundfarbe zu überschreiben.
- Der Screen-Renderer füllt jede Zellfläche mit ihrer eigenen Hintergrundfarbe und zeichnet das Zeichen mit dessen Vordergrundfarbe.
- „Farbe auf aktuelle Zelle“ berücksichtigt den Farbmodus.
- Neue binäre `.scr`-/`.screen`-Dateien nutzen das verlustfreie erweiterte **3000-Byte-Format**: 1000 Zeichen, anschließend 1000 Zellhintergründe, anschließend 1000 Zeichenfarben. Alte 1000-/2000-Byte-Dateien können weiterhin importiert werden; fehlende Hintergründe werden als 0 (schwarz) interpretiert.
- JSON-Version 2 schreibt explizit `background` pro Zelle, während `color` die Vordergrundfarbe bezeichnet. Alte JSON-Strukturen können weiterhin eingelesen werden.
- Assembler-, C-, Pascal- und BASIC-Exporte umfassen auch die eigene Hintergrundebene.
- Ältere Funktionsaufrufe ohne Hintergrundparameter arbeiten aus Kompatibilitätsgründen weiterhin mit den ursprünglichen Zweiebenen-Rückgaben. Der Editor verwendet beim Laden die neue dreifache Rückgabe.

**Hinweis:** Das erweiterte 3000-Byte-Format bildet die zusätzlichen Zellattribute der Editor-Software ab. Es ist nicht mit dem unveränderten VIC-II-Textspeicherformat eines originalen C64 gleichzusetzen: Auf der ursprünglichen Hardware wird die Hintergrundfarbe normalerweise über gemeinsame Register eingestellt.

## Dark-Mode für QGroupBox-Titel

Weiße Gruppentitel bei aktiviertem Dark-Mode für:

1. C64 Text-Bildschirm-Editor
2. C64 Pixel-Bildschirm-Editor
3. C64 Paletten-Editor
4. C64 Character Editor
5. Localize PO→MO
6. Doxygen Dokumentation

Beim Zurückschalten in den Light-Mode werden die vorherigen lokalen Stylesheets der Gruppen wiederhergestellt. Die Änderung gilt sowohl bei der initialen Erstellung als auch bei der globalen Theme-Umschaltung.

## Änderung und Test

- `d64_dism.py`: Farbmodelle, Datei-/JSON-/Codecs, Oberfläche und Theme-Verteilung.
- `test_stage440_c64_cell_colors_and_themes.py`: 10 neue Tests (reale Funktionen isoliert aus der großen Quelldatei geprüft).
- `STAGE440_C64_ZELLHINTERGRUND_GROUPBOX_DARKMODE.md` (neu).

Geprüft: Syntax via `py_compile`, 10 neue Tests, ZIP-Integrität. Visuelle Windows-/PyQt5-Prüfung ist in der Laufzeitumgebung ohne PyQt5 nicht möglich.
