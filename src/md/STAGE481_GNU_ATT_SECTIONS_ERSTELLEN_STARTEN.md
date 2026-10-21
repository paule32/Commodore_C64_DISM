# Stage 481 – GNU AT&T .section, Formular-Designer und Erstellen → Starten

Ausgangsbasis: `d64_dism_asm_480.zip`.

## Fehlerbehebung GNU AT&T

Die Stage-480-Konvertierung behandelte interne `.section .text` / `.section .data` / `.section .bss`-Zeilen des WFM-Compilers fälschlich als Instruktionen und wandelte `.text` in einen Immediate-Operand `$.text` um. Der Rückübersetzer meldete daraufhin `AT&T-Zeile N: COFF-Sektion nicht unterstützt: $.text`.

`windows_asm_att.intel_to_att()` erkennt nun sowohl `section .text` als auch `.section .text` und überführt diese Zeilen in korrekte GNU-Abschnittsdirektiven (`.text`, `.data`, `.bss`). Der Rückübersetzer `att_to_intel()` akzeptiert zusätzlich bereits vorhandene, versehentlich erzeugte `$.text`-, `$.data`- und `$.bss`-Abschnittsangaben als Altbestandskorrektur. Die normalen `%include`- und `%define`-Direktiven bleiben unverändert.

## Menü Erstellen

Unter `AMIGA 500` steht ein Separator und anschließend **Starten**. Die Menüfolge beginnt weiterhin mit **Kompilieren + Linken**, danach **Kompilieren**.

- Beim sichtbaren **dBASE-Formular-Designer** beziehen sich `Kompilieren`, `Kompilieren + Linken` und das Architekturprofil auf den WFM-Compiler des Designers statt auf ein möglicherweise zuvor aktives, im Hintergrund verborgenes Dokument.
- `Kompilieren` ruft `compile_dbase_form()` auf und erzeugt nur ASM.
- `Kompilieren + Linken` ruft erst `compile_dbase_form()` und dann `assemble_dbase_form()` auf, ohne das Programm automatisch zu starten.
- `Starten` ruft im Formular-Designer `start_dbase_form()` auf (inklusive Prüfung/Bereitstellung der Qt-Runtime); bei anderen Quelldokumenten `_launch_assembled_document(document)`.
- `Starten` bleibt vor einem vollständigen erfolgreichen Build deaktiviert. Verfügbarkeit setzt eine existente gelinkte Datei, passendes Ziel und bei WFM einen unveränderten Formular-Snapshot voraus. Nach Compile-only oder einer Änderung wird die Berechtigung zurückgesetzt.
- Die Radio-Architekturauswahl im Designer ist mit seiner PE32-/PE64-ComboBox synchronisiert.
- Die Aktion wird beim Öffnen des Menüs und beim Wechsel des Dokument-/Designer-Zustands aktualisiert.

## Prüfungen

- `test_stage481_att_sections_build_menu.py`: GNU/Intel-Roundtrip und PE32/PE64-COFF-Linking mit `.section`, Abwärtskompatibilität mit alten `$.text`-Dateien, Reihenfolge der Menüeinträge sowie Formular-Compile/Assemble/Start mit gesperrter Startaktion vor Erfolg und nach Formularänderung.
- Python-Syntaxprüfung von `d64_dism.py` und `windows_asm_att.py`.
- Native PyQt5-/Windows-Interaktion ist unter dieser Linux-Testumgebung nicht verfügbar; Tests verwenden AST-extrahierte Methoden und Testattrappen der QAction-Steuerung.
