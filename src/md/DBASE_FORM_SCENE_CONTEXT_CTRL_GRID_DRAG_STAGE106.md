# Stage 106 – Scene-Kontextmenü und CTRL-Grid-Drag

## Graphics Scene Kontextmenü

Ein Rechtsklick auf die freie Formular-Designer-Scene öffnet jetzt dieselben
Einträge wie bei einer Komponente:

- Hilfe
- Kopieren
- Einfügen
- Ausschneiden
- Entfernen

Liegt kein Control unter dem Mauszeiger, bleibt eine vorhandene Selektion für
Kopieren/Ausschneiden/Entfernen erhalten. Einfügen auf die freie Scene erzeugt
ein Top-Level-Control an der angeklickten Scene-Position.

## CTRL-Drag

Während eines linken Drags gilt:

- CTRL gedrückt: Bewegung in 10-Pixel-Schritten (`GRID_SPACING`)
- CTRL nicht gedrückt: Bewegung in 1-Pixel-Schritten
- CTRL kann während des Drags gedrückt oder losgelassen werden
- beim Moduswechsel wird der Drag-Anker neu gesetzt, damit das Control nicht springt

Die gewünschte Position wird weiterhin über `setPos()` gesetzt. Dadurch läuft
sie durch das vorhandene `itemChange()` und respektiert weiterhin:

- Scene-Grenzen
- Panel-Grenzen
- Designer-only Border-Content-Limits
- verschachtelte Panels

Die 10-Pixel-Regel ist ausschließlich eine Bedienfunktion des Designers und
keine Runtime-Regel des erzeugten Programms.
