# Stage 675: `libd64_console.dll` → `libd64_qt5.dll`

Basis: Stage 674. Ziel: Die elf C-ABI-Exporte der früheren Pascal-Konsolenruntime werden gemeinsam mit der Qt5-Bridge in **einer** Windows-DLL gebaut. Für neu übersetzte Pascal-PE32-/PE32+-Projekte ist `libd64_console.dll` nicht mehr erforderlich.

## Umsetzung

- **`d64qt5/d64_pascal_console.cpp`** enthält die bisherige Konsolenimplementierung (Konsolenstart/-restore, Text, Integer, Double, Char, Zeilenumbruch, Löschen, Lesen von Text/Integer/String). Das ursprüngliche `cdecl`-ABI und die Funktionsnamen bleiben unverändert.
- **`d64qt5/d64qt5_bridge.pro`** baut die neue C++-Datei im Windows-Zweig direkt in die Qt5-DLL ein. Den Build mit `qmake` *neu* erzeugen, nicht ein altes `Makefile.Release` aus dem Archiv wiederverwenden.
- **`d64qt5/d64qt5_bridge.def`** exportiert die elf Namen mit den neuen Ordinals **1022–1032**. Die bisherigen Ordinals 1–64 und 1001–1021 bleiben bestehen; der ursprüngliche 64er-ABI-Hash ist unverändert.
- **`d64qt5/d64qt5_bridge.h`** enthält die C-ABI-Prototypen.
- **`c64pascal/compiler.py`** importiert dieselben Symbole künftig aus `libd64_qt5.dll` statt `libd64_console.dll` (PE32 und PE32+).
- **`pascal_console_dependencies.py`, `d64_dism.py`** prüfen die passende Architektur und erforderlichen Exporte der Qt5-DLL und stellen sie im Ausgabeordner bereit. Alte Objekt-/DLL-Imports auf `libd64_console.dll` werden als veraltet gemeldet, damit kein scheinbar erfolgreicher Build mit der alten Abhängigkeit ausgeliefert wird.
- **`runtime/compiler/build.console.win32.sh`** und `build.console.win64.sh` sind Kompatibilitätswrapper und rufen jetzt den gemeinsamen Qt5-Build auf. Sie erzeugen keine separate Console-DLL mehr.

## Exportierte ABI

| Ordinal | Export |
| ---: | --- |
| 1022 | `d64_console_init` |
| 1023 | `d64_console_restore` |
| 1024 | `d64_console_write_text` |
| 1025 | `d64_console_write_int` |
| 1026 | `d64_console_write_double` |
| 1027 | `d64_console_write_char` |
| 1028 | `d64_console_newline` |
| 1029 | `d64_console_clear` |
| 1030 | `d64_console_read_line` |
| 1031 | `d64_console_read_int` |
| 1032 | `d64_console_read_string` |

## Build und Umstieg unter Windows

Für jede Architektur in der **entsprechenden MSYS2-Shell (MINGW32 bzw. MINGW64)**:

```bash
cd d64qt5
python3 generate_runtime_abi.py
qmake d64qt5_bridge.pro CONFIG+=release
mingw32-make release
```

Danach `d64qt5/release/libd64_qt5.dll` in den zur Architektur passenden Programm-Ausgabeordner übernehmen. Ein Build für PE32 und PE32+ muss mit jeweils passender Toolchain erfolgen; 32-/64-Bit-DLLs sind nicht austauschbar.

Alle eigenen Pascal-Programme, Units, Runtime-Bibliotheken und COFF-Objekte, die noch `libd64_console.dll` importieren, **neu kompilieren und linken**. Erst nach Prüfung der tatsächlichen Importtabelle die alte DLL aus der Auslieferung entfernen. Das bisherige `libd64_runtime.dll` bleibt u. a. für `_jit_malloc` beim `d64_console_read_string` erforderlich.

**Wichtige Abgrenzung:** Die dBASE-spezifische `c64_dbase_runtime.dll` und deren `DBaseConsoleWrite`-ABI sind andere Komponenten und wurden nicht ersetzt. Die frühere Stage-673-/674-Qt5-Ausgabe (`DBaseQtRuntimeWrite` / `DBaseQtRuntimeWriteText`) bleibt unverändert. Qt5-Abhängigkeiten der Qt5-DLL müssen natürlich weiterhin vorhanden sein.

## Tests und Grenzen

- **7 neue Stage-675-Tests:** Export-Namen/Ordinals, Compiler-Importzuordnung, Runtime-Validierung, stale DLL erkennen; ein echter nativer C++-Test der integrierten Konsolenausgabe und `ReadInt`, der Windows-APIs testweise nachbildet; eigene reale COFF32-/COFF64- und PE32-/PE32+-Linktests bestätigen, dass nur `libd64_qt5.dll` und nicht `libd64_console.dll` importiert wird.
- **10 bestehende Stage-673/674-Tests:** O1/O2-ABI und Generator-Regressionen.
- **4 weitere Stage-674-COFF-Tests:** O2-Link mit separaten Programmobjekten.
- Die Python-Syntaxprüfungen (Hauptprogramm: `lazy import` für den lokalen Python-3.13-Parser vorübergehend normalisiert) und `bash -n` der Buildskripte sind erfolgreich.
- **Nicht durchgeführt:** echter Windows-MinGW-Qt5-Neubau, PE32-/PE32+-Ausführung unter Windows und vollständiger Pascal-Frontend-Test. Die lokale ANTLR-Python-Runtime 4.9.3 ist nicht kompatibel mit den aktuell generierten Pascal-Lexer-Dateien. Daraus wird **keine** erfolgreiche Windows-Ausführung abgeleitet.
