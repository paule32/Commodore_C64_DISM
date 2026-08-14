# Datei öffnen Dialog – Stage 31

Stage 31 ersetzt für `Datei -> Öffnen` den nativen `QFileDialog.getOpenFileName()`-Aufruf durch einen eigenen PyQt5-Dateidialog.

## Aufbau

Obere Zeile:
- Zurück
- Vor
- Hoch
- umschaltbare Pfadleiste
  - Breadcrumb-/Button-Ansicht
  - editierbare ComboBox mit vollständigem Pfad
  - Ordnersymbol links in der Eingabezeile zum Umschalten
  - Pfeil-nach-unten rechts der Breadcrumbs für unmittelbare Unterverzeichnisse
- Search-Eingabefeld mit Lupensymbol rechts

Hauptbereich:
- links: Computer-/Verzeichnisbaum
- Mitte: Verzeichnisse und Dateien
- rechts: CheckBox-Liste der unterstützten Dateierweiterungen
- die drei Bereiche liegen in einem horizontalen QSplitter

Die erste Filterzeile lautet `Alle *.*`. Weitere Zeilen sind die unterstützten Erweiterungen. Mehrere Erweiterungen können gleichzeitig aktiviert werden. Der Suchtext filtert sowohl Verzeichnis- als auch Dateinamen.

Unter dem Splitter befindet sich eine ComboBox, die die im aktuellen Verzeichnis sichtbaren Dateien mit vollständigem Pfad enthält. Bei jedem Verzeichniswechsel wird sie gelöscht und neu aufgebaut.

Unten befinden sich `Öffnen` und `Abbrechen`.

## fileName

Vor `accept()` wird `ProjectOpenFileDialog.fileName` mit dem aufgelösten vollständigen Dateipfad gesetzt.

## Projektintegration

Nach erfolgreichem Öffnen wird die Datei über `project_category_for_path()` der passenden Projektkategorie zugeordnet. Falls noch kein Projekt existiert, wird wie bei neuen Projektdokumenten ein `Unbenannt_Projekt_<n>.pro` angelegt. Anschließend wird der Eintrag über `_add_project_entry()` in die Projekt-TreeList übernommen und das Projekt gespeichert.

Projektdateien (`.pro`) werden nicht als Eintrag in sich selbst registriert; sie werden normal geladen.

## Navigation

Vor jedem Verzeichniswechsel wird das bisherige Verzeichnis in die Pfad-ComboBox-Historie aufgenommen. Zurück/Vor führen getrennte Navigationsstapel. Hoch wechselt in das Elternverzeichnis.

## Tests

Neue Regression: `tests/test_custom_open_file_dialog_stage31.py`.
