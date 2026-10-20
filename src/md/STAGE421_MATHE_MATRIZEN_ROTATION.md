# Stage 421 – Matrizen: Arten von … / Rechnen mit … / Rotation Matrix

**Verbindliche Basis:** `d64_dism_asm_420(1).zip` (Benutzer-Upload).

## Änderungen

- `d64_dism.py`: Mathematik/Fakten/Matrizen enthält jetzt die zwei
  Gruppen **Arten von . . .** und **Rechnen mit . . .**.
- Alle 38 bestehenden Matrixarten werden *unverändert* unter
  **Arten von . . .** angezeigt. Ihre bisherigen Schlüssel und
  `BasicMathRulesFactWidget`-Inhalte bleiben erhalten.
- **Rechnen mit . . . → Rotation Matrix** öffnet rechts eine eigene
  scrollbare Lernseite (`matrix_rotation`).
- `rotation_matrix_fact.py`: eigenständige Qt5-/QPainter-Lernseite nach
  der hochgeladenen Bildvorlage; Formeln, Drahtwürfel und Pfeile sind
  native Vektorgrafik statt einer kopierten Rastergrafik.
- Angeforderte Wortlaute: **Elementare Verschiebungen**,
  **Verschiebung um die x-Achse**, **Verschiebung um die y-Achse**,
  **Verschiebung um die z-Achse**.
- Der am Würfel unten eingeblendete störende Schriftzug wurde nicht
  übernommen; keinerlei Wasserzeichen wird gezeichnet.
- Bestehende Theme-Umschaltung und `QScrollArea` werden weiterverwendet.

**Mathematischer Hinweis:** Die Matrizen beschreiben Drehungen (Rotationen),
keine Translationen. Die vier Überschriften bleiben dennoch exakt nach
Benutzervorgabe auf "Verschiebung" gesetzt.

## Tests

```sh
python -m py_compile d64_dism.py rotation_matrix_fact.py
python -m pytest -q test_stage421_rotation_matrix.py
```

Qt5-Sichtprüfung auf Windows: `python rotation_matrix_fact.py`; die
vollständige Anwendung braucht wie zuvor PyQt5 und ihre eigenen Abhängigkeiten.

Der Test auf einer Umgebung ohne PyQt5 kann Struktur und Syntax verifizieren,
nicht jedoch die tatsächliche GUI-Laufzeit.
