# Stage 69 – PROLOG Wissen-Datenbank: sichtbare Alternativen direkt unter dem Parent

Basis: Stage 68.

## Fehlerbild

Auf nativer Qt5/Windows-Oberfläche wurde nach Klick auf den `▼`-Button zwar die
per Parent erzeugte ComboBox sichtbar geschaltet, sie erschien aber nicht auf dem
Bildschirm. Der Screenshot zeigte weiterhin nur den einzeiligen Button
`[ apfel ▼ ]` und darunter sofort das grüne Alternativen-Label.

## Ursache

`KnowledgeLevelButton` liegt in einem eigenen `KnowledgeFlowLayout`. Das FlowLayout
behielt für das Widget den alten einzeiligen Size-Hint (ca. 32 px). Die eingebetteten
Widgets (Label, ComboBox, Prüfen) lagen damit geometrisch unterhalb des Parent-Widgets
und wurden von Qt geclippt.

## Stage-69-Fix

- `KnowledgeLevelButton.sizeHint()` und `minimumSizeHint()` berücksichtigen nun explizit:
  - die `[Parent ▼]`-Zeile,
  - das Alternativen-Label,
  - die ComboBox,
  - den lokalen `Prüfen`-Button.
- Der Alternative-Host erhält beim Öffnen eine deterministische feste Höhe.
- `KnowledgeFlowLayout` verwendet den aktuellen Widget-Size-Hint und erweitert ihn
  mit `minimumSizeHint()` und `minimumSize()`.
- Die Höhe von `level_button_host` wird mit `heightForWidth()` neu gesetzt.
- Die innere Query-ScrollArea wird anschließend erneut dynamisch vermessen.
- Beim Schließen der Alternativen wird der Level-Button wieder auf die normale
  einzeilige Höhe reduziert.

## Gewünschtes sichtbares Verhalten

Vor Klick:

    [ apfel ▼ ]

Nach Klick auf `▼`:

    [ apfel ▼ ]
    [ Alternativen zu apfel: ]
    [ gesund              ▼ ]
    [        Prüfen          ]

Nach Auswahl `gesund` und erfolgreichem `Prüfen`:

    [ apfel ▼ ] -> [ gesund ▼ ]

ComboBox und lokaler Prüfen-Button verschwinden nach erfolgreichem Einfügen wieder.
Ein erneuter Klick auf `▼` öffnet die jeweilige Alternativen-Gruppe erneut.

## Schrift

Die Alternativen-ComboBox bleibt bei:

- Consolas, 9 pt
- Fallback: Courier New, 9 pt

## Tests

- Stage-69-spezifische Layout-/Quelltests: 7/7
- Stage-61..68 Wissen-Browser-Regressionen zusammen mit Stage 69: 68/68
- kompletter Projekt-Testlauf: 696/696

Eine native visuelle Windows-/PyQt5-Ausführung ist in der Containerumgebung nicht
möglich. Der Fix adressiert jedoch direkt die im Screenshot sichtbare Clipping-Ursache
im Custom-FlowLayout.
