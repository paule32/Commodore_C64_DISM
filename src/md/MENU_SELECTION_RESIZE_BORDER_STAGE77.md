# Stage 77 – Menüauswahl und sichtbarer Resize-Rand

Basis: Stage 76.

## Menüauswahl

Die Theme-Farben aus Stage 76 bleiben erhalten. Geändert wurde nur die Schriftfarbe selektierter Menüeinträge:

- Auswahl-Hintergrund: `#2E7D32`
- Auswahl-Schrift: `#FFFFFF`

Das gilt sowohl für die obere `QMenuBar` als auch für `QMenu`-Popup-Einträge. Dark-/Light-Mode, Arial 9 pt und die Farben deaktivierter Einträge bleiben unverändert.

## Hauptfenster-Rand

Das frameless Windows-Hauptfenster besitzt jetzt einen sichtbaren Rand:

- Breite: 2 px
- Farbe: Beige `#F5F0E6`

Dazu reserviert `ExplorerWindow` unter Windows 2 px `contentsMargins` und zeichnet den Rand im eigenen `paintEvent()`.

Die vorhandene native Resize-Logik über `WM_NCHITTEST` bleibt erhalten. Die sichtbare Randbreite und die Maus-Hit-Zone sind absichtlich getrennt:

- `FRAMELESS_VISIBLE_BORDER = 2`
- `FRAMELESS_RESIZE_BORDER = 7`

Dadurch bleibt der Rand optisch exakt 2 px breit, während Kanten und Ecken weiterhin komfortabel mit der Maus getroffen werden können.

## Tests

- Stage-76/77 gezielt: 14/14
- Gesamtprojekt: 749/749
