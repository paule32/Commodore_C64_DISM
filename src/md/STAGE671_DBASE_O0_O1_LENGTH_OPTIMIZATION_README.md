# Stage 671 – dBASE O0/O1 Längenoptimierung

**Verbindliche Basis:** Stage 670 (`d64_dism_stage670.zip`).

## Bedienung

In **Projekt-Einstellungen → Windows → 32-Bit / 64-Bit → Compiler → dBASE → Optimierung** erscheint rechts als **erste GroupBox**:

> **Optimierungsstufen:**
> - O0  -  keine Optimierung (Standard)
> - O1  -  Längen Optimierung

PE32 und PE32+ erhalten **unabhängige** Einstellungen. Ändern der Stufe macht bestehende dBASE-Assembler-/Link-Ergebnisse ungültig. Quelle erneut kompilieren, assemblieren, dann linken.

Die `.pro`-Datei speichert den Wert in:

```ini
[Settings.Windows.32Bit.Compiler.dBASE.Optimierung]
OptimizationLevel = O1

[Settings.Windows.64Bit.Compiler.dBASE.Optimierung]
OptimizationLevel = O0
```

Fehlende oder ungültige Angaben ergeben O0. Der Status wird beim neuen Projekt und Schließen eines Projekts auf O0 zurückgesetzt.

## Ausführung

Eine neue Datei `dbase_size_optimizer.py` optimiert nur mit O1. Bei O0 bleibt der ASM-Text bytegetreu unverändert. Die neue Längenstufe entfernt nur eindeutig redundante Maschineninstruktionen in `.text`, nicht in `.data` oder `.bss`:

1. `jcc L1; jmp L2; L1:` → invertierter `jcc L2; L1:`.
2. Ein unbedingter Sprung direkt vor einem anderen unbedingten Sprung ohne Label wird verworfen, weil die zweite Instruktion unerreichbar ist.
3. `jmp L; L:` wird durch direkten Fallthrough ersetzt.

Das betrifft ausschließlich vom Compiler erzeugtes dBASE-Intel-ASM und keine Pascal-/PROLOG-Compiler. Alle Labels bleiben stehen. Entfernte Instruktionen werden in derselben Zeile durch Kommentare ersetzt, damit Source-Map/Fehlerzeilen erhalten bleiben.

**Wichtig:** `mov eax,eax` wird absichtlich nicht gelöscht: Auf x86-64 löscht dies die oberen 32 Bit von RAX. Auch GUI-Aufrufe, FPU-/Exception-Code, Runtime-Imports, VMTs und Aufrufkonventionen werden nicht spekulativ verändert.

Die bisherigen separat konfigurierbaren Stage-609-Peephole-Optionen werden im dBASE-Compiler/Linkpfad bei O0 unterdrückt. Bei O1 dürfen sie zusätzlich wirken, sofern deren Checkboxen aktiviert sind; für Pascal bleibt ihr Verhalten unverändert.

## Hochgeladene Probe `App001.generated.pe32.asm`

Die Prüfung des vom Benutzer hochgeladenen Assemblertexts (1110 Zeilen) ergibt bei O1 **2 entfernte Maschineninstruktionen**:

- Direkt nach `jmp __dbase_catch_dispatch_8` ist `jmp __dbase_exception_finally_9` unerreichbar.
- `je __dbase_catch_handler_38; jmp __dbase_catch_next_39; __dbase_catch_handler_38:` wird zu `jne __dbase_catch_next_39; __dbase_catch_handler_38:`.

Die kontrollierte COFF-Testfolge erzeugt PE32 und PE32+ jeweils von 31 Bytes `.text` bei O0 auf 21 Bytes bei O1. Die konkrete Byte-Ersparnis im hochgeladenen *vollständigen* Programm konnte mangels zugehöriger `App001.generated.pe32.extern.inc` nicht als ausführbare EXE verifiziert werden. Eine aus dem Upload abgeleitete O1-Vorschau liegt im Archiv unter `examples/dbase/App001.generated.pe32.O1.asm` und bleibt auf die zur Quelldatei passende Include-Datei angewiesen.

## Dateien

- `d64_dism.py`: neue Gruppierung, GUI-Callbacks, projektbezogene `.pro`-Persistenz und O0/O1-Integration vor der Import-/ASM-Ausgabe; Bau-Snapshots prüfen auch den Wechsel der Optimierungsstufe.
- `dbase_size_optimizer.py`: eigenständige, getestete O1-Optimierung.
- `test_stage671.py`: Regressionen inkl. INI-Roundtrip und echten PE32-/PE32+-Assembler-Läufen.
- `tests/fixtures/App001.generated.pe32.asm`: Regressionsvorlage aus dem Benutzer-Upload.

## Tests / Grenzen

- 8 neue Stage-671-Tests bestanden.
- 12 vorhandene Stage-609-Tests bestanden (zuzüglich 8 Untertests).
- 7 Stage-670-Tests bestanden.
- 5 gezielte Stage-668-Tests sowie 2 Stage-669-Tests bestanden.
- Große historische Linker-/GUI-Gesamtläufe wurden wegen des Zeitlimits **nicht vollständig** abgeschlossen. Keine native PyQt5-GUI-Prüfung unter Windows in dieser Umgebung.

Diese Optimierung ist eine vorsichtige erste O1-Stufe, kein globales Link-Time-Optimizing oder semantisches Dead-Code-Elimination. Die sichtbare ASM-Textdatei kann wegen Kommentaren ungefähr gleich lang bleiben, auch wenn die emittierten Maschineninstruktionen kürzer werden.
