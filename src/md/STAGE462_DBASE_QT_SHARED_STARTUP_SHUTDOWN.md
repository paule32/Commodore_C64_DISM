# Stage 462 – Gemeinsamer Qt5-Runtime-Startup/Shutdown

Verbindliche Ausgangsbasis: `d64_dism_asm_461.zip`.

## Ziel

Den wiederholten Start-/Shutdown-Assembler für dBASE-Konsole und WFM in die vorhandene
`libd64_qt5.dll` verlagern. Die alte Ordinal-ABI (64 Kern-Exporte) bleibt unverändert.

## Neue additive Qt5-Exports (nur über Namen eingebunden)

```c
int DBaseQtRuntimeStartup(const char *title, int workstationMode,
                         int debugTheme, int guiMode, void **formatBuffer);
void DBaseQtRuntimeShutdown(void **formatBuffer);
```

DEF-Ordinals: `@1011` und `@1012` (außerhalb der unveränderten Kern-Ordinal-ABI).
Der SHA-256-Hash der Kern-Ordinalbelegung bleibt
`02c94324ebc9e8373c08011d0f8c5ba5aec95b158087092ed4e741877b1a7cd7`.

### Initialisierung

* `formatBuffer` ist weiterhin ein Pointer-Slot in der `.bss`-Sektion des Programms.
* Der DLL-Helfer reserviert einen nullinitialisierten 96-Byte-Puffer
  (`VirtualAlloc`, unter Nicht-Windows `calloc`) und verwaltet seine Freigabe.
* Danach werden Workstation Mode und Debug Theme gesetzt. `guiMode=0`
  verwendet `DBaseQtInitialize`, `guiMode=1` verwendet `DBaseQtInitializeGui`.
* Bei fehlgeschlagener Allokation oder fehlgeschlagener Qt-Initialisierung gibt
  die Funktion `0` zurück und hinterlässt einen leeren Pointer-Slot; sie gibt
  den Puffer bei Qt-Fehlschlag frei. Der generierte Code beendet dann mit
  `ExitProcess(1)`.
* Bei Erfolg wird `1` zurückgegeben und der Pointer-Slot gefüllt.

### Shutdown

`DBaseQtRuntimeShutdown(&formatBuffer)` setzt den Slot auf null und gibt den
Puffer **vor** `DBaseQtShutdown()` frei. Das ist erforderlich, weil
`DBaseQtShutdown()` im normalen Nicht-Workstation-Start selbst `ExitProcess(0)`
auslösen kann.

Im **Konsolenpfad** werden Speech-Cleanup (falls aktiv) und
`DBaseConsoleShutdown()` **vor** dem gemeinsamen Qt-Shutdown ausgeführt.
Im **WFM-Pfad** bleiben `__main__`/`__del__` und die Eventhandler im bisherigen
Code. WFM prüft neu auch den Rückgabewert von `DBaseQtRuntimeStartup`.

Die bisherige MS-x64-ABI-Aufrufkonvention wird eingehalten:
RCX/RDX/R8/R9 für die ersten vier Argumente, der fünfte Pointer im Stack-Slot
`[rsp+32]` nach dem 40-Byte-Stackreservierungsbereich; PE32 verwendet cdecl.

`VirtualAlloc/VirtualFree` können weiterhin für **andere** Funktionen nötig
sein, insbesondere für die temporäre RAWINPUT-Geräteliste von `ISKEYBOARD()`.
Diese separaten Imports bleiben bedarfsabhängig erhalten.

## Geänderte Dateien

* `d64qt5/d64qt5_bridge.{h,cpp,def}`: neue C-ABI-Runtime-Exports.
* `d64qt5/generate_runtime_abi.py`: Namen von der festen Kern-ABI ausgeschlossen.
* `d64dbase/compiler.py`: dBASE-Konsolencompiler nutzt die neue Runtime.
* `d64_dism.py`: WFM-Entry, bedarfsabhängige ISKEYBOARD-Imports und neue
  optionale Qt5-Exporte für die bestehende DLL-Kompatibilitätsprüfung.
* `test_stage459_qt5_ordinal_abi.py`: Exportanzahl um die zwei neuen
  Erweiterungen angepasst, unveränderter Kernhash geprüft.
* `test_stage462_dbase_runtime_startup.py`: echte PE32-/PE32+-Linktests
  einschließlich `ISKEYBOARD()`, ABI-Prüfung und native isolierte
  C++-Startup-/Shutdown-Ausführung mit simulierten Qt-Funktionen.

## Größenmessung am vollständigen intern gelinkten PE-Image

| Testprogramm | Stage 461 `.text` | Stage 462 `.text` | Ersparnis |
|---|---:|---:|---:|
| dBASE-Konsole PE32 | 1174 B | 1046 B | 128 B |
| dBASE-Konsole PE32+ | 1717 B | 1446 B | 271 B |
| WFM PE32 | 3042 B | 2826 B | 216 B |
| WFM PE32+ | 3702 B | 3302 B | 400 B |

Die Dateigröße kann aufgrund von PE-Sektionsausrichtung unverändert bleiben.
Die Größe der Runtime-DLL steigt durch die neuen gemeinsamen Routinen leicht;
diese Mehrkosten entstehen nur einmal statt in jeder kompilierten EXE.

## Prüfung und Einschränkungen

Python-Syntax, C++-Helferkörper in einem nativen Stub-Test, interne
Assembler/COFF/PE32- und PE32+-Builds sowie die betroffenen Regressionstests
wurden getestet. Die vollständige `libd64_qt5.dll` muss unter Windows mit Qt5
neu gebaut werden, denn ältere DLLs besitzen die Exporte `@1011` und `@1012`
noch nicht. **Ein echter Windows-`LoadLibrary`-/GUI-Starttest war in dieser
Umgebung nicht möglich.** Der native Stub-Test simuliert die Qt-Funktionen
und ersetzt keinen vollständigen Qt5-Test.
