# Stage 91 – dBase Formulardesigner: Panel Parent/Child

Stage 91 erweitert den Stage-90-Formulardesigner um echte hierarchische Panel-Container.

## Platzierung

1. Ein Panel im Designer auswählen/fokussieren.
2. Im Tab `Standard` eine neue Komponente auswählen.
3. Innerhalb des selektierten Panels in die GraphicScene klicken.
4. Die neue Komponente wird als `QGraphicsItem`-Child des Panels angelegt.

Liegt die Zielposition außerhalb des selektierten Panels, wird die Komponente weiterhin als Top-Level-Control in der Scene erzeugt.

## Verschachtelte Panels

Panels können selbst Child eines Panels sein. Ein selektiertes inneres Panel wird zum Parent der anschließend darin platzierten Komponente. Dadurch sind rekursive Hierarchien möglich:

```text
Panel1
  Panel2
    Button1
    CheckBox1
  ComboBox1
```

## Koordinaten und Geometrie

- Child-Positionen (`Top`, `Left`) sind relativ zum Parent-Panel.
- Wird ein Parent-Panel verschoben, bewegen sich seine Child-Controls automatisch mit.
- Verschieben von Child-Controls wird auf die Fläche des Parent-Panels begrenzt.
- Resize-Vorschau arbeitet weiter in Scene-Koordinaten; beim Abschluss wird die Position zurück in Parent-Koordinaten übersetzt.
- Auch Child-Panels können weitere Child-Controls enthalten.

## Tests

Stage-90/91 Fokus: 15/15 OK.
Gesamte Regression: 830/830 OK.
