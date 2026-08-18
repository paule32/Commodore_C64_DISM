# Stage 100 – Kontextmenü für Formulardesigner-Komponenten

## Rechtsklick

Ein Rechtsklick ermittelt das oberste `DBaseFormControlItem` direkt unter dem
Mauszeiger und selektiert genau dieses Control.

Das Kontextmenü enthält:

- Hilfe
- Kopieren
- Einfügen
- Ausschneiden
- Entfernen

## Zwischenablage

Kopiert werden nicht nur Typ und Geometrie, sondern auch Brush-, Font- und
Border-Eigenschaften. Bei einem Panel wird die komplette Child-Hierarchie
rekursiv übernommen.

Beim Einfügen auf einem Panel wird die Kopie Child dieses Panels. Bei einem
normalen Control wird auf derselben Parent-Ebene eingefügt.
