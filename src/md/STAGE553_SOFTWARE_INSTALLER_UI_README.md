# Stage 553 – Software Installer (PyQt5-Arbeitsbereich)

## Basis und Umfang

Vollständiger Projektstand aus `d64_dism_stage552.zip`. Geändert wurde `d64_dism.py`; neu sind `software_installer.py`, `software_installer_model.py`, `test_stage553.py`, `test_stage553_qt.py` und dieses Dokument.

**Die Erweiterung ist zunächst ein Installer-Projekteditor, kein fertiger Setup-/MSI-Generator.** Aktionen unter „Einstellungen“, „Bildschirme“ und „Aktionen“ speichern momentan editierbare Textkonfigurationen. Ihre spätere Übersetzung in ein ausführbares Installationspaket gehört nicht zu Stage 553.

## Aufruf und Fensterverwaltung

- Hauptmenü **Erstellen → Starten → [Separator] → Software Installer**.
- Beim Öffnen benutzt die IDE die vorhandene `_activate_exclusive_tool_workspace`-Verwaltung: alle anderen **direkt am Hauptfenster angemeldeten** Docks werden ausgeblendet und der zentrale Editorbereich wird vorübergehend verborgen.
- Das äußere Dock **Software Installer** nimmt die verfügbare Fläche ein. Schließen stellt den ursprünglichen IDE-Workspace über `_exclusive_tool_workspace_visibility_changed` wieder her.
- Im äußeren Dock befindet sich ein eigenes `QMainWindow`. Dessen zwei innere QDockWidgets können durch Ziehen ihrer Titelleisten links oder rechts angeordnet werden. **Oben, unten und Floating sind gesperrt.** Anfangsbreiten: ca. **25 % Dateien / 75 % Tabelle**. Der Trennbereich bleibt danach manuell verstellbar.
- Die Dark-/Light-Darstellung folgt der IDE-Einstellung; die Panels, Toolbar, Tabellen und Docktitel erhalten eine passende Palette.

## Linkes Dock: Dateien

Vier vertikal angeordnete, aufklappbare Gruppen. Jede Gruppe besteht aus einem äußeren Rahmen (`InstallerCollapsiblePanel`), einem Kopfbereich mit Überschrift und Pfeil sowie einem separaten Inhaltsbereich mit Icons und linksbündigen Buttons.

1. **Dateien**: Datei hinzufügen, Pfad hinzufügen, Elemente Löschen, Datei Eigenschaften.
2. **Einstellungen**: Session Variable, Hintergrund Fenster, Benötigte Resourcen, Log-Datei, Sicherheit, Packages, Sprachen.
3. **Bildschirme**: Projekt Theme, Vor der Installation, Während der Installation, Nach der Installation.
4. **Aktionen**: OnStartup, OnPreInstall, OnInstallError, OnPostInstall.

Der Pfeil zeigt bei eingeklapptem Panel **nach unten**, bei ausgeklapptem Panel **nach oben**. Eine Scroll-Area hält alle vier Panels auch bei geringer Fensterhöhe erreichbar.

## Rechtes Dock: Archiv und Extern

Ein `QTabWidget` mit exakt zwei Tabs und jeweils einer editierbaren `QTableWidget`. Spalten: `Name`, `Ziel`, `Lokaler Pfad`, `Größe`, `Datum`, `Datei Version`, `Status`, `Package`, `Short Cut`.

Die Kontextmenüs beider Tabellen erlauben **Zeile hinzufügen**, **Datei hinzufügen** und **Ausgewählte Zeilen löschen**. Mehrfachauswahl ist möglich. Die Dateiauswahl befüllt lokale Pfade, Dateigröße, Änderungsdatum und `Vorhanden`/`Fehlt`; Bearbeiten im Tabellenfeld aktualisiert das Datenmodell.

## Obere Filterleiste und Konfiguration

Die oberhalb beider inneren Docks angeordnete Leiste enthält die ComboBox `Filter` mit `Alle Elemente`, `Nur Archiv`, `Nur Extern`, `Vorhandene Dateien`, `Fehlende Dateien`. Die Archiv-/Extern-Filter wählen den entsprechenden Tab; Statusfilter blenden passende Zeilen in beiden Tabellen ein/aus.

Zusätzlich wurden **Installer-Projekt öffnen …** und **Installer-Projekt speichern …** in der Leiste hinzugefügt, damit die eingetragenen Dateien und Konfigurationstexte nicht nur im Arbeitsspeicher existieren. Dateiformat: `.installer.json`, UTF-8, Version 1, atomarer Schreibvorgang. Das ist ein Projektformat; es erzeugt keine Installationsdatei. `Strg+S` der IDE bleibt unverändert (zentrales Dokumentenspeichern); die Installer-Projektdatei wird über die eigene Schaltfläche gespeichert.

## Tests

```bash
python -m unittest -v test_stage553 test_stage553_qt
```

In der Erstellungsumgebung erfolgreich: **13 Modell-/Integrations-/Syntaxprüfungen**. Die **4 zusätzlichen nativen Qt-Widgettests** (`test_stage553_qt.py`) werden hier übersprungen, weil PyQt5 nicht installiert ist. Eine interaktive Prüfung auf Windows (Docking, Mausdragging, Theme, Dateidialoge, GUI-Layout) ist erforderlich; sie wird **nicht** als bestanden behauptet.

## Zu überprüfende Punkte unter Windows

1. Mehrere Editor-Docks öffnen; `Erstellen → Software Installer` klicken; alle bisherigen Docks müssen verschwinden.
2. Dateien-Dock zunächst links (ca. 1/4) und Tab-Dock rechts (ca. 3/4); beide müssen auch auf die jeweils andere Seite ziehbar sein, jedoch nicht oben/unten.
3. Gruppen aus- und einklappen; Status des Pfeils kontrollieren.
4. Je eine Datei im Archiv und Extern anlegen; Filter testen; via Kontextmenü Zeilen löschen.
5. Installer-Konfiguration speichern und erneut öffnen; Inhalte vergleichen.
6. Dark-/Light-Modus während geöffneten Arbeitsbereichs umstellen.
7. Äußeres Dock schließen: ursprüngliche Editor- und Dock-Anordnung muss wiedererscheinen.
