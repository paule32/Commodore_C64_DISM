# Stage 99 – Border-Eigenschaften im dBase-Formulardesigner

## Neuer Root-Eintrag

`Border` ist ein eigener Root-Knoten. Direkt am Root befindet sich eine ComboBox
mit folgenden Rahmentypen:

- Kein Rahmen
- Solid
- Dashed
- Dotted
- Double
- Hard Shadow rechts/unten
- Hard Shadow links/oben
- Hard Shadow rechts
- Hard Shadow unten

## Untereigenschaften

- Size – SpinBox in Pixeln
- Color – ColorComboBox inkl. Eigene Farbe
- Rounded TL – SpinBox in Pixeln
- Rounded TR – SpinBox in Pixeln
- Rounded BL – SpinBox in Pixeln
- Rounded BR – SpinBox in Pixeln

Alle Änderungen wirken sofort auf das aktuell selektierte Control. Die vier
Eckenradien sind voneinander unabhängig. Hard-Shadow-Stile verwenden einen
ungeglätteten QGraphicsDropShadowEffect (`blurRadius = 0`) und die gewählte
Border-Farbe.
