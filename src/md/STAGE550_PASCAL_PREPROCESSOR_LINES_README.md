# Stage 550 – Pascal: Use Pre-processor Lines

**Verbindliche Basis:** `d64_dism_stage549.zip`.

## Neue Projekteinstellung

Für **Windows → 32-Bit → Compiler → Pascal → Importe / Cache** und
**Windows → 64-Bit → Compiler → Pascal → Importe / Cache** ist die neue
Checkbox **Use Pre-processor Lines** hinzugekommen.

- Vorgabe: **aus** (kompatibel zu Stage 549).
- Nur sinnvoll, und in der GUI nur bedienbar, wenn **Import-Deklarationen in .inc auslagern** eingeschaltet ist.
- PE32 und PE32+ werden unabhängig in der `.pro`-Datei gespeichert.

Beispiel:

```ini
[Settings.Windows.32Bit.Compiler.Pascal.Imports]
Externalize = true
UsePreprocessorLines = true

[Settings.Windows.64Bit.Compiler.Pascal.Imports]
Externalize = false
UsePreprocessorLines = false
```

## ASM-Ausgabe

Bisher behielt der externe Import-Manager die Zahl der physischen ASM-Zeilen
bei und ersetzte entfernte Importdeklarationen durch Leerzeilen. Bei aktivierter
neuer Option werden zusammenhängende Import-/Extern-Deklarationen (einschließlich
Stage-541-Kommentaren über unbenutzte/duplizierte Deklarationen) kompakt
zusammengezogen:

```asm
bits 32
global _start
entry _start
%include "test_raise.generated.pe32.asm.imports.inc"
%line 27
_start:
    ...
```

**Wichtig:** `%line 27` setzt die *nächste* Zeile auf die **logische**
Originalzeilennummer 27; dies ist die NASM-Semantik. Die Ziffer wird automatisch
berechnet und ist nicht fest im Compiler kodiert. Liegt beispielsweise das
ursprüngliche `_start:` auf Zeile 27, wird nach dem ersetzten Importblock
`%line 27` geschrieben.

Die `.imports.inc` enthält weiterhin die ausgelagerten aktiven `extern`-/`import`-
Deklarationen. Nicht benötigte Deklarationen bleiben entfernt, sofern
„Nicht verwendete Imports entfernen“ aktiviert und die Verwendung eindeutig ist.
Bei nicht zusammenhängenden Blöcken erscheinen aus Gründen korrekter
Zeilenpositionen mehrere `%line`-Direktiven; echter Code und erklärende
Kommentare dazwischen werden nicht gelöscht.

## Integrierter COFF32-/COFF64-Assembler

Neue Datei: `windows_asm_line_directives.py`.

`d64_dism.py::_preprocess_windows_assembly()` verarbeitet `%line N` sowie die
NASM-Variante `%line N+M [filename]`, bevor das vorhandene `%include`/
Makro-Preprocessing ausgeführt wird:

1. `%line` wird aus dem Assembler-Input entfernt, da es **kein Maschinenbefehl** ist.
2. Das physische Zeilenlayout bleibt für das Makro-Preprocessing erhalten.
3. Die vom bestehenden Preprocessor gelieferten Quellpositionen werden anhand
   des `%line`-Werts auf **logische** Zeilennummern abgebildet.
4. Fehlermeldungen aus späterer IA-32-/AMD64-Assemblierung verwenden die
   logische Position. Zeilennummern in der eingebundenen `.inc` werden nicht
   überschrieben.

Die Vorverarbeitung unterstützt die neue Direktive im Haupt-ASM-Quelltext;
individuelle `%line`-Anweisungen innerhalb beliebiger fremder Include-Dateien
sind nicht Bestandteil der neuen Funktion.

## Parallel-Compiler

`pascal_parallel_build.py` erhält den neuen Job-Wert
`import_use_preprocessor_lines`. Die Include-Auslagerung erfolgt dort mit
demselben Schalter wie beim normalen IDE-Compile.

## Tests

```bash
python -m unittest -q test_stage550
```

**11 von 11 neuen Tests erfolgreich**, darunter Importkompaktierung,
Stage-541-Pruning, Quellzeilen-Zuordnung, `.pro`-Persistenz und Anbindung
an den Parallel-Worker. Gezielte Stage-541-Tests bestanden ebenfalls; ein
umfangreicher kombinierter älterer Testlauf hat hier das Zeitlimit erreicht.

**Nicht geprüft:** Nativer Windows-Build mit dem vollständigen Qt/Assembler-
Setup. Die Stage-549-ZIP enthält die Quellabhängigkeit `windows_asm_macros.py`
nicht; die Einbindung wurde deshalb mit einem Preprocessor-Test-Doppel
geprüft, nicht mit einer vollständigen Windows-COFF-Datei.

## Betroffene Dateien

- `d64_dism.py` – GUI, `.pro` und ASM-Vorverarbeitung
- `pascal_import_manager.py` – optionale kompakte `.inc`-Ausgabe
- `pascal_parallel_build.py` – Weitergabe der Compileroption
- `windows_asm_line_directives.py` – neue `%line`-Quellpositionsabbildung
- `test_stage550.py` – neue Regressionstests

Die bestehenden CES-, Stack-Cookie-, Pascal-Klassen-/DLL- und
Import-Cache-Funktionen sind unverändert.
