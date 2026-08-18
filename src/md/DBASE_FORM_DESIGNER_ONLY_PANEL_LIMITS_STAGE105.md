# Stage 105 – Panel-Border-Limits nur im Formulardesigner

Die Content-Grenzen eines Panels sind jetzt im Code ausdrücklich als Designer-Funktion markiert.

## Designer

Beim visuellen Bearbeiten gelten weiterhin die berechneten Innenlimits aus den aktiven Border-Seiten:

- Einfügen
- Verschieben
- Resize
- Änderungen über den Eigenschaftenbaum

Dadurch können Controls nicht versehentlich in den vom Border verdeckten Bereich geraten.

## Laufzeit / erzeugtes Programm

Die Border-Innenlimits sind **keine Runtime-Regel**. Das erzeugte Programm darf eine eingebettete Komponente weiterhin programmatisch frei positionieren oder vergrößern – auch bis an den Rand oder in einen Bereich, der vom Panel/Border verdeckt wird.

Dazu wurden die betreffenden Hilfen bewusst als Designer-Funktionen benannt:

- `_designer_effective_border_inset()`
- `designer_panel_content_rect()`
- `_designer_constrain_panel_children_to_content()`
- `DESIGNER_ENFORCE_PANEL_CONTENT_LIMITS`

Es wird daraus kein zusätzliches Laufzeit-Limit serialisiert oder in den generierten Anwendungscode übernommen.
