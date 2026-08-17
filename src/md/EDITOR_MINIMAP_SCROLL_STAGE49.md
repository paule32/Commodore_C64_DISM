# Stage 49 – scrollende Editor-Mini-Map ab 120 px

Die Mini-Map bleibt rechts neben dem vorhandenen `SourceTextEdit` und nutzt
weiterhin ausschließlich dessen vertikale `QScrollBar` als Scrollzustand.

## Verhalten

- Bis 120 logischen Mini-Map-Pixeln/Quellzeilen wird der gesamte Inhalt gezeigt.
- Ab mehr als 120 Pixeln wird der Inhalt nicht weiter zusammengedrückt.
- Stattdessen wird ein 120-Pixel-Fenster aus dem Dokument dargestellt.
- Die Startposition dieses Fensters wird proportional aus
  `editor.verticalScrollBar().value()` berechnet.
- Scrollt der Editor, scrollt daher der Mini-Map-Inhalt automatisch mit.
- Klick/Drag und Mausrad in der Mini-Map steuern weiterhin dieselbe Scrollbar
  des Editors.
- Rechts in der Mini-Map erscheint bei langen Dokumenten ein schmaler
  Scrollindikator.
- Die Mini-Map speichert keinen zweiten unabhängigen Scrollwert. Dadurch kann
  ihre Position nicht vom Haupteditor wegdriften.

## Synchronisation

```text
SourceTextEdit.verticalScrollBar()
              |
              +--> sichtbarer Editor-Ausschnitt
              |
              +--> Mini-Map 120-px-Fenster
              |
              +--> Mini-Map-Scrollindikator
```

Die bestehende Gutter-, Breakpoint-, Bookmark-, Autocomplete- und Syntax-
Highlighter-Logik bleibt unverändert.
