# Stage 424 – Matrizen-Ansichten folgen Dark-/Light-Mode

## Ausgangsbasis
- `d64_dism_asm_423.zip` (verbindlich, ungekürzte Projektdateien)

## Änderung
Die beiden Seiten unter `Mathematik -> Fakten -> Matrizen -> Rechnen mit . . .`
werden durch `set_dark_mode(enabled)` **vollständig** in passenden Farben
neu gezeichnet:

- **Multiplikation**: Seiten- und Kachelhintergrund, Überschrift, Text,
  Matrixklammern, Formelzeichen, Zeilen-/Spaltenmarkierungen und Ergebnisfelder.
  Dunkel: marineblaue Hintergründe und helle Formeln. Hell: cremeweiße Flächen,
  dunkle Formeln und kontrastreiche Markierungen.
- **Verschieben 3-D**: Seitenhintergrund samt Verlauf, Überschrift und
  Abschnittsüberschriften, Rotationsmatrizen, Klammern, Würfel und Achsen-
  Zeichnungen. Dunkel: dunkler Verlauf/helle Beschriftung; Hell: cremefarbener
  Verlauf/dunkle Beschriftung.

Die Schriftfarben sind also **nicht mehr fest an Dark-Mode gebunden**.
Ein Wechsel über das Anwendungstheme wird bereits über
`MathematicsLearningDockWidget.set_dark_mode(enabled)` an beide Widgets
weitergereicht. Die Widgets verwalten ihre Farbpalette pro Instanz und rufen
bei jedem Themewechsel `update()` auf.

## Dateien
- `math_matrix_theme.py` (neu, von Qt unabhängig)
- `rotation_matrix_fact.py` (geändert)
- `multiplication_matrix_fact.py` (geändert)
- `test_stage424_matrix_theme.py` (neu)

`d64_dism.py` selbst benötigt keinen Eingriff: Die Anbindung beider Ansichten
an das übergeordnete Theme war in Stage 423 schon vorhanden.

## Regressionen
- Alle 38 bisherigen Matrizen-Arten bleiben bestehen.
- Icons, Baumstruktur, Umbenennung in `Verschieben 3-D` und die Seite
  `Multiplikation` bleiben unverändert.
- Stage-423-Verschiebung und Zellbreite der unteren Matrix `P_z` bleiben
  bei `x = 95` und `col_width = 125`.

## Prüfung
- Stage-421-Tests: 5 bestanden
- Stage-422-Tests: 5 bestanden
- Stage-423-Test: 1 bestanden
- Stage-424-Tests: 4 bestanden
- Zusätzlich beide `paintEvent`-Methoden mit einem vereinfachten QPainter-
  Ersatz vollständig im Zyklus **Dark -> Light -> Dark** ausgeführt.
- Python-Syntaxprüfung (`py_compile`): bestanden.

**Nicht geprüft:** echte Windows-/PyQt5-Renderausgabe (PyQt5 ist auf der
Testmaschine nicht installiert); die QPainter-Dummytests sind keine
pixelgenaue visuelle Abnahme.
