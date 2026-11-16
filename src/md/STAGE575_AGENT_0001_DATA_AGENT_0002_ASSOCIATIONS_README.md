# Stage 575 – Agent 0001 JSON neben EXE + Agent 0002 für Formen

**Verbindliche Ausgangsbasis:** `d64_dism_stage574.zip`.

## Agent 0001: Dateipfad

Die **aktive** Beispielsatzdatei heißt nun **`agent_0001_example.json`** (Singular) und liegt unter

```
<Verzeichnis der d64_dism.exe>/data/agent_0001_example.json
```

Bei Ausführung von `d64_dism.py` als Python-Skript wird der Ordner der Python-Quellmodule anstelle des EXE-Ordners verwendet. Der Pfad wird unabhängig vom aktuellen Arbeitsverzeichnis ermittelt. Wurde die Anwendung z. B. als PyInstaller-EXE eingefroren, orientiert sich die Funktion an `sys.executable`, **nicht** an `sys._MEIPASS`.

- Die Datei wird in UTF-8 gelesen und bei Änderungen atomar über eine temporäre Datei geschrieben.
- Die neue JSON-Datei ist maßgeblich. Eine fehlende Datei wird samt `data`-Ordner angelegt.
- Auf einem früheren Stand unter `%APPDATA%/d64_dism/agent_0001_examples.json` gespeicherte Sätze werden beim Erststart übernommen, falls die neue Datei fehlt **oder** nur die fünf mitgelieferten Standardbeispiele enthält. Die alte Datei wird dabei nicht verändert.
- Beschädigte lokale JSON-Dateien werden nicht überschrieben; ihre Fehler werden weiter im vorhandenen Agent-0001-Dialog angezeigt.
- Eine schreibgeschützte EXE-Installation, etwa in `C:\Program Files`, braucht für lokale Speicherung entsprechende Schreibrechte; es erfolgt kein verstecktes Ausweichen nach `%APPDATA%`.
- Die Datei liegt absichtlich direkt im `data`-Verzeichnis. **Beim Aktualisieren darf diese persönliche Datei nicht versehentlich mit einem unveränderten ZIP-Standardbestand überschrieben werden.**

## Agent 0002: neues Docking-Fenster

Aufruf über **Agent → 0002**. Der bestehende exklusive Dock-Workspace wird verwendet (andere Docking-Fenster werden ausgeblendet). Stage 574 / Agent 0001 bleiben erhalten.

Die drei bisherigen nebeneinanderliegenden Bereiche bilden nun **den oberen Bereich**:

1. Text / Beispiele – editierbare ComboBox, Eingabefeld, Button „Assoziation erkennen“.
2. Wörter / Analyse – dreispaltige Token-Tabelle mit expliziten Dark-/Light-Headern.
3. Prüfergebnis / Assoziation – erkannte Form, Aussage-/Frage-Intent und Analysehinweise.

Darunter liegt als **zweiter Bereich** die „Visuelle Assoziation“ mit einer skalierbaren Zeichenfläche. Der vertikale QSplitter erlaubt dem Benutzer, die Höhe beider Bereiche anzupassen. Beide Agenten reagieren auf die globale `set_dark_mode()`-Umschaltung.

### Verstandene Beispiele

- `Was ist ein Kreis?` → Kreis mit Mittelpunkt
- `Wie sieht ein Kreis aus?` → Kreis mit Mittelpunkt
- `Zeige mir ein Dreieck` → Dreieck

Die Grafiken werden direkt mit PyQt5 `QPainter` gezeichnet; keine externen PNG/SVG-Dateien sind erforderlich. Nicht erkannte, verneinte oder mehrdeutige Aussagen erzeugen **keine** Form, sondern einen Hinweis.

Der Parser ist bewusst regelbasiert und erkennt zunächst nur die genannten Formbegriffe. Er ist weder ein vollständiger deutscher Grammatikparser noch ein allgemeiner Bildgenerator. Die Beispieltexte von Agent 0002 sind zunächst fest im Modul hinterlegt; die angeforderte JSON-Persistenz betrifft Agent 0001.

## Dateien

- Geändert: `d64_dism.py`, `agent_0001_data.py`, `test_stage573.py` (Testpfad).
- Verschoben/umbenannt: `agent_0001_examples.json` → `data/agent_0001_example.json`.
- Neu: `agent_0002_core.py`, `agent_0002.py`, `test_stage575.py`, diese README.
- Die übrigen Projektdateien aus Stage 574 bleiben inhaltlich unverändert.

## Verifikation

- Agent-Regressionen Stages 571–575: **43 erfolgreich, 5 übersprungen**.
- Breitere Stage-Regressionen 550–575: **271 erfolgreich, 53 übersprungen, 213 Subtests erfolgreich**.
- Native Qt-GUI-Tests wurden mangels PyQt5 in der Testumgebung übersprungen.
- Python 3.13 kann `d64_dism.py` wegen der bereits in Stage 574 verwendeten Python-3.15-Lazy-Import-Syntax nicht vollständig kompilieren. Die neu eingefügte Dock-Methode wurde daher separat syntaktisch geprüft; bestehende Stage-Dateien wurden nicht auf Python 3.13 zurückgeschrieben.
