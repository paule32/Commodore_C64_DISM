# Stage 491 – Plattformmakros, Linux-Win32-Basistypen und Qt5-FFI

Verbindliche Basis: Stage 490 (`d64_dism_asm_490.zip`).

## Plattformmakros

Der dBASE-Präprozessor definiert pro Kompilierziel automatisch und exklusiv:

- `WINDOWS=1` für `pe32` und `pe64`
- `LINUX=1` für `linux32` und `linux64`

Das jeweils andere Symbol bleibt undefiniert. Explizite `#undef` und `#define` bleiben möglich; sie wechseln **nicht** die eigentliche Compilerzielarchitektur. Der Makrozustand gilt auch für verschachtelte `#include`-Dateien.

```text
#ifdef WINDOWS
#define shell32 "shell32.dll"
#define user32  "user32.dll"
#else
#ifdef LINUX
#define shell32 "shell32.so"
#define user32  "user32.so"
#endif
#endif
extern HINSTANCE ShellExecute(HWND,LPCSTR,LPCSTR,LPCSTR,LPCSTR,CINT) shell32 from "ShellExecuteA"
extern CINT MessageBoxA(HWND,LPCSTR,LPCSTR,UINT) user32 from "MessageBoxA"
```

## Typen und HWND

Die Win32-FFI-Typ-Aliasnamen sind auch unter Linux zulässig. `HWND`, `HANDLE` sowie `LPCSTR` sind pointergroß (ELF32: 32 Bit, ELF64: 64 Bit), `CINT`/`UINT` bleiben 32 Bit, `CVOID` signalisiert `void`. Das sind **C-ABI-Typen**, keine Windows-Objekte.

Unter Linux/X11 liefert `THIS.HWND` eine native Qt-`WId`, also eine X11-Fenster-ID (`XID`). Die Bridge ermittelt einen passenden Qt-Fensterelternteil nur durch Abgleich mit vorhandenen Top-Level-QWidgets. Ein beliebiger Win32-`HWND` wird niemals als `QWidget*` interpretiert. Unter Wayland existiert kein allgemeines X11-XID; `THIS.HWND` liefert hierfür 0 und `MessageBoxA` kann einen eigenständigen Dialog anzeigen.

## Native Shared Library

Die Linux-Runtime `d64qt5/d64qt5_linux_form.cpp` exportiert aus `libd64_qt5.so` die C-ABI-Symbole:

```c
int MessageBoxA(uintptr_t hwnd, const char *text, const char *caption, unsigned int type);
int MessageBoxW(uintptr_t hwnd, const uint16_t *text, const uint16_t *caption, unsigned int type);
```

Diese sind zusätzlich über die Aliase `user32.so` und `shell32.so` erreichbar. **Diese Aliase sind keine vollständigen Win32-Bibliotheken**: Die einzige reale Implementierung ist die Qt5-Bridge `libd64_qt5.so`. Der Linux-dBASE-Compiler kennt die eindeutigen Kompatibilitätsaufrufe `MessageBoxA/W` (sowie `ShellExecuteA/W`) und ruft sie im gegenwärtigen Linux-WFM-Teilumfang über `DBaseQtRunFormJson`/`DBaseQtRunConsoleJson` auf. Die ELF-Datei ist dynamisch mit `libd64_qt5.so` verbunden. Unbekannte `.dll`-/`.so`-Aufrufe erzeugen weiterhin Compilerfehler.

### MessageBox-Typen und Rückgabewerte

`uType & 0x0F` legt die Buttons fest: `MB_OK`, `MB_OKCANCEL`, `MB_ABORTRETRYIGNORE`, `MB_YESNOCANCEL`, `MB_YESNO`, `MB_RETRYCANCEL`, `MB_CANCELTRYCONTINUE`. Die Flags `MB_ICONERROR` (0x10), `MB_ICONQUESTION` (0x20), `MB_ICONWARNING` (0x30), `MB_ICONINFORMATION` (0x40) bestimmen das Qt-Symbol. `MB_DEFBUTTON1..4` steuert die Standardtaste für gängige Schaltflächengruppen.

Rückgabe bei erfolgreicher Dialogauswahl: `IDOK=1`, `IDCANCEL=2`, `IDABORT=3`, `IDRETRY=4`, `IDIGNORE=5`, `IDYES=6`, `IDNO=7`, `IDTRYAGAIN=10`, `IDCONTINUE=11`. Bei einem GUI-/Thread-Fehler oder einem nicht regulär abgeschlossenen Dialog ist `0` möglich. `MessageBoxA` interpretiert Strings in der lokalen ANSI-/System-Zeichenkodierung (auf Ubuntu üblicherweise UTF-8); `MessageBoxW` übernimmt UTF-16.

## Ubuntu-Build und Installation

```bash
sudo apt install build-essential qtbase5-dev qt5-qmake
cd d64qt5
./build_linux.sh
```

Das Skript legt `release/libd64_qt5.so` sowie Verknüpfungen `release/shell32.so`, `release/user32.so` an. Die IDE kopiert die passende ELF32-/ELF64-Qt-Bibliothek und vorhandene passende Aliase neben das Zielprogramm. **ELF32 benötigt auch eine tatsächlich als 32-Bit gebaute Qt5-Bibliothek**; ein 64-Bit-Build darf nicht als ELF32-Laufzeit verwendet werden.

## Tests und bekannte Grenzen

- Die Präprozessorpfade für Windows und Linux, `#include`-Makros, `ShellExecuteA`, `MessageBoxA/W`, `THIS.HWND`, Argumentfehler, `.prg`/`.wfm`, ELF32/ELF64 wurden mit Python-Regressionsprüfungen getestet.
- Qt5-Entwicklungsdateien stehen in der ausführenden Testumgebung nicht zur Verfügung. Der wirkliche `QMessageBox`-Dialog sowie der Bau von `libd64_qt5.so` sind **nicht** grafisch bzw. durch einen echten Qt5-Compiler-Lauf bestätigt.
- Die bisherigen Linux-WFM-Methoden unterstützen nur einen dokumentierten Teilumfang des dBASE-Sprachumfangs. Es gibt keine vollständige Nachbildung der Windows-API oder eine freie allgemeine Bindung beliebiger Shared-Library-Funktionen.

Beispiele: `examples/winapi_stage491/linux_windows_compat.h`, `dialog.prg`, `Form1.wfm`.
