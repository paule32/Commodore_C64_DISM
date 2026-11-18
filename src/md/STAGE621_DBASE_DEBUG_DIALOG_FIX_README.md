# Stage 621 – dBASE `?` / `??` sichtbar im DEBUG-Dialog

Verbindliche Grundlage: `d64_dism_stage620.zip`.

## Bestätigte Ursache

Der aktive Compiler (`d64dbase/compiler.py`, über `from d64dbase import
compile_dbase_to_assembly` in `d64_dism.py`) erzeugt bereits den richtigen
DEBUG-Ausgabekanal für `? "Hihi"` und `?? "..."`. Die Runtime-Daten enthalten
`__dbase_output_format_screen: dd 1` und den optionalen Override `dd -1`.

**Die eigentliche Lücke lag in der Qt5-Bridge:**
`d64qt5/d64qt5_bridge.cpp` hat in `ensure_wfm_output_dialog()`
bisher normale `.prg`-Anwendungen ohne Workstation-Modus mit
`if (!g_wfm_gui_mode && !g_workstation_mode_enabled) return;` ausgeschlossen.
`DBaseQtAppendDebug()` rief den Dialog-Helfer zwar auf, aber es gab keinen
angelegten `QPlainTextEdit`, deshalb wurde die Ausgabe verworfen.

## Änderungen

1. `d64qt5/d64qt5_bridge.cpp`: Den ungewollten Guard in
   `ensure_wfm_output_dialog()` entfernen. Der vorhandene `DBaseDebugOutputDialog`
   wird nun auch für direkt gestartete normale dBASE-Programme angelegt.
2. Die Anzeige wird wie bisher bei DEBUG-Ausgabe automatisch sichtbar.
3. Die Textfarbe wird sowohl über QSS als auch über eine `QPalette` gesetzt:
   Dark Mode `#d0d0d0` auf `#101010`, Light Mode `#454545` auf `#ffffff`.
   Es handelt sich **nicht** nur um eine Farbänderung; der frühere Dialog-
   Erzeugungsfehler ist ebenfalls behoben.
4. Neuer Helfer `build_and_deploy_dbase_debug_stage621.bat`:
   baut die PE32-DLL mit `d64qt5/build_d64qt5_mingw32.bat` und kopiert
   `release/libd64_qt5.dll` nach `runtime/dbase/pe32` (oder in das als
   Parameter übergebene Ausgabe-Verzeichnis).

**Nicht geändert:** Die Standardzuordnung im aktiven dBASE-Compiler,
`SET FORMAT TO CONSOLE`, `SET DEBUG ON/OFF`, Workstation-Pipe, WFM-Dialoge
und die vorhandene Pascal-DEBUG-Ausgabe.

## So unter Windows testen

Im Stammverzeichnis der entpackten Stage-621-Dateien:

```bat
build_and_deploy_dbase_debug_stage621.bat
```

Falls das Projekt ein anderes Ausgabe-Verzeichnis besitzt, dieses als
**ein** Argument übergeben, z. B.:

```bat
build_and_deploy_dbase_debug_stage621.bat "D:\MeineProjekte\Ausgabe\pe32"
```

Benötigt: passende 32-Bit-Qt5-/MinGW-Toolchain mit `qmake`,
`mingw32-make`, `g++` und Python im PATH. **Das ZIP enthält keine neu
kompilierte Windows-DLL.** Die bereits vorhandene `libd64_qt5.dll` neben
der EXE muss wirklich ersetzt werden. Für PE32+ entsprechend mit
passender 64-Bit-Toolchain bauen und die richtige DLL einsetzen.

Als dBASE-Testprogramm:

```dbase
? "Hihi"
?? "Hallo "
? "Welt"
```

Die erwartete DEBUG-Ausgabe ist:

```text
Hihi
Hallo Welt
```

Der DEBUG-Dialog erscheint beim ersten `?` automatisch. Sollten ältere EXE-
Dateien noch die Console als Standard verwenden, das Programm mit Stage 621
neu assemblieren und linken. Bei bereits mit Stage 619/620 erstellten
Programmen, deren generierter Code tatsächlich DEBUG anspricht, ist der
Austausch der DLL der entscheidende Schritt.

Bewusste Alternativen:

```dbase
SET FORMAT TO CONSOLE
? "Konsole"
SET FORMAT TO SCREEN
? "Debug"
```

## Prüfungen

Unter Python 3.13 / Linux:

```bash
python -m pytest -q test_stage621.py test_stage619.py test_stage618.py \
    test_stage617.py test_stage616.py test_stage614.py test_stage620.py
```

Ergebnis: **63 passed**. Außerdem wurde die Ausgabe der tatsächlich
verwendeten `d64dbase.compiler.compile_dbase_to_assembly()` für `? "Hihi"`
(PE32 und PE32+) mit `DBaseQtAppendDebug` und den initialisierten
Ausgabe-Flags geprüft. Die C++-Quelllogik wird durch gezielte statische
Tests abgesichert. **Ein realer Qt5-/Windows-DLL-Build und GUI-Test konnte
in dieser Linux-Umgebung nicht durchgeführt werden.**
