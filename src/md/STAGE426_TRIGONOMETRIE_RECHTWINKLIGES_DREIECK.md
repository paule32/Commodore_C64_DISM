# Stage 426 – Trigometrie / Rechtwinkliges Dreieck

## Basis
- Verbindliche Basis: `d64_dism_asm_425.zip`

## Änderungen

### 1. Geometrie-Startzustand
- Unter `Grundwissen -> Geometrie` werden jetzt
  - `Flächen`
  - `Volumen`
  standardmäßig **eingeklappt** dargestellt.

### 2. Trigometrie als Knoten
- `Trigometrie` ist jetzt ein **Knoten** unter `Grundwissen`.
- Darunter wurde das Sub-Blatt `Rechtwinkliges Dreieck` eingefügt.

### 3. Neue rechte Ansicht `Rechtwinkliges Dreieck`
- Neue QPainter-Seite: `trigonometry_right_triangle_fact.py`
- Inhalt nach Referenz:
  - Titel `SPICKZETTEL`
  - `Sinus, Cosinus & Tangens`
  - rechtwinkliges Dreieck mit den Beschriftungen
    - `Ankathete`
    - `Gegenkathete`
    - `Hypotenuse`
  - Formeln für `sin(α)`, `cos(α)` und `tan(α)`
- Keine 1:1-Pixelkopie; alle Elemente werden gezeichnet.

## Geänderte Dateien
- `d64_dism.py`
- `trigonometry_right_triangle_fact.py` (neu)
- `test_stage426_trigonometry_right_triangle.py` (neu)
- `STAGE426_TRIGONOMETRIE_RECHTWINKLIGES_DREIECK.md` (neu)

## Prüfungen
- Struktur- und Seitentests für Stage 426 erfolgreich
- Syntaxprüfung erfolgreich
