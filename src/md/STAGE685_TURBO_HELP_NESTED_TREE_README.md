# Stage 685 – Verschachtelte Turbo-Hilfe / getrennte Eingabe-Verzeichnisse

**Verbindliche Basis:** `d64_dism_stage684.zip`.

## Projekt-Informationen → Turbo Hilfe

- Der Hauptknoten heißt jetzt **Turbo Hilfe**; er kann selbst nicht gelöscht oder umbenannt werden.
- Ordner und Unterordner lassen sich beliebig verschachteln; sie verwenden das native Ordner-Icon von Qt.
- Das Rechtsklick-Kontextmenü zeigt **in der gewünschten Reihenfolge**:
  `Haupt-Eintrag`, `Inhalt hinzufügen`, `Datei umbenennen`, `Inhalt löschen`, Trennlinie, `Ordner umbenennen`, `Ordner hinzufügen`, `Ordner löschen`.
  Nur die für den jeweiligen Knotentyp passenden Einträge sind aktiv.
- Blätter verfügen links vom Datei-Icon über eine Qt-Checkmarkierung. **Haupt-Eintrag** setzt die Markierung exklusiv. Ein anderer Haupt-Eintrag ersetzt den bisherigen.
- **Inhalt hinzufügen** fragt nach dem `.thlp`-Dateinamen, erstellt die Datei im ersten unter **Turbo Hilfe** konfigurierten Eingabe-Verzeichnis bzw. seinem gewählten Unterordner und fügt erst nach erfolgreichem Schreibvorgang das Blatt in den Baum ein. Fehlt das Eingabe-Verzeichnis oder scheitert das Schreiben, erscheint eine Dark-Mode-taugliche Warnung; es entsteht kein Phantomblatt.
- **Ordner hinzufügen** legt den Ordner sowohl im Baum als auch auf der Festplatte an. Pfad-Traversal, ungültige Namen und Namenskollisionen werden abgefangen.
- **Datei/Ordner umbenennen** benennt die tatsächliche Datei bzw. das Verzeichnis um und aktualisiert betroffene Projektknoten und offene Editor-Tabs. Externe Dateien in eingebundenen Verzeichnissen bleiben am bestehenden Speicherort.
- **Inhalt löschen** und **Ordner löschen** entfernen nur die Projektbaum-Zuordnung, beim Ordner einschließlich sämtlicher Unterknoten. **Gespeicherte Dateien und Verzeichnisse werden dabei nicht von der Festplatte gelöscht.** Bereits offen gehaltene, explizit entfernte Hilfedateien werden bei einem erneuten Speichern nicht stillschweigend wieder eingetragen.

## Projekt-Einstellungen → Compiler → dBASE → Eingabe-Verzeichnis

- GroupBox **Entwicklung:** mit den bereits vorhandenen Suchverzeichnis-Einstellungen.
- Unabhängige GroupBox **Turbo Hilfe:** mit relativen/absoluten Pfaden, Eingabezeile, Durchsuchen, ListBox und Hinzufügen/Löschen/Alle löschen/Hoch/Runter.
- Die dBASE-Eingabeseite ist scrollbar; beide Gruppen bleiben bei kleiner Fensterhöhe zugänglich.
- Der erste Eintrag unter **Turbo Hilfe** ist das Stammverzeichnis für die `.thlp`-Baumstruktur; weitere Einträge werden als zusätzliche Include-Suchverzeichnisse berücksichtigt.
- Verzeichnisse und relativer Pfadmodus werden **getrennt von Entwicklung und getrennt für PE32/PE32+** in der `.pro`-Datei gespeichert.

## Projektformat und Hilfecompiler

- `Category.TurboHelp` speichert `kind`, `parent`, `title`, `path` und `main` je Knoten. Alte flache `ItemNNNN`-Einträge ohne `kind` bleiben lesbar.
- Die Hilfe-Komprimierung ist hier kein Thema: der bestehende PO→HLP/MO-Workflow bleibt erhalten.
- F2 und die automatische EXE-Hilfeerzeugung sammeln die registrierten `.thlp`-Blätter **rekursiv**. Das einzige als Haupt-Eintrag markierte Blatt wird als erste Quelle eingelesen. Ohne einen eindeutig markierten Haupt-Eintrag wird keine neue Hilfe generiert.
- `%include "unterordner/datei.thlp"` verwendet zuerst den Pfad relativ zur einbindenden Datei, dann die Hilfe-Suchpfade, anschließend eindeutige bekannte Projektblätter. Mehrdeutige gleichnamige Blätter, fehlende Dateien, unzulässige Pfade und Include-Zyklen führen zu einem nachvollziehbaren Fehler.
- Historisches `%include "test.tlhp"` kann ersatzweise eine existierende `test.thlp`-Datei finden, wenn es keine gleichnamige `.tlhp`-Datei gibt.
- Das Hauptthema `%topic "index"` bleibt für die Laufzeit-Hilfe erforderlich. Der erzeugte HLP-Katalog erhält weiterhin den ausgewählten EXE-Namen.

## Dateien

- `d64_dism.py`: neue Tree-Node-Rollen, Kontextmenüaktionen, Speichern/Laden der Baumhierarchie und Turbo-Hilfe-Suchpfade, Hauptdokumentauswahl, F2-/Link-Integration sowie GroupBox/Scrollbereich.
- `turbo_help_path_widgets.py` (neu): eigenständige Turbo-Hilfe-Pfadverwaltung.
- `turbo_help_project_tree.py` (neu): validierte Namen/Pfade, eindeutiger Haupt-Eintrag, Include-Auflösung.
- `turbo_help_gui.py`: Hauptdokumentprüfung vor einem ungewollten Save-As, F2-Projektquellen.
- `turbo_help_compiler.py`: Hauptquelle, Include-Pfade, rekursive und eindeutige Dateiauflösung.
- `turbo_help_sidecar.py`: Projekt- und Linkzeit-Kompatibilität mit optionalem Hilfe-Stammverzeichnis.
- `test_stage685.py`: neue Unit- und Integrationstests.

## Prüfung

```sh
python -m pytest -q test_stage685.py test_stage654.py test_stage662.py test_stage663.py test_stage683.py test_stage684.py
```

Die relevanten Tests prüfen den Help-Kompilier-Roundtrip mit verschachtelten Includes und `.hlp`-Output, Dateinamen-/Traversal-Schutz, fehlende Hauptmarkierung, doppelte Includes und eine Qt-freie Simulation der echten QTreeWidgetItem-Funktionen. Zusätzlich werden bestehende Editor-/Dock- und Settings-Regressionstests ausgeführt.

**Einschränkung:** Die Windows-PyQt5-Oberfläche ist in der Testumgebung nicht installiert; Sichtprüfung und echter F2-Tastendruck unter Windows müssen auf dem Zielsystem erfolgen. Der Projektstand enthält unverändert die Python-3.15-Lazy-Import-Syntax (`lazy from ...`); für die Syntaxkontrolle unter dem vorhandenen Python 3.13 wurde ausschließlich eine temporäre, nicht gespeicherte Normalisierung dieser Imports verwendet.
