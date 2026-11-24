# Stage 677 – MinGW `-Wcast-function-type` im Qt5-Bridge-Build beheben

**Basis:** `d64_dism_stage676.zip`

Bei der Windows-32-Bit-Kompilierung mit MSYS2 MINGW32 meldete GCC zwei Warnungen
wegen direkter Konvertierung von `GetProcAddress()`/`FARPROC` in eine konkrete
`cdecl`-Funktionssignatur:

- `d64qt5/d64_pascal_console.cpp` – `_jit_malloc(unsigned)`;
- `d64qt5/d64qt5_bridge.cpp` – `DBaseConsoleWrite(const char*, int)`.

Beide Signaturen und die `cdecl`-Konvention bleiben **unverändert**. Der
Funktionszeiger wird nun zunächst als `FARPROC` mit `GetProcAddress()`
ermittelt, auf `nullptr` geprüft und anschließend **über `std::memcpy`** in
einen korrekt typisierten Funktionszeiger übernommen. Die `static_assert`-
Prüfung stellt sicher, dass beide Funktionszeigertypen auf der Zielplattform
die gleiche Größe besitzen. Dieser Windows-spezifische ABI-Ansatz vermeidet
den direkten Cast zwischen inkompatiblen Funktionstypen, ohne
`-Wcast-function-type` zu deaktivieren oder das DLL-ABI zu verändern.

`DBaseQtRuntimeWrite` verwendet unverändert den Fallback
`DBaseQtAppendConsole`, wenn der Export nicht gefunden wurde. Der Pascal-
Stringleser verwendet weiter den `_jit_malloc`-Allocator aus `libd64_runtime.dll`.
Keine Änderungen an den Exporten, Ordinals, DLL-Namen, Runtime-Zuständen,
O0/O1/O2-Einstellungen oder anderen Compiler-Zweigen.

## Prüfung

```sh
python -m pytest -q test_stage677.py test_stage676.py
```

Der erste Test kompiliert einen ABI-Dummy mit GCC und aktiviert dabei
`-Wcast-function-type` sowie `-Werror=cast-function-type`. Das ist ein
lokaler **Warnungs-/Pointer-Repräsentationstest**, kein Ersatz für den echten
Windows-MinGW-/Qt5-Build. Für die endgültige Bestätigung bitte auf MINGW32
und gegebenenfalls MINGW64 `qmake` und `mingw32-make release` erneut ausführen.
