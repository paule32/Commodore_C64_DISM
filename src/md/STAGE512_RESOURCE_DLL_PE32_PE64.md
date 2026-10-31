# Stage 512 – Ressourcen-DLLs aus dem Ressourcen-Editor

**Verbindliche Basis:** `d64_dism_asm_511.zip` / Stage 511.

## Bedienung

Die oberste Buttonleiste des Ressourcen-Editors wurde hinter **Aktualisieren** ergänzt:

- **win32 DLL**: Ressourcendatei als Windows-PE32-DLL (Intel 386) ausgeben.
- **win64 DLL**: Ressourcendatei als Windows-PE32+-DLL (AMD64) ausgeben.

Der Abstand vom Button **Aktualisieren** zu **win32 DLL** ist im gemeinsamen
`QHBoxLayout` mit `addSpacing(14)` und `setSpacing(0)` auf **14 logische Pixel**
festgelegt. Beide neuen Aktionen verwenden dieselben aktuell kompilierten
Ressourceneinträge wie `RC → RES`, `COFF32` und `COFF64`.

## Dateiausgabe

Für die Quelldatei `Resource32.rc` entsteht:

```
Quellverzeichnis/
  Resource32.rc
  win32/
    Resource32.res
    Resource32.o
    Resource32.dll
  win64/
    Resource32.res
    Resource32.o
    Resource32.dll
```

Die Dateien enthalten **alle** erfolgreich kompilierten Ressourceneinträge
inklusive Typen, IDs, Sprachen und Binärdaten. Bei ungespeicherten Änderungen
an der `.rc`-Datei greift wie bei der bisherigen RC-Kompilierung zuerst
`_compile_current_rc()`, das die Änderungen speichert.

## Technische Implementierung

- `write_res`: vorhandener Microsoft-RES-Writer.
- `write_resource_coff`: vorhandener Microsoft-COFF32-/COFF64-Writer
  für `.rsrc$01` und `.rsrc$02`.
- `write_resource_dll`: neuer, integrierter PE32-/PE32+-Writer. Fügt dieselben
  Ressourcen-Direktorien und -Daten zu einer `.rsrc`-Sektion zusammen und
  löst die COFF-`ADDR32NB`-Relocations auf deren tatsächliche RVAs auf.
- `build_resource_dll_files`: erstellt `.res`, `.o` und `.dll` im
  architekturspezifischen Unterverzeichnis.
- `WindowsResourceEditorWidget.compile_to_resource_dll`: Qt5-Anbindung
  einschließlich Fehleranzeige und Statusmeldung.

Die DLL hat das Flag `IMAGE_FILE_DLL` und **keinen ausführbaren Einstiegspunkt**
(`AddressOfEntryPoint=0`). Dies ist für reine Ressourcen-DLLs vorgesehen. Sie
exportiert keine Funktionen und benötigt keine andere Runtime-Bibliothek.

Es wird **kein externer MinGW-/MSVC-/LLVM-Linker** zum Erstellen der DLL benötigt.

## Titelleiste

Der Ressourcen-Dock erhält die bereits in der Anwendung vorhandene
`DockTitleBar`. Die Symbole für Andocken/Abdocken und Schließen sind dadurch
**weiß im Dark Mode** und **schwarz im Light Mode**; der globale Themewechsel
ruft `set_dark_mode()` für diesen Widgettyp bereits auf.

## Tests / Status

- 7 neue gezielte DLL- und GUI-Strukturtests bestanden.
- 98 Tests aus dem Ressourcen-Editor-Testpaket einschließlich Stage 512 bestanden.
- Beide DLL-Typen wurden zusätzlich durch `file` und `objdump` unabhängig als
  Windows-PE32/PE32+-DLL erkannt, mit korrekten `.rsrc`-Verzeichnisbäumen.
- Die generierten `.o`-Dateien wurden zum Vergleich mit `lld-link` zu
  unabhängigen Ressourcen-DLLs gelinkt (`/safeseh:no` für x86).
- Der vollständige, längere historische Formular-/Compiler-Sammellauf hat sein
  Zeitlimit erreicht und gilt **nicht** als abgeschlossen.
- Ein echter `LoadLibraryEx`- bzw. visueller PyQt5-Test auf Windows war hier
  nicht verfügbar; dieser sollte vor produktivem Einsatz nachgeholt werden.
