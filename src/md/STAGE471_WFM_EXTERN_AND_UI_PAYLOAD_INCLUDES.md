# Stage 471 – WFM-Imports und externer UI-Payload als Include-Dateien

**Verbindliche Basis:** `d64_dism_asm_470.zip`.

## Ziel

Generierte Windows-dBase/WFM-Assemblerdateien bleiben übersichtlich: Die
Import-Direktiven verwenden eine Include-Datei ohne künstliche spitze Klammern,
und der numerische UI-Payload wird in eine zweite Include-Datei ausgelagert.

### Vorher (Stage 470)

```asm
%include "<Form1.generated.pe32.extern.inc>"
...
__dbase_wfm_external_ui_payload:
    db 123, 34, 118, 101, ...
    db 114, 115, 105, 111, ...
```

### Nachher (Stage 471)

**Form1.generated.pe32.asm**

```asm
%include "Form1.generated.pe32.extern.inc"
...
.section .data
...
__dbase_wfm_external_ui_payload:
    %include "Form1.generated.pe32.payload.inc"
...
```

**Form1.generated.pe32.extern.inc**

```asm
import DBaseQtRuntimeStartup, "libd64_qt5.dll", "#1011"
...
```

**Form1.generated.pe32.payload.inc**

```asm
    db 123, 34, 118, 101, ...
    db 114, 115, 105, 111, ...
```

Für PE64 werden analog `Form1.generated.pe64.extern.inc` und
`Form1.generated.pe64.payload.inc` erzeugt. Die Dateien liegen neben der
jeweiligen generierten `.asm`-Datei und werden beim Kompilieren neu geschrieben.

### Umsetzung

- `windows_asm_macros.py`: `externalize_windows_imports()` gibt reguläre
  Include-Angaben ohne `< >` aus.
- `windows_asm_macros.py`: neue Hilfsfunktion
  `externalize_windows_wfm_payload()` extrahiert ausschließlich unmittelbar
  hinter `__dbase_wfm_external_ui_payload:` stehende dezimale `db`-Zeilen.
  Label, Datensektion, folgende Labels und `.bss`-Abschnitte bleiben erhalten.
- `d64_dism.py`: `_finish_compile_stage()` ruft beide Helfer auf und speichert
  die Include-Dateien vor der Haupt-ASM-Datei; die Editoransicht bekommt die
  kompakte ASM-Ausgabe.
- Die Funktion benötigt keine neue Projekt-Einstellung. Falls das Feature
  "External UI components" deaktiviert ist, wird keine Payload-INC generiert.
- Der Windows-Assembler aus Stage 470 expandiert diese Dateien mit demselben
  Include-Pfadmechanismus wie benutzereigene Includes.

**Wichtig:** Für eine spätere manuelle Assemblierung müssen die `.extern.inc`
und `.payload.inc` neben der zugehörigen `.asm` verbleiben (oder über die
Projekt-Include-Suchpfade auffindbar sein). Es werden zur Laufzeit keine
externen `.inc`-Dateien benötigt; sie werden in das COFF-Objekt assembliert.

## Tests

`python -m pytest -q test_stage471_wfm_payload_include.py test_stage470_windows_asm_macros.py`

Erweiterter Lauf mit Compiler- und WFM-Regressionen der Stages 445 bis 471:
**147 Tests bestanden**.

Explizit geprüft: PE32 und PE64, komprimierter und unkomprimierter UI-Payload,
Include-Pfade, unveränderte Bytes in `.text` und `.data`, COFF-Linking bis PE EXE.
Eine interaktive Windows-/Qt5-Oberflächenprüfung war in dieser Umgebung nicht
möglich.
