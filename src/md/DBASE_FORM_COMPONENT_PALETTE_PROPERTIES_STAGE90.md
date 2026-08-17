# Stage 90 – dBase Formulardesigner: Komponentenpalette und Property-Tree

Stage 90 erweitert Stage 89 additiv.

## Komponentenpalette – Tab „Standard“

Der untere linke Tab enthält jetzt auswählbare Icon-Einträge für:

- Button
- Checkbox
- Radiobutton
- ComboBox
- Label
- Image
- Panel
- Tabellen-Grid
- vertikale Scrollbar
- horizontale Scrollbar
- Statusbar
- Toolbar
- Menü

Ein Klick setzt einen einmaligen Platzierungs-Flag. Der nächste Linksklick in die QGraphicsScene erzeugt die ausgewählte Komponente an der Mausposition und löscht den Flag wieder.

## Echte Qt-Controls

Die Designer-Controls werden als echte QWidget-Instanzen in QGraphicsProxyWidget eingebettet. Dadurch kann auf Windows `QWidget.winId()` verwendet werden, um den Fenster-Handle der Komponente als HWND-Eigenschaft anzuzeigen.

Die vorhandenen acht Resize-Griffe sowie Move/Resize bleiben erhalten.

## Eigenschaften

Das bisherige zweispaltige Property-Grid wurde durch eine QTreeWidget-basierte TreeList ersetzt.

Header:

- Key
- Value

Im Dark-Mode:

- Header-Hintergrund: #2A2A2A
- Header-Schrift: weiß
- Property-Editoren: schwarz mit gelber Schrift

Der Root-Knoten `Position` spannt beide Spalten und verwendet:

- Hintergrund: Navy #000080
- Schrift: Gelb #FFFF00

Unter `Position` liegen:

- Top
- Left
- Width
- Height

Alle vier Werte besitzen QSpinBox-Editoren. Ein Doppelklick auf `Position` klappt die Gruppe ein bzw. aus.

Weitere Eigenschaften:

- HWND
- Name
- Hintergrundfarbe
- Schriftfarbe
- Schriftart (QComboBox)
- Font (Punktgröße)
- Fett
- Kursiv

Änderungen werden direkt auf das aktuell selektierte Qt-Control angewendet.

## Tests

Stage-90-Fokus: 25/25 erfolgreich.
Gesamte Regression: 823/823 erfolgreich.
