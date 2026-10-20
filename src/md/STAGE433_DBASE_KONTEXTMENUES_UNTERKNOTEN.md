# Stage 433 – Kontextmenüs für dBASE-Unterknoten

## Verbindliche Basis
`d64_dism_asm_432.zip`

## Neue erste Kontextmenüaktion

Im Projekt-Informationen-Baum unter `dBASE Programme`:

| Kontextknoten | Erste Menüaktion | Dateityp / Speicherung |
|---|---|---|
| Formulare | `Neu:  Formular-Datei` | `.wfm` / `forms` |
| Tabellen | `Neu:  Tabelle` | `.dbf` / `tables` |
| Abfragen | `Neu:  Abfrage Datei` | `.d64sql` / `queries` |
| Berichte | `Neu:  Bericht Datei` | `.d64report` / `reports` |
| Etiketten | `Neu:  Etikett Datei` | `.d64label` / `labels` |
| Archiv Dateien | `Neu:  Archiv Datei` | `.a` / `archives` |
| Windows PE32 | `Neu:  Windows PE32 Ressource Datei` | `.rc`, `.res` / Ressourcenknoten `dbase/pe32` |
| Windows PE32+ | `Neu:  Windows PE32+ Ressource Datei` | `.rc`, `.res` / Ressourcenknoten `dbase/pe64` |

Die bestehenden `Hinzufügen`, `Einträge löschen` und `Knoten öffnen/schließen` bleiben erhalten. Der bisherige `Programme`-Spezialeintrag bleibt unberührt. Nicht-dBASE-Windows-Zielknoten behalten ihre bisherigen Menüs.

## Dateidialog und Projektlogik
- Alle neuen Aktionen führen in `_new_dbase_project_file`.
- Der Dark-/Light-Mode-fähige `DBaseProjectOpenFileDialog` aus Stage 432 mit 3-Pixel-Rahmen, Verlaufstitel, Schließen-X und angepasstem Detail-Header wird wiederverwendet.
- Der Dialogtitel entspricht der jeweils angeklickten Menüaktion.
- Bereits vorhandene Dateien werden ausgewählt und eingebunden, aber nicht überschrieben.
- Neue Dateien werden im vorhandenen, zum Dateityp gehörenden Grundformat erzeugt.
- dBASE-Formulare, -Tabellen, -Abfragen, -Berichte, -Etiketten und -Archive werden in ihren vorhandenen Gruppen gespeichert; Ressourcen in den getrennten PE32-/PE32+-Ressourcen-Zweigen.
- Nach Hinzufügen: Zielknoten aufklappen, Blatt selektieren, Projekt speichern und entsprechenden Editor/Designer bzw. Archivinformationsansicht öffnen.
- `.prg`-Binärprüfung aus Stage 431 bleibt unverändert.

### Neue `.a`-Datei
- Ein neues Archiv wird **nicht** als Textdatei erzeugt, sondern als gültiges leeres `ar`-Archiv mit `b"!<arch>\\n"`.
- Das Format wurde direkt gegen die bestehende `analyze_coff_archive_bytes`-Implementierung getestet (0 Mitglieder).
- Bereits existierende Archive werden weder neu geschrieben noch verändert.

## Änderungen
- `d64_dism.py` – Gruppenkontextmenüs, dBASE-Windows-Zielmenüs, Titelübernahme und gemeinsamer Dateiauswahl-Workflow.
- `dbase_project_new.py` – Menüdefinitionen pro Unterknoten und Erzeugung gültiger leerer Archive.
- `test_stage433_dbase_group_new_menus.py` – sieben Tests einschließlich simuliertem Kontextmenü und Archivparser.

## Prüfung
- Stage 431: 7/7 Tests
- Stage 432: 4/4 Tests
- Stage 433: 7/7 Tests
- Python-Syntaxprüfung erfolgreich.
- Eine echte Windows/PyQt5-Sichtprüfung ist in dieser Umgebung nicht möglich.
