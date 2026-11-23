# Stage 662 – Turbo Help Projektblätter und Tabwechsel

**Verbindliche Basis:** Stage 661 (`d64_dism_stage661.zip`).

## Fehler und Ursache

`show_turbo_help_compiler_dock()` lud bisher jedes projektseitig registrierte
`.thlp`-Dokument in einen neuen Tab. Das passierte auch beim ersten Klick auf
ein einziges Projektblatt. Der nachfolgende Projektblatt-Handler griff
zusätzlich erneut auf die Editor-Referenz zu, deren strenge Klassenprüfung
nach einem Dock-/Modulwechsel fehlschlagen konnte.

## Änderungen

* `d64_dism.py`: Beim Erzeugen des Hilfecompiler-Docks nur einen
  unmodifizierten, ersetzbaren Platzhalter anlegen. Registrierte Quellen
  werden für F2 in `project_sources` gehalten, aber **nicht automatisch
  als Tabs geöffnet**. Ein Klick auf ein Projektblatt öffnet nur dessen
  `.thlp`-Datei; weitere Klicks ergänzen nur die jeweils angewählte Quelle.
* `_project_turbo_help_open()` verwendet bevorzugt den **tatsächlich
  zurückgegebenen Editor** und fällt bei einem booleschen Rückgabewert
  sicher auf `_turbo_help_active_editor()` zurück. Dessen Prüfung
  erkennt auch gültige Qt-Editor-Objekte mit abweichender Modulidentität.
* `turbo_help_gui.py`: Tabwechsel werden zentral über
  `_sync_current()` und `_save_changes_before_switch()` abgesichert.
  Wurde das bisherige Dokument verändert, speichert der Editor es vor
  dem Wechsel. Bei einer neuen Datei erscheint **Speichern unter ...**.
  Abbruch oder Schreibfehler bewirkt die Rückkehr zum vorherigen Tab.
  Das gilt auch für Wechsel über die Tab-Leiste oder die Tastatur.
* `load_document()` und `new_document()` prüfen Änderungen bereits
  **vor dem Erstellen oder Aktivieren** eines weiteren Tabs.
* Der gewählte Tab und sein `QPlainTextEdit` erhalten anschließend den
  Fokus. Mehrmaliges Anklicken derselben Datei erzeugt keinen zweiten Tab.
* Das Projektdateiverzeichnis, die GNU-PO/HLP-Kompilierung, F2 und die
  Qt5-Bridge bleiben unverändert. F2 berücksichtigt weiterhin auch
  Projektquellen, deren Tabs noch nicht geöffnet wurden.

## Nachweis

`python -m pytest -q test_stage662.py test_stage661.py test_stage659.py
 test_stage658.py test_stage657.py test_stage656.py test_stage655.py
 test_stage654.py test_stage653.py test_stage652.py test_stage651.py
 test_stage650.py`

Ergebnis: **76 passed**. Neue Tests simulieren die echte
`TurboHelpEditor`-Tabwechselsteuerung einschließlich erfolgreichem
Speichern und einem abgebrochenen Speichern-unter-Dialog.

Die ursprüngliche Anwendung enthält Python-3.15-`lazy import`-Syntax.
Die Qt5-GUI konnte in dieser Linux-Testumgebung nicht nativ gestartet
werden; für die GUI-Prüfung wurden kleine Qt-Testdoubles verwendet.
Ein visueller Windows-/PyQt5-Test bleibt offen.

## Installation

Den vollständigen Inhalt von `d64_dism_stage662.zip` anstelle von
Stage 661 einsetzen. Die Qt5-Bridge-Bibliothek muss nicht neu gebaut
werden; ausschließlich Python-Dateien wurden verändert.
