# Stage 646 — Win32-Dateifehler als dBASE-Exceptions und Dateidialog-Feinschliff

**Verbindliche Basis:** Stage 645 (`d64_dism_stage645.zip`).

## Datei-Öffnen-Dialog (zusätzliche Änderungsanforderung)

- Das Label `Pfad: /...`, die linke Verzeichnisliste und die rechte Dateiliste (einschließlich Spaltenköpfen) erhalten dieselbe Monospace-Schriftfamilie. Die Auswahl erfolgt in der Reihenfolge **Consolas → Courier New → Courier** über `QFontDatabase::hasFamily()`.
- Bei Hover über Titelleiste, Titeltext und das rechte leere Titelstück zeigt Qt `Qt::SizeAllCursor` (Verschieben). Der Schließen-Button bleibt bei `Qt::PointingHandCursor`.
- Die erste Spalte `Name` der rechten Dateiliste wird nach jedem Verzeichniswechsel auf den automatisch gemessenen Inhalt plus **24 Pixel** gesetzt. Die restlichen Spalten bleiben unverändert; der Benutzer kann die Spaltenbreite weiterhin mit dem Sizer ändern.
- Die übrigen Cursorbelegungen (Hand über Einträgen/Buttons, Split-Cursor über Teilergrenzen, Pfeil auf freien Flächen) und das virtuelle Dateisystem bleiben bestehen.

Betroffene Datei: `d64qt5/d64_turbo_editor.hpp`.

## Win32-Fehlerbrücke (Fortsetzung der vorausgehenden Anfrage)

- `Exception.Code` ist numerisch und wird in geerbten nativen Instanzen mitgespeichert; `Win32Exception` und `Win32FileException` sind von `Exception` abgeleitet.
- Die expliziten dBASE-Builtins `Win32Raise(code)` und `Win32FileRaise(code)` erzeugen eine typisierte Exception, wenn `code != 0`; `Code = 0` löst keine Exception aus.
- `Win32CheckFile("Dokumente/datei.prg")` prüft eine virtuelle Datei auf Lesezugriff via `DBaseQtVfsCheckOpenRead` und erfasst auf Windows direkt nach dem gescheiterten `CreateFileW` den tatsächlichen `GetLastError()`-Code. Das bleibt an den VFS-Mountpoints gebunden.
- Der native Compiler verwendet `FormatMessageA` zur Windows-Systemmeldung; die portable Vorschau hat einen kleineren deutschen Fallback-Katalog.
- `THROW e` erhält den numerischen Code. Der Python-Interpreter und der native Klassenmethoden-Emitter berücksichtigen `e.Code`.

Betroffene Dateien: `d64dbase/compiler.py`, `d64dbase/native_method_exceptions.py`, `d64dbase/win32_errors.py`, `runtime/dbase/src/System.SysUtils.prg`, `d64qt5/d64qt5_bridge.cpp` und `.h`.

**Abgrenzung:** Dies ist eine *Win32-Rückgabefehler-/GetLastError*-Brücke, keine native SEH-Unwind-Implementierung. Nicht jeder fehlgeschlagene Windows-API-Aufruf erzeugt automatisch eine Exception; die explizite Prüfung/Weiterleitung muss am jeweiligen Aufruf erfolgen. Nicht alle bestehenden Datei-APIs sind bereits angebunden.

## Prüfungen

- `test_stage646.py`: numerische Codes, Typisierung, `Message`, `THROW e`, VFS-Quelle, Assembler/COFF.
- `test_stage646_dialog_ui.py`: Schrift-Fallback-Reihenfolge, gemeinsame Schriftfamilie, Titelcursor, 24px-Spaltenzugabe, unveränderte übrige Cursor und VFS-Verknüpfung.
- Regression: Tests Stage 639–646. Native Windows-GUI-Interaktion und tatsächliche Ausführung der neu erzeugten EXEs wurden **nicht** in diesem Linux-Testcontainer durchgeführt.

## Build

`build_and_deploy_dbase_editor_stage646.bat` baut `libd64_qt5.dll` über `d64qt5/build_d64qt5_mingw32.bat` und kopiert sie in `runtime/dbase/pe32`. Änderungen an Compiler und Runtime-PRG erfordern außerdem ein erneutes Kompilieren/Linken der betroffenen dBASE-Programme und Neuaufbau der entsprechenden Runtime-Komponenten.
