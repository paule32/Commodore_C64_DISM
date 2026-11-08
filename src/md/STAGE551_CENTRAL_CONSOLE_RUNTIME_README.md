# Stage 551 – Zentrale Pascal-Konsolenruntime

Basis: `d64_dism_stage550.zip`. Keine pauschale Veränderung der anderen
Compiler-Frontends oder der bisherigen Runtime-DLL-Binärdateien.

## Architektur

Das bisherige direkte Einbetten von `AllocConsole`, `GetConsoleMode`,
`SetConsoleWindowInfo`, `WriteFile`, `wsprintfA` usw. in jedes Pascal-Modul
entfällt. Der neue, architekturgleiche Runtime-Baustein
`libd64_console.dll` verwaltet Konsolen-Handles und -Zustand. Dieser Name
wurde bewusst als **separater** Dienst gewählt, weil Stage 550 für Windows
32 Bit `libd64_runtime.dll` baut, die vorhandene 64-Bit-Buildroutine aber
`libdbase2many.64.dll` erzeugt. Mit einer eigenen DLL bleibt die ABI für
PE32 und PE32+ einheitlich, ohne eine alte Runtime-DLL durch eine inkompatible
64-Bit-Teilimplementierung zu überschreiben.

Die existierende `libd64_runtime.dll` bleibt für Objektverwaltung, Exceptions,
`_jit_malloc` und `_jit_free` notwendig. `d64_console_read_string` reserviert
Speicher ausdrücklich über den `_jit_malloc`-Export dieser DLL, damit
`_jit_free` denselben Allokator verwendet.

Die neue Console-DLL exportiert:

- `d64_console_init()` – vorhandene Konsole respektieren, andernfalls für
  ein explizit initialisierendes Hauptprogramm eine Konsole öffnen; 80×25
  nach Möglichkeit für die neu angelegte Konsole setzen; VT-Unterstützung
  aktivieren, sofern verfügbar.
- `d64_console_restore()` – alten Modus wiederherstellen; nur selbst
  erzeugte Konsole mit `FreeConsole` freigeben.
- `d64_console_write_text`, `_int`, `_double`, `_char`, `d64_console_newline`
  und `d64_console_clear` – gemeinsame Ausgabefunktionen.
- `d64_console_read_line`, `_read_int`, `_read_string` – begrenzte Eingabe,
  sichere NUL-Terminierung und keine zusätzliche, blockierende Leseoperation
  nach einem `ReadLn(Integer)`.

Importe bleiben über den Stage-541-Importmanager und die Stage-550-Include-
Auslagerung behandelbar. Nicht referenzierte Symbole sollten beim finalen
Linken anhand tatsächlich verwendeter COFF-Relocations entfallen.

Die Pascal-Codegeneratoren erzeugen weiterhin sehr kurze ABI-Adapter
(`__pas_print_string` usw.). PE32 übergibt Werte gemäß CDECL über den
Stack, PE32+ gemäß Windows-x64-ABI über RCX bzw. XMM0 mit 32 Byte Shadow
Space. Bei `Double` wird der x87-Wert zuvor in ein temporäres Stack-
DWORD-Paar abgelegt. Die bisherigen konsolenspezifischen `.bss`-Variablen
und die alten WinAPI-Aufrufblöcke entfallen.

Units und Library-Module öffnen keine eigene Konsole. Sie schreiben nur in
einen verfügbaren Host-Standardausgabekanal. `DllMain` verwendet keine
Konsoleninitialisierung.

## Erstellen unter Windows / MSYS2

**PE32:**

```bash
cd runtime/compiler
bash build.console.win32.sh
```

In einer MSYS2-MINGW32-Umgebung entsteht:
`runtime/compiler/win32/libd64_console.dll`.

**PE32+:**

```bash
cd runtime/compiler
bash build.console.win64.sh
```

In einer MSYS2-MINGW64-Umgebung entsteht:
`runtime/compiler/win64/libd64_console.dll`.

Die vorhandenen `build.win32.sh` und `build.win64.sh` rufen diese Skripte
nach dem jeweiligen Haupt-Runtime-Build auf. Weil der frühere 64-Bit-Build
nicht alle Bestandteile einer `libd64_runtime.dll` enthält, kann die neue
Console-DLL bei Bedarf auch separat erstellt werden.

Wichtig: Die DLL muss zur Architektur der erzeugten Pascal-EXE passen und
neben der EXE liegen. Die IDE versucht nach einem erfolgreichen Pascal-PE-Link
nur eine zur PE-Maschinenkennung passende DLL automatisch aus den genannten
Buildverzeichnissen dorthin zu kopieren. Findet sie keine, meldet sie die
fehlende Abhängigkeit, anstatt einen erfolgreichen Laufzeitstart zu behaupten.

## Tests

```bash
python -m pytest -q test_stage551.py
```

Die neuen AST-/Codegenerator-Tests prüfen Adapter, PE32/PE32+, ReadLn,
Importe, die weggefallene lokale Konsolenablage und die Buildskripte.

Ausgewählte Regressionstests:

```bash
python -m pytest -q test_stage551.py test_stage540.py \
    test_stage535.py test_stage543.py test_stage550.py
```

**Nicht hier getestet:** Nativer Windows-DLL-Build und der tatsächliche
EXE-Start unter Windows. In dieser Umgebung steht kein MinGW-Crosscompiler
bereit; der C++-Code wurde zusätzlich syntaktisch mit einem isolierten
Windows-API-Testheader geprüft. Es wird deshalb keine bereits fertige neue
DLL und keine gemessene Imagegrößenersparnis behauptet.

**Bewusste Abgrenzungen:** `ReadLn(a, b)` für mehrere Integer-Variablen
verwendet derzeit weiterhin die bestehenden sequenziellen Einzelaufrufe
(ein Integer je Zeile). Eine vollwertige Tokenisierung einer Eingabezeile
ist eine separate Pascal-Frontend-Erweiterung. Die bisherige 80×25-
Fenstergröße wird bei bestehenden Hostkonsolen absichtlich nicht erzwungen.
Die übernommenen Testfälle von Stage 544, die explizit die ehemaligen
`__pas_stdout_handle`-Symbole erwarten, sind als Strukturtests veraltet;
die funktionale Stage-551-Prüfung ersetzt diese Erwartungen.
