# Stage 574 – Dark-/Light-Mode für Dialoge im deutschen Grammatikparser

**Verbindliche Ausgangsbasis:** `d64_dism_stage573.zip`

## Problem

Die Meldungsfenster des Agents 0001 wurden bisher mit den statischen
`QMessageBox.question`, `QMessageBox.warning` und `QMessageBox.information`
aufgerufen. Dadurch ließen sich ihre Hintergründe, Texte und Schaltflächen
nicht zuverlässig an das aktive Theme anpassen; im Dark-Mode konnten helle
Dialogflächen und eine helle Windows-Titelleiste erscheinen.

## Korrekturen

- Neue Klasse `_GrammarMessageBox(QMessageBox)` in `agent_0001.py`.
- Dialog-spezifische `QPalette` und CSS für Dark- und Light-Mode; ausdrücklich
  gefärbte Nachrichtentexte, Buttons, Hover-/Pressed-/Default-Zustände.
- Windows-DWM-Attribut für dunkle Titelleisten (`20`, bei älteren Systemen
  Fallback `19`); beim Zurückschalten wird der Wert wieder deaktiviert.
  Nicht-Windows-Systeme behalten ihre normale Fensterverwaltung.
- Alle sechs bisherigen Benachrichtigungs-/Bestätigungsstellen benutzen
  `_show_grammar_dialog`: JSON-Ladefehler, leere/ungültige Eingabe,
  JSON-Lesefehler, Speichernachfrage, Speicherfehler und Speicherbestätigung.
- Die Anzeige wird bereits **vor** dem anfänglichen Laden der JSON-Datei
  an das aktuelle Anwendungstheme angepasst, damit auch Fehlermeldungen
  beim Programmstart korrekt aussehen.
- Existierende modale Agent-Meldungsfenster werden bei `set_dark_mode()`
  ebenfalls aktualisiert.
- Die Abfrage vor dem Speichern ist weiterhin standardmäßig **Nein**;
  nur ausdrückliches **Ja** übernimmt den Text in die JSON-Datei.

## Umfang

Geändert: `agent_0001.py`, bestehende Tests `test_stage571.py` und
`test_stage572.py` auf die zentrale MessageBox-Methode angepasst.
Neu: `test_stage574.py` und diese Dokumentation.

`d64_dism.py`, `agent_0001_core.py`, `agent_0001_data.py`, die Beispiel-JSON
und alle anderen Projektmodule bleiben unverändert gegenüber Stage 573.

## Tests

Die Agent-Regressionen `test_stage571.py` bis `test_stage574.py` wurden
in der bereitgestellten Umgebung ausgeführt: **26 bestanden, 4 übersprungen**.

Breiterer Regressionstest der Stages 550–574 (`test_stage55*.py`,
`test_stage56*.py`, `test_stage57*.py`): **254 bestanden, 52 übersprungen,
213 Subtests bestanden**. Die optionalen GUI-Tests benötigen PyQt5;
eine native Kontrolle der Dialogfarben und der Windows-Titelleiste unter
Windows steht noch aus.
