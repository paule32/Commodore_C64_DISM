# Stage 434 – dBASE-Dateidialog mit Erstellen, Öffnen und Abbrechen

**Verbindliche Ausgangsbasis:** `d64_dism_asm_433.zip`

## Neuer Dialog
- Standard-Geometrie: `X, Y, 640, 480`; X/Y werden aus der Mitte des Elternfensters berechnet.
- Bestehender Dark-/Light-Mode mit 3-Pixel-Rahmen, Verlaufstitelleiste (im Dark-Mode Schwarz bis Grau), Schließen-X und eingefärbtem Detail-Header bleibt vorhanden.
- Titelleisten-X von 18 auf 36 Pixel vergrößert; Navigations-/Ansichtssymbole von typischerweise 16 auf 34 Pixel vergrößert.
- Drei getrennte Schaltflächen: `Erstellen`, `Öffnen`, `Abbrechen`. Der eingebettete Qt-Dateibrowser zeigt seine eigene Standard-ButtonBox nicht mehr.

## Erstellen
- Der ausgewählte oder eingetippte Dateiname wird gegen das Verzeichnis des Datei-Browsers auf Existenz geprüft.
- Bei vorhandener Datei wird **nichts überschrieben**. Stattdessen erscheint eine modale Warnung mit `Die angegebene Datei existiert bereits` und `OK`.
- Bei freiem Dateinamen wird die Operation `create` zurückgegeben. Die vorhandene Projektdatei-Logik legt danach das typgerechte Grunddokument an und öffnet es.
- Vor dem tatsächlichen Schreiben wird erneut auf Existenz geprüft; auch FileExistsError wird mit der neuen Warnung behandelt.

## Öffnen
- Die Operation `open` akzeptiert nur eine vorhandene reguläre Datei, für die reale Lese- und Schreibzugriffe möglich sind (Datei wird dabei nicht verändert).
- Bei fehlenden Rechten erscheint der Hinweis `Sie haben nicht die benötigten Rechte um die ausgewählte Datei zu öffnen/bearbeiten` mit `OK`.
- Auf dem Projekt-Workflow wird die Rechteprüfung wiederholt; bereits vorhandene Dateien werden beim Öffnen **nicht** neu erzeugt/überschrieben.
- Die dBASE-PRG-Binärprüfung aus Stage 431 bleibt unverändert.

## Warn-Dialoge
- Eigene Klasse `DBaseProjectWarningDialog`: modal, Dark-/Light-Mode, 3-Pixel-Rahmen, Titelleiste mit Schwarz-Grau-Verlauf im Dark-Mode, Schließen-X rechts und OK-Button.

## Geänderte Dateien
- `d64_dism.py`: Qt-Dialoge, Dateiauswahl und Projektbaum-Workflow
- `dbase_project_new.py`: `can_open_dbase_project_file` als GUI-unabhängige Zugriffsprüfung
- `test_stage432_dbase_file_dialog_theme.py`: alte UI-Erwartungen an neue Geometrie/Icons angepasst
- `test_stage434_dbase_dialog_actions.py`: neue Tests für Dialog, Zugriffsrechte, Dateien und Projektverarbeitung

## Tests
- Alle Stage-431–434-Tests mit Python/pytest erfolgreich.
- Python-Syntaxprüfung erfolgreich.
- Linux-Testumgebung ohne PyQt5: eine echte Windows-/PyQt5-GUI-Sichtprüfung ist weiter erforderlich.
