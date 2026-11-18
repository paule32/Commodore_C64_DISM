# Stage 604 – Projekt-Einstellungen: Schriftgröße +1 pt

**Verbindliche Basis:** `d64_dism_stage603.zip`.

## Änderung

In `d64_dism.py`, Methode `MainWindow._ensure_project_settings_dock`, wird
beim ersten Erzeugen des `QDockWidget` die bestehende, von der Anwendung
geerbte Schriftgröße um **exakt 1 Punkt** erhöht. Die Einstellung liegt
auf dem *Projekt-Einstellungen-Dock* (nicht global auf der Anwendung) und
wird **vor** dem Aufbau des `QScrollArea` und `ProjectSettingsPanel` gesetzt.

Damit erben alle nicht eigens font-konfigurierten Bedienelemente der
Projekt-Einstellungen – Windows PE32/PE64, C64, TreeLists, Reiter,
Labels, Checkboxen, Buttons, Eingabefelder und Auswahlmenüs – die
vergrößerte Schrift. Die eigene Schriftgröße der Editor-Vorschau wird
nicht verändert. Das Dark-/Light-Theme und die Einstellungen in `.pro`
bleiben unverändert. Der Scroll-Viewport nimmt bei Bedarf zusätzlichen
Platz auf, statt das Hauptfenster zu verbreitern.

Bei Fonts, deren Punktgröße nicht verfügbar ist, wird zuerst die
Applikationsschrift und als letzte Reserve 10 pt als Ausgangswert
verwendet; der Zielwert ist stets Basis +1 pt.

## Prüfung

- Quelltextbasierte Regressionstests für die Anwendungsstelle, die
  Font-Vererbung und den exakt einmaligen +1-pt-Schritt.
- Python-3.15-`lazy`-Syntax wurde im Syntaxcheck nur für die lokale
  Python-3.13-Analyse normalisiert; die originale Syntax bleibt erhalten.
- ZIP-Integrität geprüft.
- Nativer PyQt5/Windows-GUI-Test ist in der aktuellen Linux-Umgebung
  nicht möglich, da PyQt5 dort nicht installiert ist.
