# Stage 488 – Native Linux-Qt5-Library und dynamischer ELF-Linker

**Basis:** Stage 487 `d64_dism_asm_487.zip`.

## Neues Build-Verhalten

Ein dBASE-Formular (`.wfm`) mit Linux32-/Linux64-Ziel wird nach dem Präprozessor
als UTF-8-JSON für eine **native Qt5-C++-Bridge** kodiert. Die generierte
Assemblerdatei enthält einen C-Funktionszeiger auf `DBaseQtRunFormJson` und
übergibt das JSON beim Aufruf. Der eigene ELF-Assembler schreibt ein ET_REL `.o`;
der neue dynamische ELF-Linker (`linux_elf_dynamic.py`) schreibt ein ET_EXEC mit
`PT_INTERP`, `PT_DYNAMIC`, `DT_NEEDED=libd64_qt5.so`, `DT_RUNPATH=$ORIGIN`,
`DT_SYMTAB`, `DT_STRTAB`, SysV-Hash und `R_X86_64_64`/`R_386_32`-Relocations.
Unter Linux lädt `ld-linux` die `.so` aus dem EXE-Verzeichnis und löst die
Symbole einschließlich Qt-Abhängigkeiten auf. Keine GNU-Assembler/Linker im
**dBASE-Build** und kein Python/PyQt5-Subprozess mehr.

**Hinweis:** Der Qt-C++-Compiler samt qmake wird **zum Erzeugen der `.so` selbst**
benötigt; ein interner x86/ELF-Assembler kann Qt-C++-Quelltext nicht übersetzen.

## Qt5-Shared-Library erstellen (Ubuntu 22.04)

```sh
sudo apt update
sudo apt install build-essential qtbase5-dev qt5-qmake
cd d64qt5
./build_linux.sh
```

Das Linux-Projekt (`d64qt5_bridge.pro`) erstellt
`d64qt5/release/libd64_qt5.so` für die aktuelle Host-Architektur.
Die Qt5-Laufzeitbibliotheken müssen auf dem Zielsystem ebenfalls installiert
sein. Das `.so`-Build kann auf Ubuntu x86-64 direkt erfolgen; für i386 muss es
mit einem **passenden 32-Bit-Qt-Entwicklungs- und C++-Toolchain** übersetzt
und unter `d64qt5/release32/libd64_qt5.so` abgelegt werden. Eine x64 `.so`
ist **nicht** mit einem ELF32-Programm kompatibel.

Beim Linken eines Linux-WFM-Programms prüft d64_dism die ELF-Klasse/Architektur
der Bibliothek und kopiert sie neben `Form1.elf64` bzw. `Form1.elf32`.
Fehlt die kompatible Datei, wird der Build als fehlgeschlagen gemeldet und
**Starten** nicht freigeschaltet. Der Linux-Executable-Start selbst verwendet
den vorhandenen IDE-Startmechanismus.

## Qt5-Bridge-Funktion

```c
int DBaseQtRunFormJson(const char *utf8Json);
```

Die Funktion wird mit `extern "C"` aus der `libd64_qt5.so` exportiert. Sie
verwendet die bestehenden Qt5-Widgets der Bridge und verarbeitet `Caption`,
`Text`, `Left/Top/Width/Height`, `Enabled`, `Visible`, `Placeholder`, `Checked`
und einfache `onClick`-Handler (`?`, `??`, konstante Textzuweisung). Sie ruft
die Qt5-Ereignisschleife auf und liefert bei regulärem Ende deren Exit-Code.

Das ist die **erste native Linux-Qt5-Formular-Runtime**, noch keine vollständige
Portierung der gesamten Windows-WFM-Codegenerierung. Komplexere dBASE-Methoden,
die native Windows-Workstation-Runtime und beliebige Win32-DLL-Funktionen sind
nicht portiert. Der Compiler weist nicht unterstützte WFM-Methoden explizit
zurück. Shared Libraries anderer Namen oder mehrere Imports pro Modul sind
im neuen ELF-Linker noch nicht allgemein verdrahtet. ELF-PIE, dynamische
ELF-.so-Erzeugung durch den *internen* Linker und `.bss` in dynamisch
gelinkten Hauptprogrammen gehören zu späteren Stufen.

## Verifikation

- ELF32 und ELF64: ET_REL und dynamisch gebundenes ET_EXEC, `readelf -d`.
- GNU AT&T und Intel: dynamische WFM-Objekte lassen sich assemblieren.
- ELF64 wurde unter Linux mit einer **separaten echten, aber als Test-Dummy
  kompilierten `.so`** aufgerufen; die C-ABI, der Loader und `$ORIGIN` sind
  damit getestet. Der Dummy ist **keine Qt-Runtime** und nicht im ZIP enthalten.
- Die native Qt-Formularbibliothek kann in dieser Buildumgebung **nicht**
  kompiliert/interaktiv geprüft werden, weil Qt5-Entwicklungsheader und qmake
  fehlen. Deshalb ist deren tatsächliche Linux-GUI-Ausführung noch offen.

### Quelldateien

- `linux_elf_dynamic.py`: dynamischer ELF-Linker
- `linux_elf.py`: optionale dynamische Linkoptionen
- `d64dbase/linux_frontend.py`: native WFM-C-ABI statt Python-Brücke
- `d64qt5/d64qt5_linux_form.cpp`: nativer Qt5-WFM-JSON-Loader
- `d64qt5/d64qt5_bridge.h`, `d64qt5/d64qt5_bridge.pro`: Export/Qt-Build
- `d64qt5/build_linux.sh`: Ubuntu-Skript für die `.so`
- `d64_dism.py`: Build-/Runtime-Einbindung und ELF-Architekturprüfung
- `test_stage488_native_linux_so.py`: Regressionstests
