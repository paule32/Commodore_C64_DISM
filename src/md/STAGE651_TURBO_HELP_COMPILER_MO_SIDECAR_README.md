# Stage 651 – Turbo-Vision-Hilfecompiler und GNU-MO-Hilfe im DEBUG-Fenster

**Verbindliche Basis:** `d64_dism_stage650.zip`.

## Architektur

- `d64_dism.py`: Menü **Werkzeuge → Hilfecompiler**; der Compiler-Editor liegt im dBase2Many-Workspace.
- `turbo_help_gui.py`: Hilfe-Texteditor mit **F2**, Öffnen, Neu und Speichern; F2 kompiliert die aktuellen sichtbaren Inhalte und öffnet den Bridge-Viewer. F2 anderer Editoren wird nicht verändert.
- `turbo_help_compiler.py`: `%include "datei"` bzw. `%include <datei>`, `%topic "id"`, `%ref "thema" #anker`, `%link "thema"` sowie `%anchor #anker` (Sprungziel). Schreibt standardkonforme gettext-`.po` und binäre GNU-`.mo` ohne `msgfmt`. `msgid` ist die Topic-ID, `msgstr` der Themeninhalt.
- `turbo_help_bridge_host.py`: startet den passenden nativen Qt5-Bridge-Viewer als separaten Prozess für die direkte F2-Vorschau (vermeidet Qt-Runtime-Kollisionen von 64-Bit-Python und MinGW32-Qt5).
- `d64qt5/d64_turbo_help_window.hpp`: cyanfarbenes, verschiebbares Hilfe-Fenster **im DEBUG-Viewport** mit heller Titelleiste, Schließen-Schaltfläche, Doppelklick-Maximieren/Wiederherstellen, blauen unterstrichenen Links, internen Ankern, Themenwechsel ohne neues Fenster.
- `d64qt5/d64qt5_bridge.cpp`: **kein Compiler**, nur GNU-MO-Reader und Runtime-Hilfeanzeige über `DBaseQtHelpShowMo`.

## Begleitdatei neben der erzeugten Windows-EXE

Nach erfolgreichem PE32-/PE64-Linken eines dBASE-Hauptprogramms stellt die Python-Anwendung, falls ein Hilfekatalog kompiliert oder dem Projekt als `System.Help.mo` beigelegt wurde, folgende Dateien bereit:

```text
MeinProgramm.exe
MeinProgramm.mo             <- eigener GNU-MO-Hilfekatalog
libd64_qt5.dll
[Qt5-Laufzeitdateien]
```

Die `.mo` wird **nicht** in die EXE oder COFF-Objektdateien eingebettet. Die ursprüngliche `System.Help.mo` und die bearbeitbare `System.Help.po` bleiben im Hilfe-Quellverzeichnis.

Die Bridge bestimmt das Hilfeverzeichnis mit `QCoreApplication::applicationFilePath()`, also **aus dem tatsächlich laufenden EXE-Image**, nicht aus dem aktuellen Arbeitsverzeichnis. `DBaseQtHelpShowMo(nullptr)` oder `DBaseQtHelpShowMo("")` öffnet der Reihe nach:

1. `<EXE-Stamm>.mo` neben der laufenden EXE;
2. `System.Help.mo` neben der laufenden EXE (manuell beigelegter Katalog).

Ein relativer Dateiname wird ebenfalls im EXE-Verzeichnis gesucht; ein absoluter UTF-8-Pfad wird unverändert verwendet (Vorschau/Host).

Im nativen Turbo-Vision-Menü **Hilfe → Inhalt** kann die bereits kompilierte EXE diesen Katalog anzeigen. `Hilfe → Über ...` bleibt unverändert, hat aber kein Kontextmenü mehr.

## Beispiel `System.Help.thlp`

```text
%topic "index"
<b>Turbo Vision Hilfe</b>
%link "Kapitel 2"
%ref "Kapitel 2" #anker1
%include "kapitel2.thlp"
```

`kapitel2.thlp`:

```text
%topic "Kapitel 2"
%anchor #anker1
<b>Kapitel 2</b> – der Inhalt.
%link "index"
```

Die Binärdaten bleiben standardkonforme GNU-MO-Daten (`gettext.GNUTranslations` liest sie); die Qt5-Bridge liest den Katalog selbst und interpretiert ausschließlich den erlaubten Markup-Teil `<b>`, `<ref>`, `<link>` und `<anchor>`.

## Build

Unter Windows mit MSYS2 MinGW32 und Qt5:

```bat
build_and_deploy_dbase_editor_stage651.bat
```

Das Batch-Skript baut `libd64_qt5.dll`, erzeugt `turbo_help_host.exe` und kopiert beides standardmäßig nach `runtime\dbase\pe32`. Für andere Ausgabeverzeichnisse kann das Ziel als erstes Argument übergeben werden. Die passenden Qt5-Laufzeitdateien sind weiterhin erforderlich.

## Tests / Einschränkungen

- `pytest -q test_stage651.py`: **11 bestanden** (GNU PO/MO, Includes/Links, Integrationsstellen, EXE-Sidecar und ungültige Dateien).
- `pytest -q test_stage650.py test_stage631.py test_stage634.py test_stage635.py test_stage636.py test_stage637.py`: **46 bestanden**.
- `pytest -q test_stage650.py test_stage651.py test_stage649.py -k 'not generated_include_name_original_lines_and_unchanged_exports'`: **21 bestanden, 2 gezielt ausgelassen** (große DLL-Linktests).
- Ein vollständiger Qt5-/MinGW32-Build und nativer Windows-Laufzeittest waren in dieser Umgebung nicht möglich.
- Das Öffnen des Help-Compilers mit F2 und die Vorschau starten keinen dBASE-Programm-Build; die Sidecar-Kopie erfolgt beim **nächsten** erfolgreichen EXE-Linken.
