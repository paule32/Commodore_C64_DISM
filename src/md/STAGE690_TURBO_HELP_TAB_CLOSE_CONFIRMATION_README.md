# Stage 690 – Turbo-Hilfe-Tabs mit Speicher-Rückfrage schließen

**Verbindliche Basis:** Stage 689 (`d64_dism_stage689.zip`).

## Fehler

`TurboHelpEditor.close_document()` verlangte bei allen noch namenlosen Tabs unmittelbar `Speichern unter ...`, selbst wenn die Datei nie verändert wurde. Ein Abbruch des Speicherns verhinderte daher das Schließen des beim ersten Anklicken des Turbo-Hilfe-Hauptknotens automatisch erzeugten `Unbenannt.thlp`-Tabs.

## Änderung

Datei `turbo_help_gui.py`:

- Beim Schließen einer geänderten oder noch namenlosen `.thlp`-Registerkarte erscheint eine thematisierte Rückfrage **„Soll die Hilfedatei … vor dem Schließen gespeichert werden?“**.
- **Ja:** vorhandener Speichervorgang; ein neuer Dateiname wird ggf. mit `Speichern unter ...` erfragt. Bei Abbruch oder Schreibfehler bleibt der Tab offen.
- **Nein:** Tab wird ohne Speicherung geschlossen. Bestehende Dateien auf der Festplatte bleiben unverändert.
- **Abbrechen**, Escape oder Schließen des Dialogs: Tab bleibt offen.
- Eine unveränderte, bereits gespeicherte `.thlp`-Datei schließt ohne Rückfrage.
- Dialoge verwenden die etablierte `MainWindow._create_message_box()`-Gestaltung, also das aktuelle Dark-/Light-Theme aus Stage 689. Das Schließen löst keinen weiteren automatischen Speichervorgang bei einem Tabwechsel aus.
- Der Tooltip des roten Kreuzes wurde aktualisiert.
- Der `Settings`-Tab bleibt davon getrennt und wird durch das Verwerfen des Start-Tabs nicht verändert.

## Tests

Neue Datei `test_stage690.py` mit Qt-freien Verhaltenstests für Speichern, Verwerfen, Abbrechen, unveränderte Quellen, die Kombination mit dem Settings-Tab, Dateiintegrität und Tabwechsel.

Ausführung im Projektordner:

```bash
pytest -q test_stage690.py test_stage689.py test_stage688.py test_stage687.py test_stage686.py test_stage662.py
```

Ergebnis: **36 bestanden**.

Erweiterte Suite mit weiteren Stage-Tests: **79 bestanden, 1 fehlgeschlagen**. `test_stage665.py::test_editor_api_unchanged_for_save_switch_and_compile` erwartet den textuell identischen Aufruf `compile_help_sources(paths, executable)`, der in der unveränderten Stage 689 bereits nicht mehr vorkommt. Der alte Test wurde für Stage 690 nicht verändert.

Ein echter PyQt5-GUI-Laufzeittest unter Windows ist noch offen, da PyQt5 in der Prüfumgebung nicht installiert ist.
