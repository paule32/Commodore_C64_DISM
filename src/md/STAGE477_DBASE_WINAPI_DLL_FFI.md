# Stage 477 – dBASE Windows DLL-FFI (Basis: Stage 476)

## Kurzüberblick

Diese Stage ergänzt `extern`-Prototypen in `.prg` und `.wfm`, auch aus
`#include`-Headerdateien. Die Basistypen `HINSTANCE`, `HWND`, `LPCSTR`, `CINT`
und `CVOID` sind im Compiler eingebaut und benötigen keine separate
Typdefinitionsdatei. Ein Header dient zur Wiederverwendung von Prototypen.

### Syntax und DLL-Makro

```dbase
#define shell32 "shell32.dll"
extern HINSTANCE ShellExecute(HWND, LPCSTR, LPCSTR, LPCSTR, ;
    LPCSTR, CINT) shell32 ;
    from "ShellExecuteA"

result = ShellExecute(0, "open", "notepad.exe", 0, 0, 1)
? result
```

Der Bezeichner `shell32` wird durch den Stage-475-Präprozessor zu
`"shell32.dll"` expandiert. Die Deklaration kann alternativ in
`#include "winapi_shell.h"` stehen; Beispiele sind im Ordner `examples/`.
Der Punkt nach `from "ShellExecuteA"` wird optional toleriert.

### ABI und Typmodell

* PE32: Windows-`WINAPI`/`__stdcall` (Argumente rückwärts auf dem Stack,
  der Aufgerufene bereinigt den Stack).
* PE32+: Microsoft-x64-ABI (RCX, RDX, R8, R9; 32 Byte Shadow Space,
  weitere Argumente im ausgerichteten Stackbereich).
* `LPCSTR`: Zeiger auf einen NUL-terminierten ANSI-Text; konstante
  Stringliterale werden im CP1252-Format eingebettet. In der WFM-Runtime
  bleiben dynamische Speicher-Strings UTF-8; bei Nicht-ASCII-Zeichen sollten
  derzeit Stringliterale verwendet oder eine explizite ANSI-Konvertierung
  vorgeschaltet werden. Dynamische ASCII-Strings sind kompatibel.
* `HWND`, `HINSTANCE`: native pointergroße Integer/Handles; zum Beispiel
  `0` als NULL-`HWND`. `THIS` bzw. Qt-Control-Pointer ist **kein** natives
  Windows-`HWND` und wird für HWND-/Handle-Parameter abgewiesen.
* `CINT`: vorzeichenbehafteter 32-Bit-Integer; dBASE-Zahlwerte werden
  mittels x87 in Ganzzahlen konvertiert (FPU-Rundungsmodus).
* `CVOID`: rückgabeloser Aufruf. Als einziger Parameter `CVOID` bedeutet
  es eine leere Parameterliste. `CVOID` kann nicht als Rückgabewert zugewiesen
  werden und darf kein normaler Argumenttyp sein.

Rückgaben außer `CVOID` erscheinen in dBASE als numerische Werte. Fehler bei
Parametertyp/Anzahl, unbekannten Typen, ungültigen DLL-Namen, wiederholten
Prototypen und ungültiger Syntax führen zu Compilerdiagnosen.

### Integration

* `d64dbase/ffi.py` (neu): `DBaseFFIPrototype`, Syntaxanalyse und
  Entfernen der Prototypen aus der temporären Präprozessor-Ausgabe bei Erhalt
  der Quellzeilenanzahl.
* `d64dbase/compiler.py`: Frontend-Result mit FFI-Deklarationen, Bindungen im
  AST/Analyzer, Windows-Importe und nativer Aufruf über COFF32/COFF64.
* `d64_dism.py`: FFI in WFM-Top-Level-Code und Methoden (Statements,
  STORE/Zuweisungen, Druckausgaben, IF-Bedingungen) sowie bestehende
  include_paths aus `Projekt-Einstellungen → Compiler → Eingabe-Verzeichnis`
  auch für den `.prg`-Build.
* DLL-Einbindung ist ein statischer PE-Import zur Ladezeit, kein dynamisches
  `LoadLibrary`-/`GetProcAddress`-System. Die DLL und das exakte Export-Symbol
  müssen für die Zielarchitektur unter Windows vorhanden sein.

### Tests

`test_stage477_dbase_winapi_ffi.py`: Prototypen mit Makro-/Include-Ersetzung,
PE32/PE32+ für `.prg`/`.wfm`, echte COFF-Assemblierung und Linking,
WFM-Event-Methoden, CVOID und Parameterdiagnosen. Zusätzlich wurden die
unmittelbar angrenzenden dBASE-/WFM-Regressionen ausgeführt.

**Grenze:** Die generierten Windows-EXEs wurden hier nicht auf einem nativen
Windows-System mit Qt5 und `shell32.dll` ausgeführt; die Validierung prüft
Compiler, Assembler, Importtabellen-Erzeugung und Linker.
