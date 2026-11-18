# Stage 606 – Projekt-Informationen: TreeList + ScrollArea mit vertikalem Splitter

Verbindliche Quellcodebasis: `d64_dism_stage605.zip`.

## Änderung

Im Tab **Projekt** des Docking-Fensters **Projekt / Informationen** wird die TreeList mit einem vertikalen `QSplitter` (`project_tree_name_splitter`) von den acht Projekt-Eingabezeilen getrennt. Die beiden Splitter-Kinder sind in dieser Reihenfolge:

1. `project_tree` (`QTreeWidget`) – die unveränderte Dateibaum- und Projektzuordnungsansicht.
2. `project_names_scroll_area` (`QScrollArea`) – alle acht Namen, jeweils Label, `QLineEdit` und Verzeichnis-Icon-Button.

Die Unterfläche `project_names_scroll_content` enthält ein einziges `QGridLayout` mit den Profilen `BASIC`, `Pascal EXE`, `Pascal DLL`, `dBASE EXE`, `dBASE DLL`, `Prolog`, `Assembler`, `Lisp` (die maßgebliche Reihenfolge liefert `project_named_targets.PROFILE_FIELDS`).

Die Ausgangsaufteilung beträgt `360:190`; der Splitter-Handle ist 6 px hoch, die Unterbereiche sind nicht vollständig einklappbar. Die ScrollArea zeigt je nach Platzangebot vertikale und horizontale Scrollbars. Die Zeilen bleiben oben gruppiert, wenn der Benutzer den unteren Bereich vergrößert.

Die Kopfzeile `Projektname:` mit ihrem Dropdown verbleibt **oberhalb** des Splitters. Die Schaltflächen **Neu**, **Speichern** und **Speichern unter...** verbleiben **unterhalb** des Splitters und werden nicht mitgescrollt.

Die bestehenden Signalverbindungen für direkte Namensänderungen, den Eingabedialog per Ordnersymbol und die Projektdatei-Speicherung bleiben unverändert. Der Style für Handle, ScrollArea und Inhaltsfläche unterscheidet Dark- und Light-Mode.

## Dateianpassungen

- `d64_dism.py`: Layout in `_create_project_tab`, Theme in `_project_named_panel_stylesheet`.
- `test_stage606.py`: isolierte Widget-Hierarchie- und Signaltests ohne installierte PyQt5-Bibliothek.

## Verifikation

- Stage 606: **6/6** Headless-Widget-/Signaltests bestanden.
- Bestehende Tests: Stage 596 **11/11**, Stage 598 **9/9**, Stage 601 **7/7**, Stage 604 **5/5** bestanden.
- Komplettes `d64_dism.py`: Syntaxanalyse mit Ersatz der bereits bestehenden Python-3.15-`lazy from`-Syntax durch klassisches `from` für die lokale Python-3.13-Prüfumgebung erfolgreich.
- Archivintegrität mit `ZipFile.testzip()` verifiziert.

Eine visuelle PyQt5-Prüfung unter Windows ist in dieser Umgebung nicht möglich und steht noch aus.
