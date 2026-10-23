# Stage 490 – Plattformübergreifendes dBASE-Qt5-Terminal und TYPE()

Verbindliche Basis: Stage 489 (`d64_dism_asm_489.zip`).

## Neue Funktion

* `?` und `??` schreiben im GUI-Modus in einen eigenen nativen Qt5-Dialog mit einem schreibgeschützten `QPlainTextEdit`. `?` erzeugt einen Zeilenumbruch, `??` nicht.
* Windows: Die bereits bestehende `DBaseQtConsoleWrite`- und `DBaseQtAppendConsole`-Schnittstelle bedient zusätzlich das neue unabhängige Terminalfenster. Bisheriger Qt-Konsolen-Tab sowie DEBUG-/Workstation-Ausgabepfade bleiben erhalten; bei Debug-Ausgabe bleiben bestehende Regeln bestehen.
* Linux WFM: ELF32/ELF64 ruft unverändert `DBaseQtRunFormJson` in `libd64_qt5.so` auf. Im JSON wird `startup_output` für ausführbare Anweisungen **vor** `CLASS ... OF FORM` ergänzt. `onClick`-`?`-Ausgaben gehen ebenfalls in denselben Terminaldialog statt nach `stdout`.
* Linux PRG: Die IDE fordert nun `compile_linux_prg(..., qt_terminal=True)` an. Damit importiert ELF32/ELF64 den neuen Linux-C-ABI-Einstieg `DBaseQtRunConsoleJson` aus der dynamisch geladenen `libd64_qt5.so`. Das Programm bleibt sichtbar, bis das Terminal geschlossen wird.
* Für bestehende eigenständige Compiler-API-Nutzer bleibt `compile_linux_prg(..., qt_terminal=False)` (Standard) als freestanding `stdout`-Variante erhalten.
* Beide Linux-Qt5-Einstiege benötigen kein Python/PyQt5 im erzeugten Programm.

## Bugfix aus Form1.wfm

Ungenutzte Windows-`extern`-Prototypen aus eingelesenen Headern werden bei Linux-Zielen nicht mehr als sofortiger Linkfehler behandelt. **Tatsächlich aufgerufene** Windows-DLL-Funktionen werden weiterhin mit einer eindeutigen Fehlermeldung zurückgewiesen. `TYPE("xyz")` überprüft die benannte Variable (`U` wenn nicht definiert). `VARTYPE(n)` überprüft den Variablenwert. Unterstützte einfache Ausdrücke/IF-Blöcke werden ebenfalls im Linux-Basisteil kompiliert.

## Linux-Build

```bash
sudo apt install build-essential qtbase5-dev qt5-qmake
cd d64qt5
./build_linux.sh
```

Auf Linux kompiliert die `.pro`-Datei nur das gezielte plattformneutrale `d64qt5_linux_form.cpp`, **nicht** die Windows-spezifische `d64qt5_bridge.cpp`. Die passende `libd64_qt5.so` wird neben die ELF-Datei kopiert und über `$ORIGIN` geladen.

## Bekannte Grenzen

* Linux-WFM-/PRG-Codegenerierung implementiert noch einen eingeschränkten Teil der dBASE-Sprache. `IF`, Zuweisungen, `TYPE`, `VARTYPE` und konstante Ausdrucksausgabe werden im Compiler ausgewertet; das ist **keine vollständige Laufzeitumsetzung dynamischer dBASE-Anweisungen**.
* Ein beliebiges Windows-WFM-Programm mit Win32-Funktionen lässt sich nicht ohne Portierung auf Linux ausführen. Ein echter Windows-DLL-Aufruf bleibt dort unzulässig.
* Die grafische Qt5-Runtime konnte in dieser Umgebung nicht gegen reale Qt5-Headers kompiliert oder interaktiv getestet werden. Die ELF-Dynamik wurde mit einer echten, kleinen C-ABI-Testbibliothek geprüft (nicht mit der vollständigen Qt5-Bibliothek).
* ELF32 wurde als Datei/Importstruktur geprüft; ein nativer 32-Bit-GUI-Lauf wurde hier nicht ausgeführt.

## Wichtigste Dateien

`d64dbase/linux_frontend.py`, `d64qt5/d64qt5_linux_form.cpp`, `d64qt5/d64qt5_bridge.cpp`, `d64qt5/d64qt5_bridge.h`, `d64qt5/d64qt5_bridge.pro`, `d64_dism.py`, `test_stage490_linux_qt_terminal.py`.
