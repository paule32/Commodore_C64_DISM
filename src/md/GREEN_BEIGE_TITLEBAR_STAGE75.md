# Stage 75 – Green & Beige Titelbalken und Menüs

Basis: Stage 74.

## Referenzpalette

Die Gestaltung orientiert sich am bereitgestellten Green-&-Beige-Referenzbild.

- Grün: `#2E7D32`
- Beige: `#F5F0E6`
- warmes Gold-Beige für den Titelbalken-Verlauf: `#D0A65F`

## Titelbalken

Unter Windows wird der native Titelrahmen durch `GreenBeigeTitleBar` ersetzt.

Der neue Titelbalken besitzt:

- 46 px Höhe
- grünen Verlauf links
- warmen beige/goldenen Verlauf rechts
- weiche transparente Wellen auf der grünen Seite
- kleine Lichtpunkte wie in der Referenz
- zentrierten weißen, fetten Fenstertitel
- App-Symbol links
- Minimieren, Maximieren/Wiederherstellen und Schließen rechts
- Doppelklick zum Maximieren/Wiederherstellen
- Ziehen des Fensters über den Titelbalken
- native Windows-Rand-/Ecken-Größenänderung via `WM_NCHITTEST`

Der Schließen-Button ruft ausschließlich `window.close()` auf. Die vorhandene
`closeEvent()`-Logik mit Projekt-/Dokument-Speicherabfragen bleibt damit
unverändert erhalten.

## Menüleiste

Direkt unter dem Titelbalken liegt eine 31 px hohe beige `QMenuBar`.

- Hintergrund: `#F5F0E6`
- Text: dunkles Grün
- Hover/aktive Menüpunkte: `#2E7D32` mit weißem Text
- abgerundete Menüeinträge

Die Hauptmenüs Datei, Ansicht, Favoriten, DISM, Werkzeuge und Hilfe bleiben
inhaltlich unverändert.

## Popup-Menüs

Die Dropdown-Menüs verwenden ebenfalls das Green-&-Beige-Schema:

- beige Fläche
- dunkelgrüner Text
- grüner Selektionsbalken
- weißer Text bei Auswahl
- abgerundete Ecken
- beige Trennlinien

## Hell-/Dunkelmodus

Die Green-&-Beige-Markenfarben des Titel- und Menübereichs bleiben bewusst in
beiden Modi erhalten. Nach einem globalen Theme-Wechsel wird der Chrome-Stil
erneut angewendet; alle übrigen Widgets folgen weiterhin dem vorhandenen
Hell-/Dunkelmodus.

## Tests

- Stage-75-spezifisch: 8/8
- Gesamtprojekt: 735/735
- `py_compile`: erfolgreich

Die native visuelle Windows/PyQt5-Ausführung konnte in der Containerumgebung
nicht durchgeführt werden.
