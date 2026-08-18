# Stage 103 – Pattern-Rückkehr, Font-Farbbuttons und Dark-Mode

## Pattern → Ohne Muster

Der Formulardesigner schaltet `Qt.WA_TranslucentBackground` nicht mehr zur Laufzeit
zwischen `True` und `False` um. Stattdessen werden Pattern, Vollton-Hintergrund,
Font und Border in einem gemeinsamen QSS-/Palette-Pfad neu aufgebaut.

Beim Wechsel von einem Pattern zu `Ohne Muster` wird ein eventuell gecachter
transparenter Stylesheet-Zustand explizit gelöscht und anschließend der komplette
aktuelle Style neu angewendet. Border-, Font- und Brush-Eigenschaften bleiben erhalten.

## Font Background / Foreground

Beide Font-Farbzeilen besitzen jetzt rechts neben der ColorComboBox einen `...`-Button.
Der Button öffnet `QColorDialog`. Nach Bestätigung wird die gewählte Farbe:

1. in den ComboBox-Eintrag `Eigene Farbe (#RRGGBB)` geschrieben,
2. als aktueller ComboBox-Eintrag ausgewählt,
3. sofort auf die selektierte Designer-Komponente angewendet.

## Dark-Mode

Die Farbswatch-Buttons erhalten im Dark-Mode einen hellen Rand und einen gelben
Hover-Rand. Das gilt insbesondere für `Brush -> Foreground -> ...` sowie die neuen
Font-Farbbuttons.
