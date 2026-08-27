# Qt5/qmake: PE32- und PE64-Beispiel

Die Architektur wird durch das jeweils verwendete qmake/MinGW-Kit bestimmt.
32- und 64-Bit-Ausgaben müssen in getrennten Shadow-Build-Verzeichnissen
erzeugt werden.

## 32-Bit-Konsolenprogramm

```sh
mkdir build-pe32-app
cd build-pe32-app
S:/msys64/mingw32/bin/qmake.exe ../d64_dual_target.pro CONFIG+=release
S:/msys64/mingw32/bin/mingw32-make.exe
```

Ausgabe: `build-pe32-app/bin/pe32/d64_sample_console.exe`

## 64-Bit-Konsolenprogramm

```sh
mkdir build-pe64-app
cd build-pe64-app
S:/msys64/mingw64/bin/qmake.exe ../d64_dual_target.pro CONFIG+=release
S:/msys64/mingw64/bin/mingw32-make.exe
```

Ausgabe: `build-pe64-app/bin/pe64/d64_sample_console.exe`

## 32- oder 64-Bit-DLL mit Importbibliothek

Zum DLL-Build wird zusätzlich `CONFIG+=d64_dll` angegeben. Beispiel PE32:

```sh
mkdir build-pe32-dll
cd build-pe32-dll
S:/msys64/mingw32/bin/qmake.exe ../d64_dual_target.pro CONFIG+=release CONFIG+=d64_dll
S:/msys64/mingw32/bin/mingw32-make.exe
```

Dabei entstehen `d64_sample.dll` und durch
`QMAKE_LFLAGS_DLL += -Wl,--out-implib,...` auch `libd64_sample.a` im
Verzeichnis `bin/pe32`. Für PE64 werden entsprechend qmake und make aus
`mingw64/bin` verwendet; die Ausgabe liegt dann unter `bin/pe64`.

