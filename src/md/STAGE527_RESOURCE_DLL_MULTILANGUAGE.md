# Stage 527 – Mehrsprachige Ressourcen-DLL (RC / RES / PE32 / PE32+)

Basis: aktuelles GitHub-Repository paule32/Commodore_C64_DISM, main, 2026-11-01.
Entwickelt als separater Feature-Branch.

## Bedienung

1. Ressourcen-Editor öffnen und ein RC-Projekt laden.
2. Im Ressourcenbaum eine Ressource auswählen.
3. In der Vorlagen-Symbolleiste **Sprachvariante hinzufügen ...** wählen.
4. Eine neue Sprache auswählen, beispielsweise ENU (0x0409) zusätzlich
   zu DEU (0x0407).
5. Die neue RC-Deklaration im Quelltext übersetzen und speichern.
6. Mit **win32 DLL** oder **win64 DLL** eine gemeinsame DLL erzeugen.

Die Ressourcenliste zeigt für dieselbe ID mehrere Sprachen. Die neue
**Sprache**-Eigenschaft wirkt auf eine ausgewählte Ressource statt global
auf alle geladenen Ressourcen.

Der Windows-Ressourcencompiler besitzt bereits die passende Verzeichnisstruktur
Typ -> Ressourcen-ID -> LANGID. Binär-RES, COFF und DLL tragen die LANGIDs.

Alle Änderungen in RC-Quelltexten werden vor Übernahme probe-kompiliert und
gegen die bisherigen Ressourcenidentitäten/Bytes geprüft. Bei Fehlern oder
Mehrdeutigkeiten bleibt das Original unverändert.

Bei RES-Projekten können Sprachen als zusätzliche Einträge gespeichert werden.

## Einschränkungen

- Beim Anlegen einer Sprachvariante werden vorhandene Texte zunächst kopiert.
  Die Übersetzungen werden anschließend im Quelltext vorgenommen.
- Zusammengefasste STRINGTABLE-Blöcke können mehrere RT_STRING-IDs erzeugen.
  Einzelne Sprachen solcher zusammengefasster Blöcke müssen ggf. direkt
  mit LANGUAGE/STRINGTABLE bearbeitet werden.
- Ressourcen aus #include-Dateien, die keine eindeutig bearbeitbare
  Deklaration in der geöffneten RC-Datei besitzen, bleiben unverändert.
- Der klassische ASCII-/UTF-8-Modus aus Stages 514-520 kann spezielle
  D64_CP-Ressourcentypen ausgeben. Für native Windows LoadString/LoadMenu
  wird die Unicode-Option empfohlen.
- Die 14-Pixel-Abstände der vorhandenen DLL-Schaltflächen bleiben erhalten.

## Dateien

src/resource_multilang.py - sichere per-Ressource RC-Sprachanpassung
src/resource_multilang_integration.py - Toolbar-Aktion beider GUI-Editoren
src/__main__.py - Aktivierung vor dem d64-Hauptfenster
src/windows_resource.py - RC-Kompilierung aus ungespeichertem Quelltext
src/windows_resource_editor.py - eigenständige Editor-Klasse
src/tests/test_stage527_multilingual_dll.py - Sprach- und Binary-Tests
src/examples/windows_resource_multilingual/demo.rc - Beispielprojekt

Testaufruf aus dem Repository:

    python -m pytest -q src/tests/test_stage527_multilingual_dll.py

Native PyQt-Windows-Klicktests bleiben zusätzlich sinnvoll.
