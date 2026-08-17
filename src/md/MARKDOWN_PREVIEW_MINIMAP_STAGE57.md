# Stage 57 - MarkDown-Viewer Schrift + Mini-Map

## Änderungen

- Die Schrift der gerenderten MarkDown-Vorschau wurde gegenüber Stage 56 um 1 pt erhöht.
- Basistext: 10 pt -> 11 pt.
- Inline-/Block-Code: 9.5 pt -> 10.5 pt.
- Code-Sprachlabel: 8.5 pt -> 9.5 pt.
- Überschriften H1..H6: 22/18/16/14/12/11 pt -> 23/19/17/15/13/12 pt.
- Der `MarkDown`-Tab besitzt jetzt rechts eine Mini-Map.
- Die Vorschau verwendet exakt dieselbe `SourceMiniMap`-Klasse wie der Rohdaten-Editor.

## Mini-Map-Verhalten

Damit gelten im MarkDown-Viewer dieselben Regeln wie im Rohdaten-Editor:

- Scrollen in der Vorschau verschiebt die Mini-Map synchron.
- Klick in die Mini-Map setzt die vertikale Scrollposition der Vorschau.
- Ziehen des Viewport-Markierers scrollt die Vorschau.
- Das Mausrad über der Mini-Map scrollt die Vorschau.
- Ab mehr als 120 logischen Mini-Map-Zeilen wird das 120-px-Scrollfenster verwendet.
- Der schmale Scrollindikator wird aus derselben `QScrollBar` berechnet.
- Es existiert kein unabhängiger Mini-Map-Scrollzustand.

## Layout

Der `MarkDown`-Tab verwendet nun einen horizontalen Sibling-Container:

```text
+------------------------------------------+----------+
| gerenderte MarkDown-Vorschau             | Mini-Map |
| QPlainTextEdit                           |          |
+------------------------------------------+----------+
```

Die Vorschau bleibt `readOnly`.

## Tests

- Stage-57-spezifisch: 6/6 erfolgreich.
- Gesamter Regressionstest: 596/596 erfolgreich.
