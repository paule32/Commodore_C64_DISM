# Stage 510 – Speichern im Kontextmenü des Ressourcenbaums

**Verbindliche Basis:** d64_dism_asm_509.zip. Die restlichen Einträge und Funktionen des Kontextmenüs bleiben erhalten.

## Erweiterung

Das per Rechtsklick auf die TreeList links neben dem RC-Quelltexteditor geöffnete Kontextmenü beginnt nun mit:

```
Speichern                  Strg+S
Speichern unter ...
-------------------------------
Neu:  Dialog
Neu:  Menü
Neu:  Text
Neu:  Icon
Neu:  Bitmap
Neu:  Cursor
Neu:  RCDATA
-------------------------------
Alles auswählen
Kopieren
Einfügen
Löschen
```

- **Speichern**: Ruft `WindowsResourceEditorWidget.save()` auf, für bisher unbenannte Dateien über deren vorhandene `save_as()`-Weiterleitung.
- **Speichern unter ...**: Ruft `WindowsResourceEditorWidget.save_as()` auf und öffnet den bestehenden Qt-Dateidialog.
- **Strg+S**: Die Kontextmenü-Aktion zeigt `QKeySequence.Save`. Der vorhandene globale Shortcut des Hauptfensters routet im aktiven Ressourcen-Workspace bereits an `save()`; es wird kein zweiter globaler Shortcut installiert.
- Die sieben Neu-Aktionen sowie Auswählen, Kopieren, Einfügen und Löschen sind unverändert und verbleiben hinter dem zusätzlichen Separator.

## Betroffene Datei

- `d64_dism.py` in `WindowsResourceEditorWidget._show_resource_tree_context_menu()`.

## Nachweise

- Kontextmenü-Aufbau, beide Signalslots, Speichern und Speichern-unter-Dialog: `test_stage510_resource_tree_save_menu.py`.
- Bisherige Kontextmenü-Regressionsfälle sind an die zwei vorangestellten Aktionen angepasst.
- Python-Syntax- und ZIP-Integritätsprüfung.

Hinweis: Ein nativer GUI-Test in PyQt5 auf Windows wurde nicht durchgeführt.
