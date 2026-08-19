# Stage 113 – Doxygen als Docking-Fenster

Die Oberfläche der bereitgestellten `doxygen.py` wird über ihre vorhandene Klasse
`DoxyGenToolWindow(QWidget)` direkt in ein `QDockWidget` des Hauptfensters eingebettet.
Die umfangreiche Doxygen-Logik wird nicht dupliziert oder verkürzt.

## Menü

`Werkzeuge -> Doxygen Dokumentation ...`

Der Menüeintrag öffnet das Dock erneut, wenn es zuvor über dessen X geschlossen wurde.

## Dock

- Titel: `Doxygen Dokumentation`
- initial rechts angedockt
- verschiebbar
- floatbar
- schließbar
- in alle Qt-Dockbereiche verschiebbar
- beim ersten Öffnen lazy geladen

Die Datei `doxygen.py` liegt neben `d64_dism.py`. Dadurch werden Doxygen-/ANTLR-/QtWebEngine-
Abhängigkeiten erst beim Öffnen des Werkzeugs importiert. Scheitert der Import, bleibt das
Hauptprogramm aktiv und zeigt eine Fehlermeldung.

## Bestehende Oberfläche

Die vorhandene `DoxyGenToolWindow`-Oberfläche wird unverändert als Dock-Inhalt verwendet.
Dadurch bleiben insbesondere Projektliste, Wizard, Expert und Run erhalten.

## Paketstruktur

Die d64qt5-Quelldateien bleiben unter `d64qt5/` und wurden gegenüber Stage 112 nicht ersetzt.
