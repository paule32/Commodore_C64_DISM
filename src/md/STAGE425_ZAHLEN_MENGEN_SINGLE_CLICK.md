# Stage 425 – Zahlen-Mengen, Einfachklick und eingeklappte Matrix-Arten

## Basis
- Verbindliche Basis: `d64_dism_asm_424.zip`

## Änderungen

### 1. Neues Blatt unter `Grundwissen`
- Unter dem Hauptknoten `Grundwissen` wurde als erstes Blatt `Zahlen-Mengen` eingefügt.
- Die rechte Ansicht wird als eigene QPainter-Seite gezeichnet (`number_sets_fact.py`).
- Die Darstellung orientiert sich an der Benutzerreferenz, ist aber keine Pixelkopie.
- Die Flächen werden als gefüllte QPainterPath-/RoundedRect-Bereiche gezeichnet; Texte entstehen per DrawText.

### 2. Mathematik-Baum: Einfachklick
- Knoten und Blätter im Fakten-Baum öffnen jetzt bereits bei einfachem Mausklick die zugehörige rechte Ansicht.
- Dasselbe gilt zusätzlich für den Spiele-Baum.
- Für Gruppenknoten ohne direkte Seite wird die erste passende Unterseite geöffnet.

### 3. Startzustand der Matrizen-Arten
- `Matrizen -> Arten von . . .` startet jetzt eingeklappt.

## Geänderte Dateien
- `d64_dism.py`
- `number_sets_fact.py` (neu)
- `test_stage425_number_sets_single_click.py` (neu)
- `STAGE425_ZAHLEN_MENGEN_SINGLE_CLICK.md` (neu)

## Prüfungen
- neue Stage-425-Strukturtests erfolgreich
- Syntaxprüfung (`py_compile`) erfolgreich
