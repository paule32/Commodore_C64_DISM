# Stage 655 – Projektbezogene Turbo-Hilfe und Konsole-Viewer

Verbindliche Grundlage: `d64_dism_stage654.zip`.

## F2: Name und Verzeichnis

Der Menüpunkt **Werkzeuge → Hilfecompiler** bleibt in der Python-Anwendung `dBase2Many` (`d64_dism.py`). Beim Kompilieren mit **F2** gilt:

- In **Projekt-Informationen → Projektname** muss das **dBASE-Programmprofil** ausgewählt sein, z. B. `Programm: AppDB`.
- Der Projektname wird über die existierende Projekt-Profilverwaltung (`project_named_targets.profile_name`) ermittelt, nicht aus Namen oder Reihenfolge der `.thlp`-Tabs.
- Das Ausgabeverzeichnis stammt aus **Projekt-Einstellungen → dBASE → Ausgabe-Verzeichnisse → EXE/DLL** für die jeweils aktive Windows-PE-Architektur.
- Bei `AppDB.exe` entsteht `AppDB.hlp` direkt im selben Ausgabeordner. **F2 benötigt nicht, dass die EXE bereits existiert.**
- Die Zwischenstufe heißt `AppDB.po` und wird im Ordner der ersten `.thlp`-Quelle geschrieben. Weitere `.thlp`-Quellen bilden zusammen einen Katalog. Aus ihnen wird **keine** `Quelle.hlp` mehr erzeugt.
- Wenn der Zielordner nicht konfiguriert ist, wird wie beim bestehenden dBASE-EXE-Linkpfad das aktuelle Projekt-/IDE-Arbeitsverzeichnis (`current_directory`) benutzt.
- Die aktive dBASE-Dokumentarchitektur (`pe32`/`pe64`) bestimmt den Ausgabeordner. Ist kein entsprechendes Dokument aktiv, wird ein eindeutiger konfigurierter PE-Ausgabeordner verwendet, andernfalls ein vorhandenes EXE-Ziel bevorzugt und schließlich PE32 als Fallback gewählt.
- Ist kein dBASE-Programm in der Projektname-ComboBox gewählt, erscheint eine Fehlermeldung **ohne** willkürliche Benennung nach der `.thlp`-Quelle.

Die bestehende Linkzeit-Erzeugung bleibt aktiv und legt den Katalog neben die tatsächlich gelinkte dBASE-EXE.

## Qt5-Bridge: Hilfe-Fenster in `Konsole`

`DBaseQtHelpShowMo(nullptr)` wird weiterhin per globalem F1 und dem Menü **Hilfe → Inhalt** aufgerufen. Die Bridge lädt `<EXE-Stamm>.hlp` aus dem realen Verzeichnis der laufenden EXE.

- Die Hilfe wird als **Kind von `g_console->viewport()`** erzeugt, nicht mehr im DEBUG-Viewport.
- Der Aufruf wechselt bei Bedarf in den Tab **Konsole**.
- Die hellere cyanfarbene Titelleiste, die Navigation, die Schließfläche, der Doppelklick zum Maximieren und der Resize-Griff sind unverändert.
- Vertikaler und horizontaler Scrollbalken sind dauerhaft eingeblendet (`Qt::ScrollBarAlwaysOn`) – im Hilfe-Textbrowser und in den beiden Haupt-Tabs `Konsole` und `DEBUG`.
- Normale Ausgabe im DEBUG-Tab ist **hellgrau** (`#d3d3d3`), auch wenn sie mit der bestehenden `append_text()`-Funktion geschrieben wird. Die individuell einstellbare farbige Konsolenausgabe bleibt unverändert.
- Ein separater `turbo_help_host.exe` wird weiterhin **nicht** verwendet oder erzeugt.

## Geänderte Dateien

- `d64_dism.py`: Projektname/PE-Ausgabeordner als F2-Ziel ermitteln und an Editor binden
- `turbo_help_gui.py`: F2 benötigt den Projektnamen; keine Ausgabe nach `.thlp`-Stem
- `turbo_help_sidecar.py`: gemeinsame Ausgabe von `<Projekt>.po` und `<Projekt>.hlp` auch ohne existente EXE
- `d64qt5/d64qt5_bridge.cpp`: F1-Hilfe in `Konsole`, DEBUG-Farbe, immer sichtbare Scrollleisten
- `d64qt5/d64_turbo_help_window.hpp`: Viewer im Konsolen-Viewport und immer sichtbare Scrollleisten
- `build_and_deploy_dbase_editor_stage655.bat`: neuer nativer Bridge-Build ohne Host
- `test_stage655.py`: projektbezogene F2-/HLP- und Konsolen-Regressionstests

## Tests / Einschränkungen

- `test_stage655.py`: **6 bestanden**.
- `test_stage651.py`, `test_stage652.py`, `test_stage653.py`: **22 bestanden** nach Anpassung überholter Erwartungen zur DEBUG-Platzierung und Dateibenennung.
- `python -m py_compile turbo_help_sidecar.py turbo_help_gui.py test_stage655.py`: erfolgreich.
- Vollständige native Windows-/Qt5-Kompilierung und interaktive Sichtprüfung sind unter dieser Linux-Testumgebung nicht verfügbar.

Neubau unter Windows:

```bat
build_and_deploy_dbase_editor_stage655.bat
```

Beim Kopieren in ein anderes Runtime-Ziel kann der Zielordner als erstes Argument übergeben werden.
