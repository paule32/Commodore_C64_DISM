# Stage 669 – dBASE-COFF-Importkorrektur und projektbezogene Editorziele

**Verbindliche Ausgangsbasis:** `d64_dism_stage668.zip`

## Behobene Fehlermeldung

`COFF32-Linker: externe Symbole nicht aufgelöst: __dbase_obj_jit_object_instance_new`

`__dbase_obj_jit_object_instance_new` ist der lokale Assemblername für den C-Runtime-Export
`jit_object_instance_new` in `libd64_runtime.dll`. Implementiert ist er in
`runtime/jitObject.cc`, exportiert durch `runtime/win32/libd64_runtime.def`.
Der Import im generierten Assembler lautet:

```asm
import __dbase_obj_jit_object_instance_new, "libd64_runtime.dll", "jit_object_instance_new"
```

Das eigentliche Problem hatte zwei Ebenen:

1. Ein `Programme`-Dokument konnte nach einem Wechsel der Projektbaum-Auswahl beim
   Betätigen von **Assemble** in den allgemeinen PE-EXE-Linkpfad fallen.
   Die Rolle des Dokuments wird nun über die Quelle und ihre Mitgliedschaft in
   `dBASE Programme -> Programme` beziehungsweise `Module` bestimmt, nicht bloß
   über die derzeit im Baum markierte Zeile.
2. Der Compiler platzierte den Laufzeitimport für die VMT-Objektfabrik unterhalb
   `; __d64_dbase_startup_begin__`, während die Klasse später eine Referenz auf
   diesen Import behielt. Beim Entfernen des Startcodes wurde bisher auch die
   Importdeklaration entfernt. `strip_program_entry_assembly()` bewahrt nun
   Importdeklarationen aus dem entfernten Block auf und entfernt lediglich den
   Einstiegscode und dessen `_start`-Symbol.

**Erwarteter Ablauf:** In `Programme` mit Windows PE32/PE32+ kompilieren und im
Assembler-Tab **Assemble** betätigen. Es wird eine reine, relocierbare COFF32-
oder COFF64-`.o` erzeugt, auch wenn Klassen auf Runtime-Symbole verweisen.
Der **Link** erfolgt ausschließlich über das ausgewählte `Module`.

## Compiler-/Assemblerziel in der `.pro`-Datei

Die beiden synchronisierten Ziel-ComboBoxen im Quell- beziehungsweise
Assembler-Editor (z. B. `Windows PE32` oder `Windows PE32+` rechts neben Start)
werden **pro Quelldatei und Projekt** gesichert. Bei Änderung wird das Projekt
als geändert markiert und, sofern es bereits gespeichert ist, aktualisiert.
Beim Wiederöffnen des Projekts beziehungsweise des Quelldatei-Tabs wird die
passende Auswahl wiederhergestellt.

Beispiel für den neuen optionalen INI-Abschnitt:

```ini
[Settings.EditorCompilerTargets]
Title = Compiler- und Assemblerziele der Quelldateien
Item0001 = {"path":"Module/App001.prg","target":"pe32"}
Item0002 = {"path":"Programme/Tools.prg","target":"pe64"}
```

Die Pfade sind nach Möglichkeit relativ zum Speicherort der `.pro`-Datei.
Ältere Projekte ohne diesen Abschnitt bleiben ladbar. Unterstützte Werte:
`c64`, `amiga`, `pe32`, `pe64`, `linux32`, `linux64`.
Die kleinen, isoliert testbaren INI-Helfer liegen in
`project_editor_targets.py`.

## Modifizierte Dateien

- `d64_dism.py` – projektbasierte dBASE-Dokumentrolle, Ziel-ComboBox-Persistenz
- `dbase_module_coff.py` – bewahrt notwendige Runtime-Importdeklarationen
- `project_editor_targets.py` – neues, Qt-unabhängiges Format für Projektziele
- `test_stage669.py` – Regressionstests

## Durchgeführte Prüfungen

- Stage-669-Tests: **8 bestanden** (getrennte Läufe von 4 + 4)
- Stage-596/597-Tests: **19 bestanden**
- Stage-668-Tests (gezielte Auswahl und reale PE32/PE32+-Links): **8 bestanden**
- Stage-667-Strukturtests: **2 bestanden**
- Zusammen **37 gezielte Tests** (kein vollständiger Gesamttest).
- Verifiziert sind auch echte dBASE-Klassencode-Objekte mit
  `__dbase_obj_jit_object_instance_new` für COFF32 und COFF64.

**Nicht durchgeführt:** nativer Windows-PyQt5-Bedientest, komplette historische
Test-Suite. `libd64_qt5.dll` wurde nicht geändert und muss nicht neu gebaut
werden. Nach dem Update die betroffenen Programmdateien neu kompilieren und
assemblieren, damit keine alten `.o` ohne Runtime-Import benutzt werden.
