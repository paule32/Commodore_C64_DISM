# Stage 85 – dBase-Tabellendesigner / DBF

Basis: Stage 84. Die bestehenden C64-, MRU- und dBase-Formulardesigner-Funktionen bleiben erhalten.

## Menü

Unter `Datei -> Neu -> dBase` steht nach `Formular` zusätzlich:

```text
Tabelle
```

Der Eintrag öffnet den Tabellendesigner als `QDockWidget`.

## Mehrere Tabellen

Der Designer besitzt ein äußeres `QTabWidget`. Jeder äußere Tab entspricht einer Tabelle und erhält zunächst Namen wie `Tabelle 1`, `Tabelle 2`, ... . Nach Laden oder Speichern wird der Dateiname, z. B. `Kunden.dbf`, als Tabtitel verwendet.

Jeder Tabellen-Tab enthält oberhalb seines inneren SubTabWidgets die Buttons:

- `Speichern`
- `Speichern unter ...`
- `Laden`

Das innere TabWidget enthält zunächst den SubTab `Felder`.

## Feldraster

Das Feldraster besitzt horizontale Header:

1. `Feldname`
2. `Feldtyp`
3. `Länge`
4. `Anzahl nach Komma`
5. `Index`

Die vertikalen Header werden nach jeder Strukturänderung vollständig neu nummeriert: `1, 2, 3, ...`.

### Editoren

- Feldname: direkt editierbares Grid-Feld
- Feldtyp: `QComboBox`
- Länge: `QSpinBox`
- Anzahl nach Komma: `QSpinBox`
- Index: `QCheckBox`

Verfügbare Feldtypen:

- Zeichen (`C`)
- Dezimal (`N`)
- Fließkomma (`F`)
- Datum (`D`)
- Logisch (`L`)
- Memo (`M`)

Für feste Feldtypen werden Länge/Nachkommastellen automatisch gesetzt, z. B. Datum = 8, Logisch = 1, Memo = 10.

## Kontextmenü

Rechtsklick im Feldraster öffnet:

```text
Hinzufügen
Kopieren
Ausschneiden
Einfügen
Löschen
```

- `Hinzufügen`: fügt hinter der aktuellen Zeile eine leere Feldzeile ein.
- `Kopieren`: kopiert die komplette aktuelle Felddefinition in den Designer-Zwischenspeicher.
- `Ausschneiden`: kopiert die Zeile und entfernt sie aus dem Grid.
- `Einfügen`: fügt die kopierte Feldzeile an der aktuell fokussierten Position ein.
- `Löschen`: entfernt die aktuelle Feldzeile.

Nach Hinzufügen, Einfügen, Ausschneiden und Löschen werden die Feldnummern neu berechnet.

## DBF-Reader/Writer

Stage 85 enthält einen lokalen DBF-Strukturreader/-writer. Er erzeugt klassische DBF-Dateien mit Feldbeschreibungen und kann bestehende DBF-Felddefinitionen sowie Datensätze wieder einlesen. Beim strukturellen Speichern werden vorhandene Werte über die ursprünglichen Feldnamen soweit möglich übernommen; neue Felder bleiben leer, entfernte Felder werden verworfen.

Die `Index`-Checkbox ist eine Designer-Markierung. Klassische DBF-Dateien enthalten die Feld-zu-Index-Zuordnung nicht im normalen Feldheader; reale NDX/MDX-Dateien werden in Stage 85 bewusst noch nicht erzeugt oder verändert. Damit die Markierung bei erneutem Laden nicht verloren geht, speichert der Designer sie ergänzend in `<datei>.dbf.d64meta.json`.

Bei Memo-Feldern wird für neue Tabellen eine leere `.dbt`-Datei angelegt. Beim `Speichern unter ...` einer geladenen Tabelle wird eine vorhandene `.dbt`-Datei mit übernommen.

## Sicherheit / Validierung

DBF-Feldnamen werden vor dem Schreiben validiert:

- 1 bis 10 Zeichen
- Buchstaben, Ziffern und `_`
- erstes Zeichen Buchstabe oder `_`
- keine doppelten Feldnamen (Groß-/Kleinschreibung ignoriert)

Die DBF-Ausgabe wird zunächst temporär geschrieben und anschließend per `os.replace()` atomar an die Zielstelle gesetzt.
