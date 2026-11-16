# Stage 576 – Agent 0002: Importkollision mit `agent_0001` beseitigt

**Basis:** `d64_dism_stage575.zip` (unverändert außer den unten beschriebenen Dateien).

## Ursache

Die bisherige Datei `agent_0002.py` importierte `from agent_0001 import _GrammarHeader`.
Auf dem Windows-Rechner liegt zusätzlich ein Paketordner `agent_0001/__init__.py`.
Python löst `import agent_0001` dadurch zum Paket auf. Dieses Paket exportiert
`_GrammarHeader` nicht, und das Laden von Agent 0002 bricht mit `ImportError` ab.
Der lokale Loader in `d64_dism.py` löst das nicht, weil er nur `agent_0002.py`
explizit lädt, nicht dessen Abhängigkeiten.

## Korrektur

* `agent_0002.py` besitzt jetzt die benötigte `_GrammarHeader`-Implementierung
  selbst. **Kein Import von `agent_0001` mehr.**
* Erhalten: selbst gezeichnete horizontale/vertikale Dark-/Light-Mode-Header,
  Zeichenfläche, Splitter, Worttabelle und Assoziationsregeln.
* Keine Änderung an `agent_0001.py`, dessen Paket oder an `d64_dism.py`.
* Der direkte Import von `agent_0001_core.py` bleibt bestehen, weil das ein
  eigenständiges Modul ist.

## Installation

Aus Stage 576 mindestens `agent_0002.py` neben `d64_dism.py` austauschen.
Das bestehende `agent_0001`-Paket muss **nicht gelöscht** werden. Python-Anwendung
vollständig neu starten, damit bereits geladene Module ersetzt werden.

## Prüfungen

* `ast.parse` für die geänderte Datei.
* Statischer Regressionstest: kein `import agent_0001` mehr vorhanden.
* Ein Stub-Importtest simuliert ohne installierte PyQt5-GUI erfolgreich die Kollision
  mit einem gleichnamigen Paket `agent_0001/__init__.py`.
* Optionaler PyQt5-Integrationstest simuliert ein gleichnamiges fremdes Paket
  `agent_0001/__init__.py`, öffnet Agent 0002 und schaltet beide Themes.
* ZIP-Integrität mit `ZipFile.testzip()` geprüft.

Eine native Windows-GUI-Prüfung ist in dieser Umgebung ohne PyQt5 nicht möglich.
