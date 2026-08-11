# dBase Qt5 Console Stage 19 – 80x25-Zeichenraster

Die Standardgeometrie der erzeugten dBase-Konsole wird jetzt aus dem aktuellen
Konsolenfont berechnet. Der sichtbare `QPlainTextEdit`-Viewport soll exakt
80 Zeichen breit und 25 Textzeilen hoch sein.

## Berechnung

- Spalten: `80 * QFontMetrics::horizontalAdvance('M')`
- Zeilen: `25 * QFontMetrics::lineSpacing()`
- Menü, Tabs/Lupen, 3-Pixel-Außenrahmen, 2-Pixel-Status-Trennlinie und
  Statusleiste liegen außerhalb dieser 80x25-Textfläche und werden über die
  reale Qt-Layoutdifferenz automatisch in die Fenstergröße eingerechnet.

## Zoom

Die beiden Lupen ändern `g_font_point_size` jeweils exakt um `+1 pt` bzw.
`-1 pt`. Danach wird das Fenster erneut so vermessen, dass der Text-Viewport
80x25 Zellen umfasst.

## Pixel-Feinkorrektur

Qt/Windows kann Punktgrößen wegen DPI und Font-Metriken auf ganze Pixel
runden. Deshalb existiert getrennt vom Punktwert `g_font_pixel_adjust`.
Normal ist dieser Wert `0`. Nur wenn nach dem Layout noch eine Abweichung von
mehr als einem Pixel verbleibt, werden die Varianten `-1 px` und `+1 px`
getestet. Die Variante mit dem kleinsten 80x25-Rasterfehler wird gewählt.

Damit bleibt der vom Benutzer gewählte Punktwert logisch unverändert; die
Pixelkorrektur dient ausschließlich dem Raster-Fit.

## Beibehaltene Stage-18-Funktionen

- normales Hauptmenü
- CP437/Terminal-Zeichenrahmen nur für Popup-Untermenüs
- zwei Lupen
- Konsole-Tab immer vorhanden
- DEBUG-Tab nur bei `SET DEBUG ON`
- 3-Pixel-Außenrahmen
- 2-Pixel-Trennlinie über der Statusleiste
- Margin/Padding/Document-Margin des Texteditors = 0
- CLEAR SCREEN / SET COLOR TO / SET BORDERCOLOR TO
