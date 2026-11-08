# Stage 544 – DLL-/UNIT-Konsole: fehlende BSS-Symbole

Basis: `d64_dism_stage543.zip`. Änderung ausschließlich im Pascal-Codegenerator plus neue Regressionstests.

## Problem

Beim Kompilieren von `library Runtime; uses System, Windows;` wurden in PE32-Ausgabehelfern (`__pas_write_cstring`) Relocations auf `__pas_stdout_handle` und `__pas_written` erzeugt. Diese BSS-Symbole wurden ausschließlich bei `console_mode=True` reserviert, während DLLs und Units standardmäßig `console_mode=False` verwenden. Abhängige Units mit `WriteLn` können die Druckhelfer trotzdem erzeugen. Der COFF32-Linker meldet daher `externe Symbole nicht aufgeloest: __pas_written, __pas_stdout_handle`.

## Änderungen

- `c64pascal/compiler.py`: gemeinsame Bedarfsermittlung `_needs_console_output_storage()` (für PE32 und PE32+).
- `stdout_handle`, `written`, `format_buffer`, `char_buffer` und auf PE32+ auch `write_ptr` werden in `.bss` reserviert, sobald der Generator eine Druck- oder Range-Fehler-Routine erzeugt – unabhängig vom Konsolenmodus.
- Für Units und DLLs ermittelt `write_cstring` den vom Hostprozess bereitgestellten Standardausgabe-Handle über `GetStdHandle(STD_OUTPUT_HANDLE)`. Der String-Zeiger wird über diesen Aufruf erhalten. Ein zusätzliches `AllocConsole()` in DLL/Unit wird **nicht** aufgerufen.
- Für Units (PE32/PE32+) und DLLs (PE32+) werden die nötigen WinAPI-`extern`-Deklarationen bereitgestellt. Die bereits vorhandenen PE32-DLL-Deklarationen bleiben erhalten. Nicht referenzierte `extern`-Namen erzeugen im COFF-Linker keine unnötigen Import-Einträge.
- Neue Datei `test_stage544.py`: sieben Regressionstests für Library/Unit in PE32 und PE32+, BSS-Symbole, Ausgabe-Handle, unveränderte Programminitialisierung und keine unnötigen BSS-Daten in Modulen ohne Druckcode.

## Teststatus

- `python -m unittest -q test_stage535 test_stage537 test_stage538 test_stage540 test_stage542 test_stage543 test_stage544` – **42 erfolgreich**.
- `python -m unittest -v test_stage544 test_stage543 test_stage542 test_stage540` – **24 erfolgreich** (Teilmenge der obigen Tests).
- Ein umfassender älterer Testsammellauf mit `test_stage541` hielt bei einem aufwendigen `.pro`-/GUI-Test an und wurde nicht vollständig abgeschlossen. Keine Erfolgsbehauptung für diesen Lauf.
- Quellcode-Syntax mit `python -m py_compile c64pascal/compiler.py` geprüft.
- **Noch ausstehend:** vollständiger nativer PE32-/PE32+-Windows-Library-Build und Test des Standardausgabe-Handles in einem DLL-Hostprozess. Für echte DLLs ohne Konsole kann `GetStdHandle` einen ungültigen Handle liefern; Windows `WriteFile` schlägt dann fehl, ohne eine Konsole zu erzwingen.

## Windows-Praxistest

1. Stage-544-Quellen einspielen; das Problem wird im Compiler behoben, eine neue Runtime-DLL ist nicht erforderlich.
2. Units aus `uses System, Windows` und `library Runtime` sauber neu kompilieren, damit keine alten COFF-/PUI-Artefakte verwendet werden.
3. Den DLL-Build ausführen. Die beiden zuvor fehlenden Symbole müssen in `.bss` des erzeugten Assembler-/COFF-Moduls vorhanden sein.
4. DLL in einem Hostprozess mit Standardausgabe testen. Das vorherige COFF32-Linkerproblem muss verschwunden sein; über das Verhalten der restlichen DLL-Exports trifft dieser Patch keine Aussage.
