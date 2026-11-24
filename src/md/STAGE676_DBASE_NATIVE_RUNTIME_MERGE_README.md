# Stage 676 – dBASE-Funktionen in `libd64_runtime.dll`

**Basis:** `d64_dism_stage675.zip`. Die zuvor getrennte `c64_dbase_runtime.dll`
ist für **neu erzeugte** dBASE-EXE-/DLL-Projekte nicht mehr vorgesehen.

## Übernommene C-ABI-Exporte

Die native Datei `runtime/dbase_runtime_merged.cc` (und die Kopie
`runtime/compiler/dbase_runtime_merged.cc`) implementiert sämtliche elf
bisher aus der eigenständigen dBASE-DLL importierten Routinen:

- `DBaseConsoleEnsure`, `DBaseConsoleWrite`, `DBaseConsoleShutdown`, `DBaseConsoleSetTitle`
- `DBaseCharIsLowerCP1252`, `DBaseCharIsUpperCP1252`, `DBaseCharIsLowerUtf8`, `DBaseCharIsUpperUtf8`
- `DBaseStringLengthN`, `DBaseWfmClassifyType`, `DBaseWfmFormatValue`

**Kompatibilität:** PE32 verwendet weiterhin `cdecl`, PE32+ die Microsoft-x64-ABI.
Die WFM-Werteslots sind gepackt: `[uint32 type][double value][pointer][uint32 length]`.
Auch das WFM-Ergebnis ist gepackt und schreibt nur Pointer plus 32-bit Länge
(also 8 Bytes bei PE32 bzw. 12 bei PE32+). Die Zeichenbereiche werden aus
den bestehenden CP1252-/UTF-8-Prädikaten abgeleitet und als
`dbase_case_ranges.inc` mitgeliefert. Die Konsolenverwaltung behält
`CONOUT$`, CP1252, 500-Zeilen-Scrollback und die bisherige Window-Anhebung.

## Änderungen am Compiler und GUI

Die dBASE-Compiler-Imports (`d64dbase/compiler.py`) und die dynamische
Ausgabeumleitung (`d64qt5/d64qt5_bridge.cpp`) verweisen jetzt auf
`libd64_runtime.dll`. Gleiches gilt für die zusätzlichen WFM-Imports in
`d64_dism.py`. Die bisherigen `libd64_qt5.dll`-Exporte für O1/O2 bleiben
unverändert. Alle Stufen O0/O1/O2 importieren die nativen Hilfsfunktionen
aus der gemeinsamen Runtime.

Die IDE stellt die DLL jetzt aus einem **nativen DLL-Build** bereit, statt
eine eigenständige Konsole mit dem Python-PE-Linker zu erzeugen.
`d64dbase/native_runtime_deploy.py` überprüft die PE-Maschinenkennung und
sowohl die elf neuen dBASE-Exporte als auch die bestehenden `jit_object_*`-
Exports, bevor sie eine vorhandene DLL ersetzt. Veraltete PE-Imports aus
`c64_dbase_runtime.dll` lösen eine Aufforderung zum Neuassemblieren aus.

Der bisherige Button heißt jetzt `dBASE Runtime DLL bereitstellen`, da
zum tatsächlichen **Neubau** der nativen Runtime eine MinGW-Toolchain nötig
ist. Die Option `pack dll` wirkt weiterhin auf benannte dBASE-Klassen-
bibliotheken, aber **nicht** auf die native `libd64_runtime.dll`.
Der historische eigenständige Assembler-Generator `console_runtime.py`
verbleibt nur für ältere Test-Fixtures und wird im produktiven IDE-Buildweg
nicht mehr verwendet.

## Native DLL bauen / bereitstellen

Unter MSYS2 **MINGW32** im Verzeichnis `runtime/`:

```bash
bash build.win32.sh
```

Das Skript bindet die neue C++-Objektdatei ein, exportiert die zusätzlichen
Namen (Ordinal 200–210) und linkt auch `user32` und `msvcrt`.
`runtime/compiler/build.win32.sh` ist entsprechend synchronisiert.
Das Ergebnis liegt bei `runtime/win32/libd64_runtime.dll` und wird durch
die IDE neben die erzeugte EXE kopiert. Die bisherige
`c64_dbase_runtime.dll` wird nicht mehr erzeugt oder bereitgestellt.
Vorhandene, mit älteren Stages erzeugte `.o`-Dateien müssen **neu gebaut**
werden.

**PE32+ Einschränkung:** Die elf neuen Funktionen sind auch für die
Microsoft-x64-Aufrufkonvention implementiert und die PE64-Import-/COFF-/PE-
Strecke ist getestet. Das bisherige `runtime/build.win64.sh` erzeugt jedoch
`libdbase2many.64.dll` statt einer vollständigen
`libd64_runtime.dll` mit den vorhandenen JitObject-Exports.
Für ein lauffähiges PE32+-Programm muss daher zuerst ein vollständiger
PE64-Build der nativen `libd64_runtime.dll` mit dem neuen Modul verfügbar
sein. **Ein solcher PE64-DLL-Build ist mit dieser Stage nicht bestätigt.**
Die IDE lehnt eine fehlende oder inkompatible DLL ausdrücklich ab; sie baut
keinen unvollständigen Ersatz.

## Prüfungen

- `pytest -q test_stage676.py`: **9 bestanden**; echte COFF32-/COFF64-
  Assemblierung und PE-Linkvorgänge für O0/O1/O2, Importtabellen, C++-ABI,
  CP1252 und UTF-8 über vollständige Zeichenbereiche, WFM-Layout und
  validierte DLL-Bereitstellung.
- `pytest -q test_stage674.py test_stage671.py test_stage670.py`: **27 bestanden**.
- Zusätzlich syntaktische 32-/64-Bit-Prüfungen mit GCC und Clang-
  Windows-Targets sowie Shell-Syntaxprüfung für beide PE32-Buildskripte.
- **Nicht durchgeführt:** Ein kompletter Windows-MinGW-Build von
  `libd64_runtime.dll` und ein Windows-Laufzeittest.

Hinweis: Die DLL wird als native **Quelle**, nicht als vorgetäuschtes fertiges
Windows-Binary ausgeliefert. Alte EXE-Dateien, die `c64_dbase_runtime.dll`
importieren, werden nicht automatisch umgeschrieben.
