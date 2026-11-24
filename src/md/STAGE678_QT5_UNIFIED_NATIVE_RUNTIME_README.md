# Stage 678 – Native dBASE-/Pascal-Runtime in `libd64_qt5.dll`

## Anlass

Stage 675 hatte `libd64_console.dll` in die Qt5-Bridge integriert; Stage 676 hatte dagegen die ehemalige `c64_dbase_runtime.dll` in `libd64_runtime.dll` eingegliedert. Daher hatten neu generierte dBASE-Programme noch einen Import auf `libd64_runtime.dll` und meldeten beim Start unter Windows, dass diese DLL fehlt.

**Ziel Stage 678:** Alle bislang über `libd64_runtime.dll` bereitgestellten nativen JIT-, Speicher-, Objekt-, Klassen-, Exception-, Pascal- und dBASE-Konsolenfunktionen werden als statisch gelinkte Module Bestandteil von `libd64_qt5.dll`. Neu generierte Programme benötigen diese eigenständige Runtime-DLL nicht mehr.

## Änderungen

- `d64dbase/compiler.py` und `d64dbase/object_abi.py`: interne native DLL-Imports auf `libd64_qt5.dll` umgestellt, inklusive `_jit_*`, Objekt/VMT-Funktionen und dBASE-Konsolenschreiber.
- `c64pascal/compiler.py`, `System.Objects.pui`, `System.Strings.pas` und Runtime-Metadaten: Pascal-Runtime-Importe auf `libd64_qt5.dll` umgestellt.
- `d64qt5/d64qt5_bridge.def`: bisherige Exportnamen für die native Runtime mit neuen Ordinals ab 2000 bereitgestellt. Die zuvor bestehenden Qt5-Ordinals und der Hash der 64 Kernexports bleiben unverändert.
- `d64qt5/d64qt5_bridge.cpp`: `DBaseQtRuntimeWrite` nutzt `DBaseConsoleWrite` jetzt direkt; dynamisches `LoadLibraryA/GetProcAddress` der alten Runtime entfällt.
- `d64qt5/d64_pascal_console.cpp`: `d64_console_read_string` nutzt `_jit_malloc` direkt.
- `runtime/build.qt5_embedded.win32.sh`: baut aus dem freestanding Runtime-Quellcode und den NASM-Routinen ein statisches COFF-Archiv `runtime/win32/libd64_qt5_native.a`, ohne eigenen DLL-Einstiegspunkt.
- `d64qt5/d64qt5_bridge.pro`: baut das Archiv vor dem Qt5-DLL-Link und bindet es vollständig mit `--whole-archive` ein. Kollisionen mit dem MinGW-/Qt-CRT werden vermieden.
- `runtime/{windows,error,exception}.cc`, `runtime/memory_nt32.asm`, `runtime/qt5_embedded_misc.cc`: eingebetteter Build ohne konkurrierende WinAPI-/CRT-Wrapper und ohne eigenen DllMain.
- `d64dbase/native_runtime_deploy.py`, `d64_dism.py`, `pascal_console_dependencies.py`: prüfen Qt5-Architektur und benötigte native Exporte und melden veraltete COFF-Imports auf `libd64_runtime.dll` bzw. `c64_dbase_runtime.dll`.
- Historische Regressionstests für die absichtlich geänderte DLL-Zuordnung aktualisiert.

## PE32 unter MSYS2 MINGW32 bauen

```bash
cd d64qt5
python3 generate_runtime_abi.py
qmake d64qt5_bridge.pro CONFIG+=release
mingw32-make release
```

Der Qt5-Build startet `runtime/build.qt5_embedded.win32.sh` automatisch. Voraussetzung: `g++` mit Ziel `i686-w64-mingw32`, `nasm`, `ar`, Qt5/qmake in MINGW32. Das Ergebnis `d64qt5/release/libd64_qt5.dll` muss die nativen JIT-/dBASE-Exports aus `d64qt5_bridge.def` tatsächlich enthalten. Ein zuvor erzeugtes Qt5-DLL ohne diese Exporte wird von der IDE abgewiesen.

**Wichtig:** Die DLL muss neu gebaut werden; eine alte `libd64_qt5.dll` genügt nicht. Alle betroffenen `.prg`, `.pas` und COFF-Objekte (`.o`) müssen neu kompiliert, assembliert und gelinkt werden. Alte EXEs können durch Austausch der Qt5-DLL allein nicht von ihren vorhandenen Importen auf `libd64_runtime.dll` befreit werden.

## PE32+ / Einschränkungen

Die Erzeugung von PE32+/COFF64 und deren **Importtabellen** ist umgestellt und getestet. Der statisch einbettbare native PE64-Runtime-Build ist **noch nicht implementiert**. Der Qt5-64-Bit-Build meldet deshalb bewusst einen Fehler, statt eine unvollständige DLL zu erzeugen. Ein nativer Windows-/MinGW-Qt5-DLL-Link und ein Windows-Starttest waren in der aktuellen Testumgebung nicht möglich. Es wird daher keine bereits lauffähige integrierte Windows-DLL mitgeliefert.

## Tests

`test_stage678.py`: 13 neue Tests prüfen ABI-Exports und bestehende ABI-Kernprüfsumme, Buildpfad, Qt5-Aufrufe, Deployment und echte COFF-/PE-Linkergebnisse für O0/O1/O2 jeweils auf PE32 und PE32+. Weitere gezielte Regressionen decken die alten Pascal-Konsolenfunktionen, dBASE-Runtime, VMT/Klassen und DLL-Linkerzeugung ab. Die vollständige native Windows-Laufzeitvalidierung bleibt ausstehend.

## Architektur

Für neu erzeugte PE32-Programme gilt:

```text
App001.exe
  └── libd64_qt5.dll
        ├── Qt5 GUI / DEBUG- und Konsolen-Bridge
        ├── Pascal Console
        ├── JIT-Memory / Object / VMT / Exception
        └── dBASE Console / Zeichen- und WFM-Routinen
```

Andere systembedingte Abhängigkeiten (Qt5-Bibliotheken, MSVC-/MinGW-Runtime usw.) bleiben möglich. `libd64_runtime.dll`, `c64_dbase_runtime.dll` und `libd64_console.dll` werden für **neu gebaute** Anwendungen nicht mehr als gesonderte Dateien benötigt, sofern sie ausschließlich die migrierten Schnittstellen verwenden.
