# Stage 423 – Verschieben 3-D Layout-Feinanpassung

## Basis
- Verbindliche Basis: `d64_dism_asm_422.zip`

## Änderung
Für die rechte Ansicht **„Verschieben 3-D“** wurde die untere Matrixdarstellung
(`P_z`) gezielt angepasst:

- das untere Ergebnis / die untere Matrix wurde um ca. **10 Pixel nach links** verschoben
- die **Breite der Kacheln / Matrixspalten** wurde dort um ca. **10 Pixel** erweitert

## Technische Umsetzung
- `rotation_matrix_fact.py`
  - die drei unteren Bereiche verwenden jetzt pro Abschnitt eigene Layoutparameter
  - für den z-Abschnitt wurden gesetzt:
    - `x = 95` statt `105`
    - `col_width = 125` statt `115`

## Tests
- `test_stage423_rotation_matrix_layout_tweak.py` hinzugefügt
- `py_compile` erfolgreich
- Stage-423-Prüfung erfolgreich
