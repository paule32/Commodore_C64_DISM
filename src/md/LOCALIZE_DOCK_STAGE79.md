# Stage 79 – Localize PO/MO als Docking-Fenster

Basis: Stage 78.

## Änderung

Der bisher modal mit `exec_()` geöffnete `LocalizeToolWindow` kann nun als normales Widget in einem `QDockWidget` verwendet werden.

Beim Aufruf von `Werkzeuge -> Localize PO->Mo ...`:

1. wird genau ein wiederverwendbares Dock `Localize PO/MO` erzeugt,
2. das linke Dock `Dateisystem und Dateien` wird ausgeblendet,
3. der bestehende Localize-Editor wird in den linken Dockbereich eingebettet,
4. das Dock wird auf ca. 920 px Breite angefordert,
5. das rechte Projekt-Dock und das untere Protokoll bleiben verfügbar.

Beim Ausblenden/Schließen des Localize-Docks wird der Localize-Zustand gespeichert und das zuvor sichtbare Dateisystem-Dock wieder eingeblendet.

Der bisherige `Cancel`-Button behält die Localize-Schließen-Abfrage und blendet danach das Dock aus.

PROLOG-Wissensbrowser und Localize belegen nicht gleichzeitig denselben linken Arbeitsbereich: beim Öffnen des einen wird das andere Dock ausgeblendet.

## Persistenz

`ExplorerWindow.settings` wird zusätzlich als `_settings` aliasiert. Das erhält die bereits vorhandene Localize-State-Logik (`localize/source_lang`, `localize/dest_lang`, PO/MO-Pfade und Headerfelder), die historisch `_settings` verwendet hat.

## Tests

- Stage-79-spezifisch: 8/8
- Gesamtsuite: 764/764
- keine `.pyc`-/`__pycache__`-Dateien im Paket
