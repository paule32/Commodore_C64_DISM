# Stage 554 – Software Installer: ein einziges Dock mit horizontalem Splitter

## Verbindliche Grundlage

Stage 553 (`d64_dism_stage553.zip`) wurde vollständig übernommen. Die UI-Struktur des Software Installers wurde nach Anwenderwunsch geändert; die bestehenden Datenmodelle, Tabellenaktionen, Einstellungsdialoge, Filterregeln sowie das `.installer.json`-Format bleiben erhalten. Es wird weiterhin noch kein ausführbares Installationspaket erzeugt.

## Aufbau

```
QMainWindow (bestehende d64_dism-IDE)
└── QDockWidget("Software Installer")       # EINZIGES Installer-Dock der IDE
    └── SoftwareInstallerWorkbench(QWidget)  # kein QMainWindow mehr
        └── QVBoxLayout
            ├── QToolBar "Software Installer Filter"  [fest]
            │   ├── QComboBox "Filter"
            │   ├── Installer-Projekt öffnen ...
            │   └── Installer-Projekt speichern ...
            └── QSplitter(Qt.Horizontal)
                ├── QScrollArea "Dateien"     [anfangs ca. 25 %]
                │   ├── Dateien
                │   ├── Einstellungen
                │   ├── Bildschirme
                │   └── Aktionen
                └── QTabWidget                  [anfangs ca. 75 %]
                    ├── Archiv  -> InstallerTable
                    └── Extern  -> InstallerTable
```

Die Haupt-IDE besitzt weiterhin genau ein äußeres Installer-`QDockWidget`, das sich am linken oder rechten Rand andocken lässt. Es gibt **keine** inneren `QDockWidget`s mehr: Der Benutzer verändert die relative Breite beider Bereiche über den Splitter. Die Toolbar bewegt sich dabei nicht.

Der Splitter wird beim erstmaligen Anzeigen auf ungefähr 25 % / 75 % eingestellt. Eine vom Benutzer gewählte andere Aufteilung wird beim erneuten Öffnen desselben Dock-Widgets nicht zurückgesetzt. Beide Seiten haben Mindestbreiten; bei sehr schmalem Hauptfenster kann die Aufteilung daher von 25 % / 75 % abweichen.

Wenn das Installer-Dock geöffnet wird, blendet `_activate_exclusive_tool_workspace` die vorhandenen anderen Docks aus. Beim Schließen stellt die bestehende Workspace-Verwaltung die vorherige IDE-Anordnung wieder her.

## Dark-/Light-Theme

`SoftwareInstallerWorkbench.set_dark_mode()` gestaltet die feste Toolbar, den Splittergriff, die aufklappbaren Gruppen, Tabellen und Tab-Leiste. Der IDE-weite Themewechsel ruft diese Methode unverändert auf.

## Geänderte Dateien

- `software_installer.py`: `SoftwareInstallerWorkbench` von `QMainWindow` nach `QWidget` umgestellt; feste `QToolBar`, `QVBoxLayout`, `QSplitter(Qt.Horizontal)`; alte inneren Docks und deren Style entfernt.
- `d64_dism.py`: Beim Öffnen werden keine inneren Docks mehr angezeigt; das bestehende äußere Dock und die Workspace-Verwaltung bleiben erhalten.
- `test_stage553.py`, `test_stage553_qt.py`: Strukturerwartungen an das neue Layout angepasst; zusätzlicher Widgettest für das Resizing.
- `test_stage554.py`: Neue Qt-freie Struktur- und Integrationstests.

## Tests

In der Prüfumgebung:

```
python -m unittest -q test_stage552 test_stage550 test_stage553 test_stage554 test_stage553_qt
# Ran 48 tests ... OK (skipped=5)
```

**43 Tests erfolgreich**, **5 GUI-Tests übersprungen** (PyQt5 nicht installiert). Syntax von `software_installer.py` geprüft; die große `d64_dism.py` verwendet bereits vor dieser Änderung Python-`lazy from`-Importsyntax, die der hier verfügbare Python-Interpreter nicht parsen kann. Die `d64_dism.py`-Änderung beschränkt sich auf die bereits vorhandene Methode und Kommentare/Menütext.

## Windows-Qt-Praxistest

1. IDE starten, mehrere Dockfenster öffnen, `Erstellen -> Software Installer` aufrufen.
2. Sicherstellen, dass nur **ein** Installer-Dock sichtbar ist (kein zusätzliches verschachteltes Hauptfenster).
3. Obere Filterleiste bleibt fest, wenn die linke/rechte Splitterposition verschoben wird.
4. Vier Gruppen auf-/zuklappen, beide Tabellen über das Kontextmenü bearbeiten, Filter wechseln.
5. Installer-Projekt speichern/laden, Dark-/Light-Modus wechseln.
6. Dock schließen und prüfen, dass die vorherige IDE-Anordnung wiederhergestellt wird.

Die native PyQt5-Darstellung unter Windows konnte in dieser Umgebung nicht ausgeführt werden.
