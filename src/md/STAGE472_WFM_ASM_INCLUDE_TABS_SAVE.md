# Stage 472 – dBase/WFM: Assembler-Tabs und Include-Dateien

**Verbindliche Basis:** `d64_dism_asm_471.zip` (nur dieser Entwicklungszweig).

## Darstellung

- Im WFM-Tab `Quellcode` bleibt oben der horizontale Splitter aus Quellstruktur und WFM-Quelltext und unten der verstellbare vertikale ASM-Bereich.
- Im unteren Bereich ist jetzt `QTabWidget#dbase_form_assembly_tabs`. Der erste Tab **Generierter Assembler** enthält die ursprüngliche `generated_assembly_editor_container`-Instanz mit Syntaxhervorhebung, MiniMap und Quellzeilennavigation. Er besitzt keinen Schließen-Button.
- Zusätzliche Tabs besitzen `SourceEditorWithMiniMap`, eigenen Editor, Assembler-Highlighter sowie einen rechts am Tab angebrachten Schließen-Button.

## Kontextmenü

- Rechtsklick **auf den Dateinamen** in `%include "filename"` öffnet `In neuen Tab öffnen | --- | Hilfe`.
- Die Dateisuche verwendet strikt 1) das Arbeitsverzeichnis (`current_directory`), 2) `Compiler -> Eingabe-Verzeichnis` des aktuellen Windows-Ziels (PE32/PE64). Verschachtelte relative Namen sind zulässig.
- Ein bereits geöffneter Dateipfad wird in den Vordergrund geholt (kein zweiter Tab).
- Nicht gefundene und nicht lesbare Dateien werden mit der bestehenden Dark-/Light-Mode-Fehlermeldung (`show_error()`) angezeigt.

## Speichern

- Hauptmenü **Speichern**: zunächst die aktive WFM-Datei über `save_dbase_form`, anschließend **jeden** unteren ASM-Tab auf seinen eigenen Dateipfad; neue Tabs rufen erst einen Speichern-unter-Dialog auf. Die von `DocumentEditor` generierte ASM-Datei wird über `generated_assembly_path` gespeichert.
- `Strg+S` im WFM-Quelltext: `.wfm` über `dbase_form_current_path` speichern. `Strg+S` in einem ASM-Editor: alle geöffneten Dateien speichern. Das Hauptmenü speichert ebenfalls alle.
- Hauptmenü **Speichern unter ...**: wenn zuletzt ein ASM-Editor aktiv war, wird nur dieser Tab gespeichert; andernfalls das WFM-Formular.
- Bei abweichendem Dateinamen erscheinen `Umbenennen` (neue Datei schreiben, bisherigen Pfad entfernen), `Beibehalten` oder `Abbrechen` (beide: unter bisherigem Tab-Pfad speichern). Abbrechen im Dateiauswahldialog behält den bisherigen Pfad ebenfalls, sofern vorhanden.
- Ein neu angelegter Tab `Unbenannt.asm` wird intern als noch ungespeichert markiert und erzwingt beim ersten Speichern die Dateiauswahl.
- Geladene Include-Dateien behalten ihre Zeichenkodierung und CRLF-/LF-Zeilenenden; gespeichert wird über eine temporäre Datei und `os.replace`.
- Die `.wfm`-Datei wird weiterhin aus dem bereits vorhandenen `dbase_form_current_path` bestimmt, der beim Öffnen des Formular-Knotens im Projekt-Tree gesetzt wird.

## Neue Dateien

- `wfm_asm_tab_support.py`: pure Hilfsfunktionen für Include-Parsing und Suchreihenfolge
- `test_stage472_wfm_asm_include_tabs.py`: eigene Stage-472-Regressionstests

## Prüfumgebung

Python-Syntaxprüfung, Include-Resolver-Tests, Code-Strukturtests sowie vorhandene Assembler-/WFM-Tests. Die Windows-Qt5-Interaktion muss auf dem Zielsystem bestätigt werden: PyQt5 ist in der hier verfügbaren Laufzeitumgebung nicht installiert.
