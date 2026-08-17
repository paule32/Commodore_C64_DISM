# Stage 84 – C64-Binary Build, MRU-Dateien und dBase-Formulardesigner

Basis: Stage 83. Die Erweiterungen sind additiv und lassen die vorhandenen Compiler-, Disassembler-, Projekt- und Docking-Pfade bestehen.

## 1. C64-.prg/.bin im Rohdaten-Tab

Binäre C64-Programme werden weiterhin beim Öffnen disassembliert und im Tab `Rohdaten` angezeigt. Dieser Disassembly-Text wird nun als vollwertiger Assemblerquelltext behandelt.

Direkt über dem Eingabe-Editor sind deshalb auch für `.prg` und `.bin` sichtbar:

- `Assemble`
- `Start`
- die vorhandene Zielauswahl
- der vorhandene Assembly-Status

Das Assemblieren benutzt den bestehenden internen MOS-6510-Assembler. Die Originaldatei wird dabei nicht überschrieben. Aus `demo.prg` oder `demo.bin` entsteht beispielsweise:

```text
demo.reassembled.prg
```

`Start` verwendet anschließend dieses erzeugte Programm für den vorhandenen VICE-Startpfad.

Ein Stage-84-Test prüft einen echten Roundtrip:

```text
PRG -> Disassembly -> interner 6510-Assembler -> identische PRG-Bytes
```

## 2. Datei -> Zuletzt verwendete Programme

Unter `Datei` gibt es nun das Untermenü:

```text
Zuletzt verwendete Programme
```

Es enthält maximal die letzten 10 benutzten Programm-/Quelldateien. Die Liste wird über `QSettings` unter `files/recent_programs` dauerhaft gespeichert.

Die zuletzt benutzte Datei steht oben. Ein erneutes Öffnen verschiebt sie wieder an Position 1. Nicht mehr vorhandene Dateien werden beim Anklicken aus der Liste entfernt.

Berücksichtigt werden u. a. C64-, Assembler-, Pascal-, C-, LISP-, PROLOG-, LOGO- und dBase-Dateien. Projekt-, Markdown-, Text- und reine Grafikressourcen werden nicht in diese MRU-Liste aufgenommen.

## 3. Datei -> Neu -> dBase -> Formular

Das dBase-Untermenü besitzt jetzt:

```text
Projekt
Anwendung
Programm
----------------
Formular
```

`Formular` öffnet einen eigenen Designer-Arbeitsbereich mit zwei QDockWidgets.

### Linkes Dock

Das linke Dock enthält einen vertikalen `QSplitter` und zwei übereinander angeordnete `QTabWidget`s. Die Höhe beider Bereiche kann mit dem Splitter verändert werden.

Oberes TabWidget:

- `Eigenschaften`
- `Ereignisse`
- `Methoden`

Im Tab `Eigenschaften` befindet sich ein Grid mit den Spalten:

- `Key`
- `Value`

Vorhandene Standardwerte:

- `Top` -> `QSpinBox`
- `Left` -> `QSpinBox`
- `Width` -> `QSpinBox`
- `Height` -> `QSpinBox`

Die SpinBoxes sind mit der aktuell selektierten Designer-Komponente verbunden und ändern Position bzw. Größe.

Unteres TabWidget:

- `Standard`
- `Erweitert`

`Standard` enthält eine leere IconView auf Basis von `QListWidget`/`QListView.IconMode`, in die später Designer-Komponenten aufgenommen werden können.

### Rechtes Dock / Designer

Das zweite Dock wird horizontal rechts neben dem Eigenschaftsdock angeordnet und erhält den restlichen Arbeitsbereich.

Die `QGraphicsScene` besitzt ein sichtbares Punktraster mit 10 Pixel Abstand. Zwei erste Button-Komponenten sind bereits eingesetzt.

Beide Buttons können mit der Maus verschoben werden. Bei Auswahl/Fokus erscheinen acht quadratische Resize-Griffe:

- links oben
- oben Mitte
- rechts oben
- rechts Mitte
- rechts unten
- unten Mitte
- links unten
- links Mitte

Die Griffe verwenden die passenden horizontalen, vertikalen und diagonalen Resize-Cursor.

Beim Ziehen eines Griffes wird zunächst ein gestrichelter Vorschau-Rahmen gezeichnet. Erst beim Loslassen der linken Maustaste wird die neue Größe und – bei linken/oberen Griffen – die neue Position übernommen.

## Tests

- Stage-84-spezifisch: 6 / 6 OK
- Gesamtsuite: 792 / 792 OK
- Python-Syntax via `compile(source, ..., 'exec')`: OK
- Kein `__pycache__` / keine `.pyc` im Paket

Hinweis: PyQt5 ist in der verwendeten Containerumgebung nicht installiert. Die Designer-GUI konnte daher dort nicht nativ gerendert werden; die GUI-Struktur wird durch Quellstrukturtests geprüft.
