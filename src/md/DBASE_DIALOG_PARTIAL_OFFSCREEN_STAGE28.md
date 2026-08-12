# dBase Qt5 Dialog-Raster Stage 28

Stage 28 erweitert die Verschiebegrenzen des SESSION-Login-Dialogs.

## Verschiebebereich

Der Rasterursprung ist weiterhin der `QPlainTextEdit::viewport()` der Konsole.
Damit liegt Rasterzeile 0 unmittelbar unter der Menueleiste und Rasterzeile 24
auf der letzten der 25 Textzeilen unmittelbar vor der Statusleiste.

Der Dialog darf nun teilweise aus dem Textbereich herausgeschoben werden:

- maximale Startzeile: `25 - 1 = 24`
- maximale Startspalte: `80 - 2 = 78`

Auf Zeile 24 bleibt innerhalb der Textflaeche nur die obere Dialog-/Titlebar-
Zeile sichtbar. Auf Spalte 78 bleiben rechts genau zwei Zeichenzellen des
linken Dialogbereichs sichtbar.

## Clipping

Der Login-Dialog bleibt ein frameless top-level `QDialog`, bekommt aber eine
`QRegion`-Maske aus der Schnittmenge seiner globalen Geometrie mit dem echten
Konsolen-Viewport. Alles ausserhalb der Text-Edit-Komponente wird dadurch
nicht gezeichnet. Die Menue- und Statusleisten werden nicht vom Dialog
uebermalt.

Beim Verschieben oder Skalieren des Hauptfensters und beim Lupen-Zoom wird die
Maske gemeinsam mit der gespeicherten 80x25-Rasterposition neu berechnet.

## Anfangsposition

Die erweiterten Verschiebegrenzen veraendern die Anfangsposition nicht. Beim
ersten Oeffnen bleibt der 48x12-Dialog vollstaendig sichtbar und wird anhand
von `(80-48)/2` und `(25-12)/2` zentriert.
