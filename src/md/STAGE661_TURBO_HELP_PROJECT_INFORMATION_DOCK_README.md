# Stage 661 – Projekt-Informationen neben dem Hilfecompiler

Verbindliche Ausgangsbasis: `d64_dism_stage660.zip`.

## Korrektur von Stage 660

Der vorherige Wunsch bezog sich auf das Dock **Projekt-Informationen**
(`right_dock`, Qt-Objektname `d64_content_dock`) und ausdrücklich **nicht** auf
**Projekt-Einstellungen** (`project_settings_dock`). Die Stage-660-Sonderlogik
für Projekt-Einstellungen wurde daher zurückgenommen. Der damalige spezifische
Regressionstest `test_stage660.py` ist in Stage 661 durch `test_stage661.py`
ersetzt, da seine Anforderungen gegenstandslos geworden sind. Das alte
Stage-660-README bleibt nur als historische Dokumentation enthalten.

## Neues Verhalten

- Beim Öffnen von **Werkzeuge → Hilfecompiler** bleibt ein bereits sichtbares
  Dock **Projekt-Informationen** sichtbar. War es absichtlich geschlossen,
  wird es nicht automatisch geöffnet.
- Projekt-Informationen kann weiterhin links und rechts angedockt werden
  (`Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea`); die bestehende
  1/4-Hauptfensterbreite-Obergrenze bleibt erhalten.
- Der Hilfecompiler wird nach Möglichkeit auf der gegenüberliegenden Seite
  angeordnet und belegt den restlichen horizontalen Platz.
- Ein Wechsel der Andockseite von Projekt-Informationen bei offenem
  Hilfecompiler zieht den Hilfecompiler auf die gegenüberliegende Seite nach.
  Die benutzerdefinierte Andockvorschau bietet dafür genau ein Ziel pro Seite.
  Das Dateisystem-Dock bleibt dabei geschlossen.
- Das benutzerseitig neu gewählte Andockziel von Projekt-Informationen wird
  beim Schließen des Hilfecompilers nicht durch `restoreState()` überschrieben.
  Ein während der Hilfe-Sitzung geschlossenes Projekt-Informationen-Dock wird
  anschließend nicht unerwartet wieder geöffnet.
- Die exklusiven Arbeitsbereiche der übrigen Werkzeuge und der eigenständige
  Vollflächenmodus von Projekt-Einstellungen bleiben wie vor Stage 660.

## Betroffene Dateien

- `d64_dism.py`: Exklusiver Dock-Workspace, das Re-Sizing des Hilfecompilers,
  Snap-Vorschau und Wiederherstellung für `right_dock`.
- `test_stage661.py`: Korrektur-spezifische Fake-Qt-Regressionen.

Keine C++-/Qt5-Bridge-Änderung; `libd64_qt5.dll` muss nicht neu gebaut werden.

## Prüfung

`python -m pytest -q test_stage661.py test_stage654.py test_stage658.py test_stage655.py test_stage659.py test_stage652.py test_stage653.py`

Ergebnis: **43 Tests erfolgreich** (11 neue plus 32 bestehende).

Die Tests prüfen die produktiven Python-Methoden mit Qt-kompatiblen
Testobjekten. Ein visueller PyQt5-Laufzeittest unter Windows bleibt offen.
