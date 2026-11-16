# Stage 573 – Agent 0001: Theme-Wechsel, Modulquelle und Header

**Verbindliche Ausgangsbasis:** `d64_dism_stage572.zip`.

## Fehlerbericht

Bei der Umschaltung vom Dark- in den Light-Mode meldet der Watchdog:

```
AttributeError: 'GermanGrammarWidget' object has no attribute 'set_dark_mode'
```

Dazu sind die horizontalen und vertikalen Header im mittleren Agent-0001-Panel trotz hellem Text unter Windows weiß geblieben.

## Ursache und Korrekturen

1. **Agent-Modulquelle:** In der geprüften Stage-572-`agent_0001.py` ist `GermanGrammarWidget.set_dark_mode` bereits vorhanden. Der Fehler ist somit mit dem Stand des gelieferten Pakets nicht zu reproduzieren und deutet auf eine ältere zur Laufzeit verwendete Klasse hin (z. B. aus einem anderen `sys.path`-Eintrag oder einem noch bestehenden Prozess). `show_agent_0001_dock()` lädt jetzt ausdrücklich die lokale `agent_0001.py` neben `d64_dism.py`, wenn diese Datei existiert. Bei eingebettetem PyInstaller-Modul wird auf den bisherigen regulären Import zurückgegriffen.
2. **Watchdog-Schutz:** `_apply_application_theme()` prüft vor dem Aufruf, ob `set_dark_mode` tatsächlich aufrufbar ist. Bei veralteten Widgets wird eine Diagnose ausgegeben; der Wechsel der Gesamtanwendung wird nicht mehr durch diesen `AttributeError` unterbrochen.
3. **Qt/Windows Header:** Horizontaler und vertikaler Tabellenheader verwenden jetzt `_GrammarHeader(QHeaderView)`. Dessen `paintSection()` zeichnet Hintergrund, Schrift und Trennlinien ausdrücklich statt sich ausschließlich auf `QHeaderView::section`-Stylesheets und das systemeigene Windows-Theme zu verlassen. Die bisherige Spalten-Resize-Logik bleibt unverändert.
4. **Theme-Wechsel:** Der Widget-Handler `set_dark_mode()` schaltet die Farben beider benutzerdefinierten Header und der Tabelle zwischen Dark- und Light-Mode um.

## Farben

| Ansicht | Header-Hintergrund | Schrift | Rahmen |
| --- | --- | --- | --- |
| Dark | `#303030` | `#f5f5f5` | `#565656` |
| Light | `#e1e1e1` | `#171717` | `#999999` |

## Geänderte Dateien

- `d64_dism.py`: deterministischer lokaler Agent-Import und fehlertoleranter Theme-Aufruf.
- `agent_0001.py`: QHeaderView-Unterklasse mit eigener Zeichenroutine und Dark/Light-Mode-Umschaltung.
- `test_stage571.py`, `test_stage572.py`: bisherige Textassertions an neue Implementierung angepasst, bestehende Speichern-/JSON-Tests erhalten.
- `test_stage573.py`: neue statische Regressionstests und optionaler echter Qt-Test.
- Diese README.

## Installation

Die ZIP vollständig in den Anwendungsordner entpacken. Insbesondere müssen `d64_dism.py` und `agent_0001.py` aus **derselben Stage** stammen und nebeneinanderliegen. Die Anwendung danach komplett neu starten (damit keine ältere Klasse im Python-Prozess verbleibt).

## Grenzen

Auf dem Linux-Testsystem ist PyQt5 nicht installiert. Daher kann ein nativer visueller Test des Fensterstils unter Windows nicht bestätigt werden; der optionale Qt-Test wird übersprungen. Der importbedingte `AttributeError` wird durch den zusätzlichen Schutz abgefangen. Die eigentliche Grammatik- und JSON-Logik wurde nicht verändert.
