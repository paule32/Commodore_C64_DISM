# Stage 86 – dBase-Tabellendesigner Workspace und Theme

Basis: Stage 85. Die DBF-Lese-/Schreiblogik und alle Tabellenoperationen bleiben erhalten.

## Dock-Anordnung

Der Tabellendesigner wird nicht mehr in der rechten Dock-Area zusammen mit
`Projekt / Informationen` angelegt. Er wird in der linken Dock-Area direkt
horizontal rechts neben `filesystem_dock` gesplittet.

Beim Öffnen des Tabellen-Designers entsteht ein eigener Workspace:

- `Dateisystem und Dateien` bleibt links sichtbar.
- der normale zentrale Dokumentbereich wird temporär ausgeblendet.
- `Projekt / Informationen`, Protokoll, Localize und Wissen-Dock werden temporär ausgeblendet.
- der Tabellen-Designer nimmt die gesamte verbleibende Fläche rechts vom Dateisystem ein.
- beim Schließen des Tabellen-Designer-Docks wird der vorherige Sichtbarkeitszustand wiederhergestellt.

Die horizontale Größenverteilung wird mit `resizeDocks` auf ungefähr
`320 : restliche Breite` gesetzt.

## Grid im Dark-Mode

Das Felddefinitions-Grid erhält explizite Farben:

- horizontaler Header: `#2a2a2a`, Schrift weiß
- vertikaler Header: `#2a2a2a`, Schrift weiß
- obere linke Grid-Ecke: schwarz
- normale Zellen: schwarz, Schrift weiß
- fokussierte/selektierte Zelle: Navy `#000080`, Schrift weiß
- Feldeditoren / ComboBox / SpinBox: schwarz, Schrift gelb `#ffff00`
- Popup der Feldtyp-ComboBox: schwarz / gelb

Die Selektion arbeitet nun zellenweise (`SelectItems`) statt zeilenweise.

## SpinBoxen

Sowohl `Länge` als auch `Anzahl nach Komma` verwenden eine feste Breite von
84 Pixeln.

## Dock-Symbole

`DockTitleBar` erzeugt seine Float-/Close-Symbole abhängig vom aktuellen
Theme neu:

- Dark-Mode: weiß
- Light-Mode: schwarz

Auch bereits geöffnete Dock-Fenster werden beim Theme-Wechsel unmittelbar
aktualisiert.

## Tests

- Stage-86-spezifisch: 6/6 OK
- Stage 85 + Stage 86 gezielt: 12/12 OK
- komplette Regression: 804/804 OK
