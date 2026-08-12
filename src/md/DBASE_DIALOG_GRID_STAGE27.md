# dBase Stage 27 - Dialoggrenze letzte Zeile/Spalte minus 1

Stage 27 baut auf Stage 26 auf und aendert nur die maximale Rasterposition von Dialogen.

## Neue Grenze

Die 80x25-Konsolenflaeche behaelt am rechten und unteren Rand jeweils eine freie Rasterzelle.
Der Dialog bleibt dabei weiterhin vollstaendig innerhalb des realen `QPlainTextEdit::viewport()`.

Fuer den aktuellen Login-Dialog mit 48x12 Rasterzellen gilt:

```text
maximale Startspalte = 80 - 48 - 1 = 31
maximale Startzeile  = 25 - 12 - 1 = 12
```

Damit kann der Dialograhmen bis zur letzten logischen Spalte minus 1 bzw. bis zur letzten
logischen Zeile minus 1 verschoben werden.

Die Berechnung kombiniert die logische 80x25-Grenze mit der realen Viewport-Grenze. Dadurch
bleibt das Verhalten auch bei DPI-/Font-Rundungen sicher innerhalb der Text-Edit-Komponente.

## Unveraendert

- Dialogposition bleibt zeichenrasterbasiert.
- Beim Verschieben des Hauptfensters bleibt der Dialog relativ zum Konsolen-Viewport positioniert.
- Lupen/Zoom behalten das aktuelle `CLEAR SCREEN <Zeichen>`-Muster bei.
- Keine neue dBase-Syntax und keine neue C-ABI.
