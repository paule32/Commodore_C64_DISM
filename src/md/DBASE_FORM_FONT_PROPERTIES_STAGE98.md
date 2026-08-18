# Stage 98 – Font als Root-Eigenschaft

`Font` ist jetzt ein Haupt-Eintrag im Eigenschaftenbaum. Die Value-Spalte des
Root-Eintrags enthält eine ComboBox mit allen über `QFontDatabase` registrierten
Systemschriften.

Sub-Einträge:

- `Size` – SpinBox
- `Background` – ColorComboBox mit Standardfarben und `Eigene Farbe ...`
- `Foreground` – ColorComboBox mit Standardfarben und `Eigene Farbe ...`
- `Alpha` – ComboBox mit 0 bis 255
- `Fett` – CheckBox
- `Kursiv` – CheckBox
- `Stroke` – CheckBox; wird als Durchstreichung umgesetzt
- `Underline` – CheckBox

Alle Änderungen werden direkt auf das aktuell markierte Designer-Control
angewendet. `Font` kann per Doppelklick aufgeklappt/eingeklappt werden.
