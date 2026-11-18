# Stage 613 – Dateinamen-Editoren im Dialog „Neu: Programm“

**Verbindliche Ausgangsbasis:** `d64_dism_stage612.zip`.

## Problem

Der eingebettete, nicht-native `QFileDialog` in `DBaseProjectOpenFileDialog`
zeigt beim Umbenennen/Anlegen eines Datei- oder Verzeichnisnamens in der
Detailansicht ein sehr schmales Inline-`QLineEdit`. Zusätzlich verengen
Rahmen und CSS-Abstände den tatsächlich sichtbaren Textbereich.

## Änderung

- Neuer `DBaseProjectFileNameEditDelegate` in `d64_dism.py` auf Basis von
  `QStyledItemDelegate`.
- Beim **Inline-Bearbeiten** eines Namens wird nur der betroffene Editor
  `QLineEdit` angepasst: `setFrame(False)`, Widget-Innenränder und
  Textmargins `(0, 0, 0, 0)`; im lokalen Stylesheet `border:0`,
  `margin:0`, `padding:0`.
- In der `QTreeView`-Detailansicht wird die Bearbeitungsfläche bis an den
  rechten Viewport-Rand vergrößert. X- und Y-Position sowie Zeilenhöhe
  bleiben unverändert. Die normalen Spaltenbreiten bleiben erhalten.
- Auch der Editor der `QListView` (Symbolansicht) hat keine Ränder;
  **dort** erfolgt jedoch keine Breitenvergrößerung über die Kachel hinaus.
- Installation ausschließlich für Spalte 0 der Qt-Datei-/Ordneransichten
  `treeView` und `listView`. Die Verzeichnisnavigation in der Seitenleiste
  sowie die übrigen Spalten bleiben unberührt.
- Standardverhalten von Qt (`EditRole`, Dateinamenprüfung, Commit/Cancel,
  Dateisystemmodell, Auswahl und Kontextaktionen) bleibt beim Qt-Delegate.
- Die korrigierte Darstellung gilt in Hell- und Dunkelmodus. Der Dialog
  wird auch für die anderen dBASE-Projektdateitypen wiederverwendet.

## Prüfungen

`python -m unittest -q test_stage613` – 7/7 erfolgreich mit Qt-Doubles;
inklusive Rahmen-/Margin-Prüfung, Geometrieerweiterung und Eingrenzung
auf die Namens-Editoren.

`python -m unittest -q test_stage612 test_stage612_procedure` – 20 Tests,
19 erfolgreich, 1 Windows-spezifischer Test übersprungen.

`python -m unittest -q test_stage611 test_stage610` – 16/16 erfolgreich.

**Einschränkung:** In der verfügbaren Testumgebung ist PyQt5 nicht
installiert. Eine visuelle Kontrolle und eine tatsächliche Bearbeitung
von Datei-/Ordnernamen unter Windows mit dem GUI steht noch aus.
