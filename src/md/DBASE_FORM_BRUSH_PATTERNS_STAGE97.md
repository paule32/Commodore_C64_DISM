# Stage 97 – 16 zusätzliche Patterns und Style-Cuttings

## Erweiterungen

- 16 zusätzliche Brush-Patterns
- Gesamtzahl jetzt: 48
- weiterhin in technisch und minimalistisch gegliedert
- neuer Root-Eintrag **Style** bleibt erhalten
- unter **Style** jetzt zwei zusätzliche Sub-Einträge:
  - **Cut Width**
  - **Cut Height**
- beide Werte sind als Spinbox umgesetzt
- Änderungen wirken sofort auf:
  - die Pattern-Füllung der ausgewählten Komponente
  - die ComboBox-Vorschau der Patterns

## Umsetzung

Die Cuttings arbeiten als mittiger Ausschnitt der quadratischen Pattern-Vorlage.
Anschließend wird der Ausschnitt wieder auf die originale Kachelgröße skaliert.
Damit kann die Musterwirkung live verdichtet oder vergröbert werden, ohne die
zugrundeliegende Kachelgröße der Brush zu ändern.
