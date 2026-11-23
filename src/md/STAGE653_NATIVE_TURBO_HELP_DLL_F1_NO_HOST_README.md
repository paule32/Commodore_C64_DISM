# Stage 653 – Turbo-Hilfe vollständig in der Qt5-Bridge, ohne separaten EXE-Host

**Verbindliche Basis:** `d64_dism_stage652.zip`.

## Gewünschte Änderung

`turbo_help_host.exe` wird weder gebaut noch benötigt. Der GNU-MO-basierte
`.hlp`-Viewer liegt in **`libd64_qt5.dll`**, nicht in einem zusätzlichen Prozess.
Konsolenanwendungen, die die dBASE-Qt5-Bridge verwenden, öffnen die Hilfe mit
**F1**, während das Qt5-Konsolen-/DEBUG-Fenster den Tastaturfokus hat.

## Änderungen

- `d64_dism.py`: `_turbo_help_compiled()` speichert den Katalogpfad und meldet
  das Kompilat, **ohne einen separaten Prozess zu starten**. F2 erzeugt wie
  bisher `.po` und `.hlp`; die Laufzeitansicht erfolgt über F1 in der
  gestarteten Turbo-Vision-Anwendung.
- `d64qt5/d64qt5_bridge.cpp`: bereits vorhandener `DBaseQtHelpShowMo()`-Viewer
  ist die einzige native Umsetzung. `QShortcut(Qt::Key_F1)` mit
  `Qt::ApplicationShortcut` öffnet aus Konsole, DEBUG und Eingabefeldern
  `<EXE-Stamm>.hlp` im cyanfarbenen DEBUG-Viewport. AutoRepeat ist deaktiviert.
- `d64qt5/d64_turbo_help_window.hpp`: vorhandene native Darstellung bleibt
  einschließlich Titelleiste, Links, Topicwechsel, Resize-Griff und Schließen.
- `d64qt5/d64qt5_bridge.h`: ABI-Dokumentation berichtigt: das frühere
  Symbol `DBaseQtHelpShowMo` lädt inzwischen `.hlp`.
- `turbo_help_bridge_host.py` und `d64qt5/turbo_help_host.cpp` sind entfernt.
- `build_and_deploy_dbase_editor_stage653.bat` baut **nur** die DLL und
  kopiert sie ins Zielverzeichnis. Eventuell vorhandene alte
  `turbo_help_host.exe`-Artefakte im DLL-Release- und Zielordner werden entfernt.
  Stage-651-/652-Buildskripte delegieren aus Kompatibilitätsgründen an Stage 653,
  um versehentliche Host-Builds zu verhindern.

## Beispiel zur Laufzeit

```text
Bin/
  App.exe
  App.hlp              <- gleicher Name, GNU-MO-Binärformat
  libd64_qt5.dll
```

`App.hlp` wird beim Linken weiterhin anhand des in den Projekt-Einstellungen
konfigurierten dBASE-EXE-/DLL-Ausgabeordners abgelegt. Der C++-Viewer benutzt
`QCoreApplication::applicationFilePath()`, nicht das aktuelle Arbeitsverzeichnis.

Wenn die Qt5-Konsole oder das DEBUG-Tab aktiv ist, öffnet **F1** das Thema
`index` in einem cyanfarbenen Fenster innerhalb des DEBUG-Viewports. Die
Menüaktion `Hilfe → Inhalt` benutzt denselben DLL-Export.

## Bewusste Grenze der F2-Vorschau

Früher startete F2 einen zusätzlichen 32-Bit-Prozess, wenn dBase2Many mit
64-Bit-Python lief. Da der EXE-Host explizit unerwünscht ist und eine
32-Bit-DLL nicht in einen 64-Bit-Python-Prozess geladen werden kann,
**startet F2 keine separate Hilfevorschau mehr**. Es kompiliert die `.hlp`;
anschließend F1 in einer laufenden Turbo-Vision-Anwendung verwenden.

F1 ist ein **anwendungsweiter Qt5-Shortcut**, kein Betriebssystem-weiter Hotkey.
Ein normales `cmd.exe`-Fenster ohne dBASE-Qt5-Laufzeit wird dadurch nicht
abgefangen.

## Testnachweise

- Stage-653-Tests: keine externen Host-Quellen oder Buildpfade, F2 ohne
  Prozessstart, F1 in der Bridge und Ausgabe von `ProjectApp.hlp`.
- Stage-652-/651-Tests auf das aktuelle `.hlp`-Format und die neue
  Host-freie Architektur aktualisiert, übrige bestehende Dialogtests erhalten.
- Nativer MinGW32-/Qt5-Windows-Build und visueller Funktionstest müssen auf
  dem Windows-Entwicklungsrechner ausgeführt werden; in dieser Umgebung ist
  weder `qmake` noch der Windows-MinGW32-Compiler installiert.

## Build

```bat
build_and_deploy_dbase_editor_stage653.bat
```

Optional kann der Pfad des Runtime-Ausgabeordners als erster Parameter
übergeben werden:

```bat
build_and_deploy_dbase_editor_stage653.bat "C:\MeinProjekt\bin"
```
