# Stage 658 – Turbo Help Projektblatt: bool statt Editor

Verbindliche Basis: `d64_dism_stage657.zip`.

## Fehler

Beim Anklicken eines `.thlp`-Blatts unter `Projekt-Informationen -> Turbo Help`
trat ein `AttributeError: 'bool' object has no attribute 'load_document'` auf.
Der Aufruf `show_turbo_help_compiler_dock()` wurde als Editor-Referenz
verwendet, obwohl im gemeldeten GUI-Lauf ein boolescher Wert zurückkam.

## Korrektur

- `d64_dism.py`: Neue Methode `_turbo_help_active_editor()` liefert nur ein
  tatsächliches `TurboHelpEditor`-Widget. Sie überprüft zuerst
  `self.turbo_help_compiler_editor` und stellt bei Bedarf die Referenz aus
  `self.turbo_help_compiler_dock.widget()` wieder her.
- `_project_turbo_help_open()` aktiviert zuerst das Dock, liest anschließend
  den geprüften Editor und ruft nur darauf `load_document(path)` auf.
- Ebenso abgesichert: Neu: Inhalt, ungespeicherte Blätter, Hinzufügen,
  Entfernen und der Dock-Wiederverwendungsweg.
- Sollte kein Editor verfügbar sein, erscheint eine Dialogfehlermeldung
  statt einer unbehandelten Exception.
- Bestehende `.thlp`-Dateien und Tabs werden nicht gelöscht, und
  `libd64_qt5.dll` bleibt unverändert.

## Tests

- `test_stage658.py`: fünf neue Regressionstests, darunter direkte
  Simulation eines booleschen Rückgabewerts, eines gespeicherten booleschen
  Editor-Attributs und eines ungespeicherten Blatts.
- `test_stage654.py`: bestehendes GUI-Testgerüst an den geprüften
  Editorzugriff angepasst.
- Geprüft: 54 gezielte Tests (`test_stage650.py` bis `test_stage658.py`)
  bestanden. Kein nativer Windows-GUI-Laufzeittest in dieser Umgebung.

## Deployment

Nur `d64_dism.py` aktualisieren oder das komplette ZIP übernehmen.
Keine Neuübersetzung der Qt5-Bridge und keine Änderung der Hilfedateien nötig.
