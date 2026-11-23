# Stage 674 – dBASE O2 Static String Optimierung

**Verbindliche Grundlage:** `d64_dism_stage673.zip`. Die bestehenden O0/O1-Pfade bleiben erhalten.

## Einstellungen

Projekt-Einstellungen → Windows → 32/64-Bit → Compiler → dBASE → Optimierung → **Optimierungsstufen:** (erste GroupBox).

- `O0  -  keine Optimierung` (Standard)
- `O1  -  Länge Optimierung - JNE JE`
- `O2  -  Static String Optimierung`

`O2` führt die bisherigen O1-Sprungvereinfachungen **und** den statischen Ausgabezusammenfasser aus, ersetzt aber dessen Stage-673-Aufruf mit fünf Argumenten durch einen einzigen Deskriptorzeiger.

PE32/PE32+ speichern ihren Wert wie bisher getrennt unter `Settings.Windows.32Bit.Compiler.dBASE.Optimierung` und `Settings.Windows.64Bit.Compiler.dBASE.Optimierung`, jeweils `OptimizationLevel=O0|O1|O2` in `.pro`. Alte Projekte behalten ihren Wert; fehlende/ungültige Werte werden O0.

## ABI und generierter Code

Die ursprünglichen Textdaten/Labels bleiben unverändert, damit sie weiterhin für andere String-Funktionen nutzbar sind. Ein zusätzlicher Deskriptor wird pro *benutztem Literal-Label* nur einmal erstellt.

PE32:

```asm
section .data
__dbase_o2_dbase_text_1:
    dd 4
    dd __dbase_text_1

section .text
    push __dbase_o2_dbase_text_1
    call DBaseQtRuntimeWriteText
    add esp, 4
```

Das `add esp, 4` bleibt wegen der **cdecl**-Aufrufkonvention erforderlich. PE32+ übergibt denselben Deskriptor in `RCX` und reserviert den üblichen 32-Byte-Shadow-Space sowie passende Stack-Ausrichtung:

```asm
    mov rcx, __dbase_o2_dbase_text_1
    sub rsp, 40
    call DBaseQtRuntimeWriteText
    add rsp, 40
```

Die 64-Bit-Datenstruktur benutzt `dd length; dd 0; dq text_pointer` (16 Byte) statt des 8-Byte-Deskriptors unter PE32.

## Ausgabezustand nur einmal binden

Nach erfolgreichem `DBaseQtRuntimeStartup`, am Label `__dbase_qt_init_ok_*`, bindet das EXE-Modul einmalig die Adresse einer kleinen Struktur mit **drei Zeigern** auf die bisherigen EXE-Variablen:

```asm
__dbase_o2_output_state:
    dd __dbase_output_debug_override
    dd __dbase_output_format_screen
    dd __dbase_output_debug_visible
```

Die DLL behält ausschließlich den Pointer auf diese Struktur; sie kopiert die Werte nicht. Somit werden spätere Änderungen durch `SET FORMAT TO ...` und `SET DEBUG ON/OFF` bei jeder Ausgabe wirksam. Die Bindung wird am Programm-Cleanup und zusätzlich durch `DBaseQtRuntimeShutdown` gelöscht. Bei beigelinkten COFF-Programme-Objekten übernimmt ausschließlich das startende **Module** die Registrierung.

Die dBASE-Compiler-Optimierung generiert nur für genau erkannte, statische Literal-Ausgabeblöcke die neuen Aufrufe. Dynamische Texte, Zahlen, VMT und Exceptions werden nicht ungeprüft umgeschrieben. Der bisherige O0-Code ist identisch; O1 verwendet weiter `DBaseQtRuntimeWrite`.

## Neue Qt5-DLL-Exporte

- `DBaseQtRuntimeWrite` (@1019) **unverändert**, für Stage 673 und O1.
- `DBaseQtBindOutputState` (@1020): einmaliger `DBaseQtOutputBindings*` / `nullptr` zum Abmelden.
- `DBaseQtRuntimeWriteText` (@1021): ein `DBaseQtStaticText*`.

Beide neuen Exporte werden **per Namen** importiert, sie ändern nicht die historische SHA-256-ABI-Prüfsumme für @1 bis @64 (`02c94324ebc9e8373c08011d0f8c5ba5aec95b158087092ed4e741877b1a7cd7`). Der Konsolenpfad verwendet weiterhin `DBaseConsoleWrite` aus `c64_dbase_runtime.dll`. Die Runtime prüft die Länge und delegiert die tatsächliche Ausgabe an die Stage-673-Funktion.

**Wichtig:** `libd64_qt5.dll` muss für Windows PE32 und PE32+ aus den neuen Stage-674-Quellen neu gebaut und zusammen mit O2-Anwendungen ausgeliefert werden. Die alten DLLs kennen @1020/@1021 nicht. Ein neuer Build von `c64_dbase_runtime.dll` ist wegen O2 nicht notwendig. Ein Windows-Qt5-Build und ein GUI-Laufzeittest wurden in dieser Linux-Prüfumgebung nicht durchgeführt.

## Größenvergleich mit App001.generated.pe32.asm

Die zugehörige `App001.generated.pe32.extern.inc` wurde beim wirklichen COFF-/PE-Link verwendet.

| Stufe | COFF `.text` | `.data` | PE32-EXE |
|:---|---:|---:|---:|
| O0 | 3.711 Byte | 375 Byte | 6.144 Byte |
| O1 / Stage 673 | 2.661 Byte | 375 Byte | 5.120 Byte |
| O2 / Stage 674 | **2.473 Byte** | 436 Byte | 5.120 Byte |

O2 spart gegenüber O1 **188 Codebytes** und erzeugt **61 zusätzliche Datenbytes**. Die Dateigröße bleibt durch PE-Sektionsalignment gleich. Im App001-Test wurden 10 statische Aufrufe auf O2 umgeschrieben.

## Nachweise und Einschränkungen

- `test_stage674.py`: O0/O1/O2, GUI-Labels, Roundtrip der `.pro`-INI-Fragmente, O2-Idempotenz, Stage-671-Zweigoptimierungen, COFF32/COFF64-Assemblierung und PE-Link, mehrere Objekte, eigene Runtime-Ausführung der neuen C++-Funktionen unter einem nativen Mock, App001-Link mit tatsächlichen Imports.
- `test_stage671.py` sowie `test_stage673.py` wurden erfolgreich ausgeführt. Die ersten 10 Stage-672-Tests bestanden; die letzten aufwendigen historischen Tests konnten nicht vollständig beendet werden (Zeitlimit). Die neuen Stage-674-Tests liefen in getrennten Gruppen erfolgreich.
- Die Stage-673-Runtime-Export-Testfunktion funktioniert unverändert mit dem alten ABI. Der vollständige Qt5-DLL-Build und echte Windows-GUI-Laufzeittests stehen aus.
- Für das bestehende Hauptprogramm/Programme-Modell gilt weiterhin: Top-Level-Ausführung eines Programme-Blatts wird beim Erzeugen eines beitragenden COFF-Objekts entfernt; das startende Module enthält `_start`.

## Geänderte/neu hinzugefügte Dateien

Geändert: `d64_dism.py`, `dbase_size_optimizer.py`, `d64qt5/d64qt5_bridge.cpp`, `d64qt5/d64qt5_bridge.h`, `d64qt5/d64qt5_bridge.def`, `test_stage671.py`.

Neu: `dbase_static_output_optimizer.py`, `test_stage674.py`, `STAGE674_DBASE_O2_STATIC_STRING_RUNTIME_README.md`.
