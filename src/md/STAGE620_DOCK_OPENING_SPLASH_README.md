# Stage 620 – Einheitlicher Warte-Splash vor Docking-Fenstern

**Verbindliche Basis:** `d64_dism_stage619.zip`.

## Ziel

Bei expliziten Öffnungsaktionen für die vorhandenen Docking-Fenster erscheint
vor dem Laden und Einblenden derselbe `D64OperationPreludeDialog`, der bislang
bei den **Projekt-Einstellungen** und bei WFM-Dateien verwendet wurde.
Der Dialog verwendet dieselben Farben (Dark/Light), dieselbe zentrierte
Darstellung und dieselbe unbestimmte Fortschrittsanzeige.

## Technische Umsetzung

- `dock_opening_prelude.py`: registriert die entsprechenden Python-
  Methoden des Hauptfensters vor der QAction/Signal-Verdrahtung; neue
  `show_*_dock`-Methoden werden automatisch berücksichtigt.
- `d64_dism.py`: Installation vor `ExplorerWindow.__init__`, Aktivierung
  erst nach `window.show()` und dem ersten `app.processEvents()`.
- Jeder Aufruf startet den **vorhandenen** `run_with_operation_prelude()`;
  die Originaloperation beginnt 40 ms später im GUI-Thread, damit der Splash
  zuerst sichtbar gezeichnet werden kann. Der Splash wird auch bei
  Ausnahmen sauber geschlossen.
- Verschachtelte Dock-Methoden laufen synchron innerhalb der gestarteten
  Operation; sie erzeugen keine weiteren Splash-Dialoge.
- Laufende Vorspannaktionen werden nicht durch einen zweiten externen
  Öffnungsaufruf überlagert.
- `QAction.triggered(bool)`-Parameter werden nicht an Methoden ohne einen
  passenden Parameter durchgereicht.

## Abgedeckte Öffnungsaktionen

Agent 0001/0002/0003, dBASE-/SQL-/Report-/Etiketten-/Formular-
Designer und Dateiladevorgänge, Tabellen-Designer, Windows-Ressourcen-Editor,
C64-Sprite-/Paletten-/Zeichen-/Bildschirm-Editor, Prolog-Browser,
Localize, Doxygen, HTML-Editor, E-Baukasten, Projekt-Objekt-/Archivanalyse,
Software-Installer, Desktop-Einstellungen, BIND9/OpenSSL/Apache,
Mathematik-/Musik-/Chemie- und Geographie-Lernmodule sowie weitere
`show_*_dock`-Methoden.

**Bestehende Sonderfälle:**

- `show_project_settings_dock` und `open_project_wfm_with_prelude`
  verwenden unverändert den bereits vorhandenen Vorspann.
- Beim Öffnen von SQL-Projektdateien werden der Dock-Aufbau und
  `load_project()` in einer gemeinsamen Splash-Operation durchgeführt;
  das Laden wird nicht vorzeitig ausgeführt oder übersprungen.
- C64-Sprite-Projektblätter werden als zusammenhängender Vorgang
  geöffnet, einschließlich der Blatt-/Editorzuordnung.
- Initiale Dock-Panels beim Start und interne Wiederherstellungen
  von gespeicherten Dock-Layouts werden **nicht** künstlich verzögert.

## Tests

`python -m pytest -q test_stage620.py test_stage619.py test_stage618.py test_stage617.py test_stage616.py test_stage614.py`

Ergebnis hier: **53 passed**. Syntax von `d64_dism.py` wurde für den
verfügbaren Python-3.13-Prüfer nach vorübergehender Umschreibung der beiden
Python-3.15-`lazy`-Imports geprüft. Die gelieferten Quelldateien behalten
die `lazy`-Imports unverändert bei.

**Noch erforderlich:** Sichtprüfung der nativen PyQt5-Oberfläche unter Windows
(insbesondere bei komplexen Multi-Dock-Workspaces und modalen Rückfragen).
Keine Änderung an vorhandenen EXE-/DLL-/OBJ-Binärdateien notwendig.
