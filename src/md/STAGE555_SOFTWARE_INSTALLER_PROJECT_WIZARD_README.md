# Stage 555 – Software Installer: Projektstart, Registrierung, Wizard und Speichern

**Verbindliche Basis:** `d64_dism_stage554.zip` (1.436 enthaltene Einträge).  
**Ziel:** Die bereits vorhandene Single-Dock-Oberfläche bleibt erhalten. Neu sind eine dark-/light-fähige Projektauswahl, eine globale JSON-Projektliste, die Wizard-Seiten und der Speichern-unter-Pfad für „Unbenannt“.

## Aufbau

Der Installer bleibt **ein** äußeres `QDockWidget` in der IDE. Darin liegt eine feste `QToolBar` über einem horizontalen Splitter: links vier einklappbare Gruppen, rechts die Tabellen „Archiv“ und „Extern“. Keine zusätzlichen QMainWindows oder inneren DockWidgets.

Die Toolbar-Aktionen **Installer Projekt öffnen ...** und **Installer Projekt speichern ...** sind mit Dark-/Light-Styles für ihre `QToolButton`-Widgets versehen.

## Projektstart

Klick auf **Installer Projekt öffnen ...** öffnet `InstallerProjectStartDialog` mit Titel **Neues Projekt starten**, Qt-Theme sowie der nativen dunklen Windows-Titelleiste über DWM (Windows 10/11, soweit unterstützt).

- `Neues Projekt erstellen`: Standardauswahl; die eingerückte Checkbox `start mit Wizard` ist bedienbar; Liste und „Suchen“ sind deaktiviert.
- `Vorhandenes Projekt öffnen`: Liste und „Suchen“ sind bedienbar; die Wizard-Checkbox ist deaktiviert. **Der zweite RadioButton bleibt dabei immer anklickbar**, sonst könnte man nicht von „Neu“ zu „Vorhanden“ wechseln.
- `Suchen`: Auswahl einer vorhandenen `.installer.json`, Prüfung des Projektformats und Übernahme als auswählbarer Listeneintrag.
- `OK`: Neues leeres Projekt bzw. selektiertes vorhandenes Projekt laden.
- `Abbrechen`: Leeres Projekt **Unbenannt**, ohne Dateipfad, mit `needs_save_as=True` bereitstellen.
- `Hilfe`: CHM-Viewer mit Thema **Neues Projekt starten**.

Bei vorhandenen Änderungen des bisher aktiven Installer-Projekts fragt das System vor einem Projektwechsel nach Speichern, Verwerfen oder Abbrechen. Ein abgebrochener Wechsel verliert keine Datei.

## Wizard

Wenn „Neues Projekt erstellen“ und „start mit Wizard“ aktiv sind:

1. Dialog **Allgemeine Informationen** mit den Labels und Platzhaltern: `Wie heißt Ihre Firma` / `Ihre Firma`, `Produktname oder Titel` / `Ihr Produkt`, `Produkt Version` / `1.0`, `Firmen Internetseite` / `https://www.firma.de`. Darunter eine Linie und `< Zurück` (deaktiviert), `Weiter >`, `Abbrechen`, `Hilfe`.
2. `Weiter >` öffnet den weiteren Dialog **Installationsverzeichnis**, damit die Wizard-Navigation durchlaufen werden kann. Da für Seite 2 noch kein konkretes Layout vorgegeben war, enthält sie zunächst nur das Installationsziel und die Bedienung `< Zurück`, `Fertigstellen`, `Abbrechen`, `Hilfe`. Die bisherigen Eingaben bleiben bei „Zurück“ erhalten.
3. `Fertigstellen` übernimmt die Eingaben in `InstallerProject.general`, **speichert aber noch keine Datei**. Das Projekt heißt bis zum ersten Speichern weiterhin „Unbenannt“.
4. `Abbrechen` auf einer Wizard-Seite erstellt das leere, ungespeicherte Projekt „Unbenannt“.
5. `Hilfe` ruft `ExplorerWindow.show_software_installer_help(topic)` auf und navigiert im vorhandenen CHM-Viewer zu **Wizard Seite 1** oder **Wizard Seite 2**. Für die Themen sind `help/software_installer/installer.hhc`, `.hhk`, `.hhp` und HTML-Dateien beigefügt. Liegt später eine kompilierte `help/software_installer.chm` vor, wird diese bevorzugt, andernfalls der Hilfe-Quellbaum benutzt. Der Viewer selbst setzt PyQtWebEngine voraus.

## Projektdateien und globale Liste

`InstallerProject` bleibt im bestehenden Format `d64-software-installer`, Version `1`. Neue optionale Felder `name` und `general` (Firma, Produkt, Version, Website, Installationsziel) sind **rückwärtskompatibel**; alte `.installer.json`-Dateien lassen sich weiterhin laden.

Die globale Projektliste wird als

`<Verzeichnis der IDE-EXE>/software_installer_projects.json`

geschrieben (im Python-Quellbetrieb neben `d64_dism.py`). Darin stehen pro Projekt Name, absoluter Pfad, gespeicherter Projektstand unter `settings` und Zeitstempel `saved_at`. Die Dateiliste zeigt nur Einträge, deren einzelne Projektdatei tatsächlich noch vorhanden ist. Ein über „Suchen“ geladenes gültiges Projekt wird ebenfalls in die Liste aufgenommen.

Bei erstmaligem Speichern über Installer-Toolbar oder `Strg+S` fragt ein Dark-Mode-fähiger **Speichern-unter-Dialog** nach dem Projektnamen und schreibt anschließend nach

`<Verzeichnis der IDE-EXE>/installer_projects/<Projektname>.installer.json`

Der Eingabename wird auf ungültige Windows-Dateizeichen und reservierte Gerätenamen geprüft. Vorhandene Projektdateien werden **nicht still überschrieben**. Ein vorhandenes Projekt wird bei erneuter Speicherung am bekannten Dateipfad aktualisiert; derselbe Registry-Eintrag wird ohne Dopplung ersetzt.

Projektdatei und Registry werden jeweils über temporäre Dateien + `fsync` + `os.replace` aktualisiert. Schlägt die globale Registry-Aktualisierung fehl, wird dies gemeldet, ihr bisheriger Inhalt bleibt erhalten und `_registry_pending` sorgt dafür, dass der Vorgang beim nächsten Speichern erneut versucht wird.

`Strg+S` verwendet unverändert die zentrale `save_all_open_documents()`-Routine aus Stage 547; der Installer ist jetzt ein weiterer darin berücksichtigter Projekttyp. Die bisherigen Editor-Dokumente bleiben im selben Lauf enthalten. Die IDE zeigt einen Fehlschlag korrekt an und schützt den Installer beim Beenden vor unbeabsichtigtem Verlust.

## Änderungen

- `software_installer_model.py`: Projektname/Allgemeine Daten und `InstallerProjectRegistry` ergänzt.
- `software_installer_dialogs.py`: neue Start-, Wizard- und Speichern-unter-Dialoge; Stylesheet und Windows-DWM-Titelleiste.
- `software_installer.py`: Toolbar-Buttons thematisiert, Modaldialoge, Registry, `Unbenannt`, Dirty-Status und JSON-Speicherung.
- `d64_dism.py`: `Strg+S`, Verlassen, Hilfenavigation und Aktionszustände integriert.
- `help/software_installer/*`: kontextsensitiver Hilfe-Quellbaum.
- `test_stage555.py`, `test_stage555_qt.py`: Qt-freie Modell-/Strukturtests und optionale native Qt5-Tests.

## Tests und Grenzen

`python -m unittest -q test_stage550 test_stage552 test_stage553 test_stage554 test_stage555 test_stage553_qt test_stage555_qt`

Ergebnis in der aktuellen Testumgebung: **71 Tests**, davon **61 erfolgreich**, **10 GUI-Tests mangels PyQt5 übersprungen**. Darunter alte Stage-550-Imports, Stage-552-Runtime-Abhängigkeiten und Stage-553-/554-Installer-Regressionen. Die Qt-freien Tests decken JSON-Registry und atomare Fehlerfälle ab; die neuen Dialogquellen sowie die gezielt veränderten MainWindow-Methoden wurden syntaktisch geprüft.

Für den Windows-Praxistest: IDE starten, Dark/Light umschalten, Installer öffnen, Startdialog und Radio-/Suchen-Zustände prüfen, Wizard bis Seite 2 durchlaufen und zurück navigieren, per Abbrechen zu Unbenannt zurückkehren, `Strg+S` verwenden, danach Installer schließen/erneut öffnen und Projekt aus der Liste laden. Hilfe-Button „Wizard Seite 1“ muss in den vorhandenen CHM-Viewer zum entsprechenden lokalen Thema führen.

**Nicht getestet:** Native Windows-Qt-Ausführung, Windows-DWM-Titelleiste und ein eingefrorenes EXE-Bundle. Bei Auslieferung einer gefrorenen EXE müssen die Installer-Hilfe-Dateien als Laufzeitressourcen vorhanden sein. Der Installer ist weiterhin ein Projekteditor; das Erstellen einer lauffähigen Setup-EXE gehört nicht zu dieser Stage.
