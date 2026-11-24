# Stage 680 — MINGW32 Qt5-DLL: fehlender TObject-VMT-ABI-Export

## Ausgangsbasis

`d64_dism_stage679(1).zip` (vollständig übernommen, nur Buildregeln erweitert).

## Fehler

Bei `mingw32-make release` unter MSYS2/MINGW32:

```
ld.exe: cannot export jit_default_tobject_vmt_abi: symbol not defined
collect2.exe: error: ld returned 1 exit status
```

Die Funktion `jit_default_tobject_vmt_abi()` ist seit Stage 679 in
`runtime/jitObject.cc` implementiert und in `d64qt5/d64qt5_bridge.def`
als Export `@2085` eingetragen. Das native Archiv
`runtime/win32/libd64_qt5_native.a` wurde bislang nur neu erzeugt,
wenn es fehlte: die qmake-Spezifikation listete **keine Quell- und
Headerdateien als Voraussetzungen**. Eine bei Stage 678 erstellte `.a`
konnte deshalb trotz aktualisierter DEF unverändert weiterverwendet werden.

## Korrekturen

- `d64qt5/d64qt5_bridge.pro`: Native-Archiv-Ziel hängt von sämtlichen
  neun C++-Quellen, fünf NASM-Dateien, nativen Headern, Buildskript
  und `.pro`-Datei ab. Änderungen lösen nun einen Neubau der `.a` aus.
- `runtime/build.qt5_embedded.win32.sh`: prüft mit `nm` bereits nach
  der Übersetzung von `jitObject.cc`, ob das definierte PE32-cdecl-Symbol
  `_jit_default_tobject_vmt_abi` existiert. Bei Abwesenheit bricht der
  Build mit einer präzisen Fehlermeldung ab.
- Es gibt **keine Änderung der öffentlichen ABI**, des Ordinals `2085`,
  der Klasse `TObject`, des O3-Optimierers oder der restlichen Qt5-Bibliothek.

## Einmaliger sauberer Build (MSYS2 MINGW32)

```bash
cd /T/GitHub/dBase2Many/src/asmjit/compiler/frontend/c64/d64qt5
rm -f ../runtime/win32/libd64_qt5_native.a
python3 generate_runtime_abi.py
qmake d64qt5_bridge.pro CONFIG+=release
mingw32-make release
```

Zur Kontrolle:

```bash
nm -g --defined-only ../runtime/win32/qt5_embedded/jitObject.o | grep jit_default_tobject_vmt_abi
objdump -p release/libd64_qt5.dll | grep jit_default_tobject_vmt_abi
```

## Tests

- `test_stage680.py`: vollständige Abhängigkeitsliste, Export und Symbolprüfung.
- `test_stage679.py`: vorhandene ABI-/Quellcode-Regressionen bleiben gültig.

Ein tatsächlicher MINGW32-/Qt5-DLL-Build kann nur in einer Windows-/MSYS2-Umgebung
mit `qmake`, `nasm`, `g++`, `ar` und `nm` nachgewiesen werden.
