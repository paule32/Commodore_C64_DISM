# Stage 626 – Turbo-Vision-Editor und virtuelles Dateisystem

**Verbindliche Basis:** `d64_dism_stage625.zip`.

## Funktionsumfang

Die normale dBASE-PE32-Anwendung besitzt innerhalb der `QPlainTextEdit`-Konsole
jetzt zwei voneinander getrennte Fenster:

* das grüne Turbo-Vision-Ausgabefenster aus Stage 622–625,
* den neuen blauen **Turbo-Vision-Editor** (`D64TurboEditorWidget`).

Den Editor öffnen **Datei → Neu** oder **Datei → Öffnen...**. Er nimmt Tastatur-
und Texteingaben an und zeigt in seiner linken unteren Statuszeile die
**1-basierte Cursorposition `Zeile : Spalte`**. Die Zeichenfläche ist blau
(`#0000aa`), die Textfarbe weiß (`#ffffff`), der doppelte Rahmen gelb
(`#ffff55`). Seine Titelleiste ist mit der Maus in *ganzen DOS-Zeichenzellen*
verschiebbar. Der vorhandene Zoom aktualisiert Schrift und Fensterraster.

Die Menüleiste enthält **Bearbeiten** mit:

| Menüeintrag | Shortcut |
|---|---|
| Rückgängig | Strg+Z |
| Wiederherstellen | Strg+Y |
| Ausschneiden | Strg+X |
| Kopieren | Strg+C |
| Einfügen | Strg+V |
| Löschen | Entf |
| Alles auswählen | Strg+A |

Zwischen Wiederherstellen und Ausschneiden befindet sich ein Trenner.
Die vorhandenen Einträge **Datei → Speichern** (Strg+S) und
**Datei → Speichern unter...** (Strg+Umschalt+S) sind mit dem Editor verbunden.
Bei einer neuen Datei sowie bei **Speichern unter...** erscheint der Dateidialog;
bereits bekannte Pfade werden durch **Speichern** direkt aktualisiert.
Vor **Neu**, **Öffnen** und dem regulären Beenden fragt der Editor bei
ungespeicherten Änderungen nach.

## Dateidialog

Der Dialog `D64VirtualFileDialog` enthält:

* **Links** eine anklickbare Verzeichnisliste mit
  **Meine Dokumente**, dem übergeordneten Verzeichnis und vorhandenen
  Unterordnern. Standard-Qt-Ordner-Icons kennzeichnen Verzeichnisse.
* **Rechts** eine Dateiliste (`QTreeWidget`) mit Name, Typ, Größe und
  Datei-Icons.
* **Dazwischen** einen horizontalen, frei verschiebbaren `QSplitter`.
* Oberhalb einen Suchfilter für Dateien des aktuell angezeigten Ordners.
* **Darunter** ein Dateinameneingabefeld und die Buttons **OK**, **Abbrechen**,
  **Hilfe**. Hilfe erläutert die Navigation und zeigt den gemappten Hostpfad.

## Mapping des virtuellen Dateisystems

Nach `DBaseQtInitialize` wird automatisch ein **festes, pro EXE getrenntes
Host-Verzeichnis** erzeugt und in `D64ApplicationVfs` gespeichert. Die Zuordnung
verwendet `QStandardPaths::AppLocalDataLocation`, das bereinigte EXE-Basename
und einen SHA256-Präfix des vollständigen ausführbaren Dateipfads:

```
<AppLocalDataLocation>/dBase2Many/Anwendungen/<EXE-Name>-<Hash>/
└── Dokumente/               (im Dateidialog: Meine Dokumente)
```

Der genaue Hostpfad wird über den **Hilfe**-Button im Dateidialog angezeigt.
Jeder regulär erneut gestartete EXE-Pfad bekommt wieder dieselbe Zuordnung.
Unterschiedliche EXE-Pfade werden getrennt, auch wenn die Namen identisch sind.

Die Editor-Dateioperationen akzeptieren **nur virtuelle relative Pfade**.
Absolute Pfade, `..`-Komponenten, Symlinks und Pfade außerhalb der Zuordnung
werden zurückgewiesen; vor Öffnen, Speichern und Verzeichnislisten wird die
Zuordnung erneut überprüft. Es wird UTF-8 gelesen und geschrieben; Schreiben
verwendet `QSaveFile` für atomaren Austausch. Bestätigungen verhindern
unbeabsichtigtes Überschreiben.

**Geltungsbereich:** Diese Pfadbegrenzung gilt für die **neuen Dateioperationen
des Editors**, nicht als globale Betriebssystem-Sandbox für bestehende dBASE-
Routinen, DBF-/SQL-APIs oder andere alte Runtime-Dateizugriffe.

## Geänderte bzw. ergänzte Dateien

* `d64qt5/d64qt5_bridge.cpp` – Menüaktionen, Editorinstanz, Zoom, VFS-Init.
* `d64qt5/d64qt5_bridge.pro` – neues Headerfile im Qt-Projekt.
* `d64qt5/d64_turbo_editor.hpp` – Editor, Dateidialog, VFS.
* `build_and_deploy_dbase_editor_stage626.bat` – Qt5-DLL bauen/deployen.
* `tests/test_stage626_turbo_editor.py` – statische Integrationsprüfungen.

## Installation

1. Alle laufenden EXE-Dateien schließen, die `libd64_qt5.dll` verwenden.
2. `build_and_deploy_dbase_editor_stage626.bat` auf Windows mit
   **Qt5/MinGW32** ausführen.
3. Die dBASE-EXE erneut starten; über **Datei → Neu** den Editor öffnen.
4. Text schreiben, `Datei → Speichern unter...` öffnen, im virtuellen
   `Meine Dokumente` z. B. `notiz.txt` eingeben und **OK** drücken.
5. Mit **Datei → Öffnen...** wieder öffnen; Editieraktionen/Status prüfen.

**Tests:** Python-/Quelltext-Regressionstests und ZIP-Integrität können hier
geprüft werden. Der native Windows-Qt5-DLL-Build und die grafische Bedienung
müssen auf der Zielplattform bestätigt werden.
