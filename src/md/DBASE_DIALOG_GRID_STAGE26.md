# dBase Stage 26 - Dialograster und CLEAR-SCREEN-Muster bei Zoom

Stage 26 baut auf Stage 25 auf und aendert ausschliesslich die Qt5-Runtime-Geometrie bzw. den gespeicherten Konsolenzustand.

## Dialog-Bewegungsbereich

Der Login-Dialog wird relativ zum realen `QPlainTextEdit::viewport()` positioniert. Dieser Bereich liegt exakt zwischen Hauptmenue und Statusbar.

- oberste Dialogposition: erste Textzeile direkt unter der Menueleiste
- unterste Dialogposition: der untere Dialograhmen darf bis an die letzte Textzeile direkt oberhalb der Statusbar reichen
- es wird keine zusaetzliche Leerzeile mehr abgezogen
- horizontal bleibt der Dialog vollstaendig innerhalb der 80 Spalten

Die Dialogposition wird als Rasterposition (Spalte/Zeile) gespeichert. Die Pixelposition wird daraus jeweils neu berechnet.

## Verschieben des Hauptfensters

Der Login-Dialog beobachtet Move-/Resize-/Layout-Ereignisse des Hauptfensters und des Konsolen-Viewports. Nach einer Bewegung wird dieselbe gespeicherte Rasterposition relativ zur neuen globalen Position der Textkomponente wieder hergestellt. Der Dialog kann dadurch nicht ausserhalb der Text-Edit-Komponente liegen bleiben.

## Rasterbewegung

Beim Ziehen der Custom-Titlebar wird die Mausbewegung weiterhin auf ganze Zeichenzellen quantisiert:

- horizontal: `n * Zeichenbreite`
- vertikal: `n * Zeilenhoehe`

## CLEAR SCREEN <Zeichen> und Zoom

Ein reines Zeichenfuellmuster, z. B.:

```dbase
SET COLOR TO "B/RG+"
CLEAR SCREEN 0xB0
```

wird als Runtime-Zustand gespeichert:

- CP437-Zeichencode
- Vordergrundfarbe
- Hintergrundfarbe

Nach einem Lupen-Zoom wird das 80x25-Muster mit der neuen Fontgroesse erneut aufgebaut. `0xB0` bleibt damit als CP437 `U+2591` (`░`) erhalten.

Sobald nach dem Fuellmuster normale Konsolenausgabe erfolgt, wird der automatische Muster-Restore abgeschaltet, damit ein spaeterer Zoom keine Programmausgabe ueberschreibt.

## Kompatibilitaet

Es gibt keine neue dBase-Syntax und keine neue C-ABI. Compiler, Header und DEF bleiben binär kompatibel zu Stage 25; nur die Bridge-Implementierung wurde erweitert.
