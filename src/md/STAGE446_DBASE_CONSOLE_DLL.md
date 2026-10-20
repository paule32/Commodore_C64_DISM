# Stage 446 – dBASE-Konsole als externe PE32-/PE32+-Laufzeit-DLL

## Verbindliche Basis
`d64_dism_asm_445.zip`. Alle bisherigen GUI-, WFM- und Compiler-Funktionen bleiben enthalten.

## Ergebnis

Die native dBASE-Konsolenverwaltung wird **nicht mehr in jede generierte EXE geschrieben**, sondern als `d64_dbase_console.dll` importiert. Mitgeliefert werden **zwei echte, intern erzeugte Windows-DLLs**:

- `d64dbase/bin/pe32/d64_dbase_console.dll` – Intel i386, 32 Bit
- `d64dbase/bin/pe64/d64_dbase_console.dll` – AMD64, 64 Bit

Jede exportiert exakt die vier öffentlichen Namen `DBaseConsoleEnsure`, `DBaseConsoleWrite`, `DBaseConsoleShutdown` und `DBaseConsoleSetTitle`.

## API und Zustandsverwaltung

| Export | Verhalten |
|---|---|
| `DBaseConsoleEnsure()` | Lazy `AllocConsole`, `CONOUT$` mit Standard-Handle-Fallback, CP1252, 500 Scrollback-Zeilen, Konsolentitel, Workstation-sichtbares Console-HWND |
| `DBaseConsoleWrite(buffer, length)` | Ruft bei Bedarf `Ensure` auf und schreibt den CP1252-Bytepuffer mit `WriteFile` |
| `DBaseConsoleShutdown()` | Gibt die Konsole frei und setzt DLL-internen Zustand zurück |
| `DBaseConsoleSetTitle(title)` | Setzt den ANSI-Titel bei laufender Konsole sofort, andernfalls für die nächste `Ensure`-Initialisierung vor |

Die Zustandsvariablen für Ready-Flag, Handle, Console-HWND, WriteFile-Ausgabezähler und Bildschirm-Pufferinformation sind vollständig **DLL-intern**. Der Pufferlängenzähler `__dbase_console_number_len` bleibt korrekt in der EXE, weil er zur dortigen Formatierungsroutine gehört.

Die Exporte verwenden unter PE32 die bestehende **cdecl**-Aufrufkonvention (Schreibfunktion: `char*`, `uint32_t`; Aufrufer bereinigt 8 Stackbytes), unter PE32+ die **Windows-x64-ABI** (RCX, RDX, 32-Byte-Shadow-Space). `DBaseConsoleSetTitle` entleiht den übergebenen Null-terminierten ANSI-String; dieser muss gültig bleiben, solange er als bevorzugter Titel gespeichert ist.

## Compiler-/WFM-Integration

- Der normale PRG-Compiler importiert die DLL-Funktionen und ruft ausschließlich `DBaseConsoleWrite` und `DBaseConsoleShutdown` auf; die vollständigen Console-Routinen und ihre .bss-Variablen werden **nicht** mehr in das Programm eingebettet.
- Der bisherige Marker `D64DBASE_LAZY_CONSOLE_V1` für den Workstation-Runner bleibt vorhanden.
- WFM-Ereignisausgaben nutzen unverändert `DBaseQtConsoleWrite` aus `libd64_qt5.dll`; ein gemeinsamer PRG-/WFM-Bootstrap kann zusätzlich die native DLL importieren. Beide Arten werden bei der Bereitstellung berücksichtigt.
- Der PE32+-Assembler akzeptiert jetzt die 8-Bit-Instruktionen `mov al, byte ptr [rsi]`, `cmp al, 32` usw., die ein WFM-Formular mit Stringfunktionen erzeugt. Damit sind PE32+-WFM-Assemblierungen im Test möglich.

## Build und Bereitstellung

Vor der Erfolgsmeldung für den Linkvorgang (EXE/DLL) wird geprüft, ob die erzeugte dBASE-Ausgabe `d64_dbase_console.dll` importiert. Falls ja, wird die zum Ziel passende DLL in **dasselbe Verzeichnis** kopiert. Beim Starten einer bereits gelinkten EXE wird die tatsächlich vorhandene PE-Importtabelle anhand des eingebetteten DLL-Namens überprüft und die DLL nötigenfalls erneut bereitgestellt, ohne die EXE neu zu bauen.

Architektur und vier Exportnamen werden über den vorhandenen PE-Exportparser geprüft; eine veraltete, beschädigte oder falsch architektierte DLL wird durch das mitgelieferte Original ersetzt. Fehlen die beiden vorgefertigten DLLs, baut die IDE die passende Version mit ihrem **internen COFF-/PE-Assembler und -Linker**, ohne MinGW, NASM, `make` oder andere externe Buildwerkzeuge. Kann die Bereitstellung nicht abgeschlossen werden, erscheint eine Fehlermeldung; ein scheinbar erfolgreicher Start mit fehlender DLL wird verhindert.

**Achtung:** PE32- und PE32+-DLL tragen denselben Dateinamen. Sie gehören jeweils *neben die EXE ihrer Architektur*, nicht beide in ein gemeinsames Verzeichnis. Bei parallelen Projekten unterschiedlicher Architektur getrennte Ausgabeverzeichnisse verwenden.

## Verifikation

- Beide DLLs aus Original-Assembler und internem Linker bytegenau wiedererzeugt.
- PE-Machine `0x014C` bzw. `0x8664`, DLL-Merkmal und alle vier realen Exporte geprüft.
- PRG mit `SET FORMAT TO CONSOLE`, `LEN`, `TRIM` und Textausgaben als vollwertige PE32- und PE32+-EXE gelinkt.
- WFM mit Event-Ausgaben für beide Architekturen bis zur realen PE-Datei gelinkt.
- Bereitstellung mit absichtlich beschädigter bzw. architekturfalscher DLL geprüft.
- Neue Byte-Instruktionen über ihre wirklichen COFF-Maschinenbytes getestet.

**Grenze der Verifikation:** Eine tatsächliche Ausführung unter Windows 11 (Konsole öffnen, Workstation-Desktop, Fenster-TOPMOST und Schließen) ist in dieser Linux-Testumgebung nicht möglich. Diese Laufzeit-Sichtprüfung steht noch aus.
