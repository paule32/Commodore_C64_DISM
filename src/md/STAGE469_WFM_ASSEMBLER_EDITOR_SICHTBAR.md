# Stage 469 – WFM-Assembler unter Quellstruktur und Quelltext sichtbar

**Basis:** `d64_dism_asm_468.zip`.

## Behobener Fehler

Stage 467 hatte einen vertikalen Splitter zwar angelegt, allerdings die zuvor aus
`DocumentEditor.views` (`QTabWidget`) entfernte `generated_assembly_page`
wiederverwendet. Beim Entfernen aus einem TabWidget und `setParent(None)` kann
Qt diese Seite ausgeblendet lassen, obwohl sie anschließend in einem QSplitter
liegt. Dadurch war der Assembler-Editor im Tab „Quellcode“ nicht sichtbar.

## Änderung in d64_dism.py

- Die entfernte `generated_assembly_page` bleibt als versteckter Platzhalter
  beim internen Build-Document; kein eigener Assembler-Tab wird wiederhergestellt.
- Der bestehende `generated_assembly_editor_container` (Editor und MiniMap) wird
  aus der alten Seite ausgehängt und in einen neuen `dbase_form_assembly_host`
  mit der Überschrift „Assembler“ verschoben. Alle bestehenden Signale,
  Syntaxhervorhebung, F2-Build- und Quellzeilen-Klickfunktionen bleiben am
  ursprünglichen Editor-Objekt erhalten.
- Der vertikale Splitter `dbase_form_source_assembly_splitter` enthält nun:
  1. oben `dbase_form_source_splitter` mit `Quellstruktur | Quellcode`,
  2. unten `dbase_form_assembly_host` mit Assembler-Editor.
- Editor-Container und Host werden nach dem Umhängen explizit mit `show()`
  sichtbar gemacht. Beim Wechsel zum Quellcode-Tab wird die Sichtbarkeit
  ebenfalls sichergestellt.
- Der Griff bleibt 7 Pixel breit; beide Bereiche haben eine Mindesthöhe und
  bleiben frei mit der Maus in ihrer Höhe veränderbar. Beim Wechsel des Tabs
  werden vom Benutzer gewählte Splittergrößen nicht überschrieben.

## Tests

- Neuer Test: `test_stage469_wfm_assembler_visible_below_source.py`
  (3 Struktur- und Regressionstests).
- Der bisherige Layouttest aus Stage 467 wurde auf den neuen ASM-Host
  aktualisiert.
- Insgesamt 105 WFM-/Designer-/Compiler-Regressionstests bestanden, darunter
  PE32/PE32+-Assembler- und Linkprüfungen.
- Kein nativer PyQt5-/Windows-GUI-Test in dieser Laufzeitumgebung verfügbar.
