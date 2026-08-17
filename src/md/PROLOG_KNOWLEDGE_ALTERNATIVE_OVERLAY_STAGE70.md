# PROLOG Wissen-Browser – Stage 70

## Anlass

Unter Windows/Qt5 blieb die Alternativen-ComboBox trotz `show()` unsichtbar. Der Screenshot aus Stage 69 zeigte, dass nach Klick auf `apfel ▼` nur der Faktenbutton und das Statuslabel sichtbar waren.

## Ursache

Die bisherige ComboBox war Teil des `KnowledgeLevelButton`. Damit hing ihre sichtbare Geometrie weiterhin an der Größenberechnung des Custom-`KnowledgeFlowLayout` und des Button-Containers. Native Qt5/Windows konnte den Bereich unterhalb der Buttonzeile weiterhin clippen.

## Stage-70-Lösung

Jede `KnowledgeQueryLane` besitzt jetzt ein dauerhaft erzeugtes `QFrame`:

- `prolog_knowledge_alternative_overlay`
- direkter Child von `level_button_host`
- keine `setParent()`-Operation beim Öffnen
- nicht Bestandteil des `KnowledgeLevelButton`
- beim Start verborgen

Nach Klick auf `▼` wird das Overlay anhand der echten Geometrie des Parent-Buttons positioniert:

```text
[ apfel ▼ ]
[ gesund              ▼ ]
[        Prüfen          ]
```

Die Y-Position ist `Button-Unterkante + 4 px`. Das Panel wird mit `raise_()` nach vorn geholt. Der Flow-Host reserviert zusätzlich mindestens bis zur Unterkante des Overlays Platz, damit auch die innere `QScrollArea` nichts abschneidet.

Die erste verfügbare Alternative wird direkt angezeigt (`setCurrentIndex(0)`), damit die sichtbare ComboBox nicht leer erscheint.

## Prüfen

Der lokale `Prüfen`-Button verwendet unverändert den bestehenden PROLOG-Prüfpfad. Bei Erfolg:

1. Alternative wird als nächster Level übernommen.
2. ComboBox und `Prüfen` verschwinden.
3. Level-Buttons werden neu aufgebaut.
4. Beispiel: `apfel -> gesund`.

Bei Fehlschlag bleiben ComboBox und `Prüfen` sichtbar.

## Schrift

Alternativen-ComboBox und Dropdown:

- Consolas, 9 pt
- Fallback: Courier New, 9 pt

## Tests

- Stage-70-spezifisch: 8/8
- Wissen-Browser Stage 61–70: 84/84
- Gesamtsuite: 704/704

Eine native visuelle Windows/PyQt5-Ausführung ist in der Containerumgebung nicht verfügbar.
