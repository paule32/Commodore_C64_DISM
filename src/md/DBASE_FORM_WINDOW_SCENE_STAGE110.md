# Stage 110 – dBase Form-Fenster im Formular-Designer

Stage 110 ergänzt die bisherige Formular-Designer-Scene um eine visuelle Hauptform (`DBaseFormWindowItem`).

## Verhalten

- `Form.Width` und `Form.Height` aus einer WFM-Datei bestimmen die Client-Größe der dargestellten Hauptform.
- `Form.Left` und `Form.Top` bleiben Runtime-Eigenschaften und verschieben die Designer-Form nicht.
- Der lokale Ursprung der Client-Fläche bleibt `(0,0)`. Bestehende WFM-Positionen der Controls ändern sich dadurch nicht.
- Die Form besitzt einen grauen Rahmen mit 2 Pixeln Breite.
- Oberhalb der Client-Fläche wird eine Titelbar mit Form-Klassenname gezeichnet.
- Minimieren-, Maximieren- und Schließen-Symbole sind rein visuell und führen im Designer keine Fensterlogik aus.
- Die Client-Fläche ist `#1B1B1B`, die äußere Designer-Arbeitsfläche `#101010`.
- Das 10-Pixel-Raster wird nur innerhalb der Client-Fläche gezeichnet.

## Resize

Die Hauptform kann im Designer ausschließlich an folgenden Stellen skaliert werden:

- rechter Rand
- unterer Rand
- rechte untere Ecke

Linker und oberer Rand bleiben fest. Beim Resize werden `wfm_form_width` und `wfm_form_height` aktualisiert und beim Speichern wieder als `Width`/`Height` in die WFM-Datei geschrieben.

## Designer-Limits

Top-Level-Controls sind ChildItems der visuellen Hauptform. Dadurch gelten die bisherigen Designer-Limits nun auch für die Hauptform:

- Controls können im Designer nicht über die Client-Grenzen hinaus verschoben werden.
- Beim Resize eines Controls gelten die Client-Grenzen ebenfalls.
- Beim Verkleinern der Hauptform werden Controls zurück in den sichtbaren Bereich begrenzt.
- Panel-/Border-Innenlimits aus Stage 104/105 bleiben unverändert erhalten.
- Diese Grenzen sind weiterhin ausschließlich Designer-Regeln und werden nicht als Runtime-Positionslimit in das erzeugte Programm übernommen.

## Paketstruktur

Die Quellen der `d64qt5.dll` liegen ab diesem Paket ausschließlich im Unterverzeichnis:

```
d64qt5/
    d64qt5_bridge.cpp
    d64qt5_bridge.h
    d64qt5_bridge.def
    d64qt5_bridge.pro
    d64_workstation.cpp
    d64_workstation.h
```

Die vollständige reparierte `d64qt5_bridge.cpp` (275629 Bytes) wurde verwendet.
