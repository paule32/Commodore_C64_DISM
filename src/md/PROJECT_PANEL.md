# Projekt- und Hilfe-Panel

## Rechter Dockbereich

Der bisherige Informationsbereich ist jetzt ein äußerer Registerbereich mit
zwei Tabs:

1. **Projekt**
2. **Informationen**

Der Tab **Informationen** enthält weiterhin die vorhandenen Unterregister
`DISM START` und `Datei-Informationen`.

## Projektdatei

Projektdateien besitzen die Erweiterung `.pro` und verwenden ein lesbares
INI-Format. Dateipfade werden nach Möglichkeit relativ zum Speicherort der
Projektdatei abgelegt. Dadurch kann ein kompletter Projektordner verschoben
oder kopiert werden.

Die festen Kategorien sind:

- BASIC - Programme
- Assembler-Programme
- Pascal-Programme
- C-Programme
- Character Map's
- Paletten
- Char Screen's
- Pixel Screen's
- Textdateien
- SID's
- Bilder
- Sonstiges

Diese Kategorien sind geschützte Root-Knoten. `Umbenennen` und `Löschen` sind
für jeden Root-Knoten deaktiviert. Löschen eines Dateieintrags entfernt nur
die Referenz aus dem Projekt; die Datei auf dem Datenträger bleibt erhalten.

## Bedienung

Über der TreeList befindet sich links ein Öffnen-Button und daneben das
Pfadfeld der `.pro`-Datei. Unter der TreeList befinden sich:

- `Neu`
- `Speichern`
- `Speichern unter...`

`Neu` fragt bei vorhandenen Projektdaten mit drei eindeutigen Schaltflächen:

- `Ja, speichern`
- `Nein, nicht speichern`
- `Abbrechen`

Das Kontextmenü eines Projektknotens enthält:

- Hilfe
- Umbenennen
- Kopieren
- Einfügen
- Löschen

Ein Dateiknoten wird mit einem Klick geöffnet. Character Maps, Paletten,
Char-Screens und Pixel-Screens verwenden ihre integrierten Spezialeditoren.
Quelltexte werden im zentralen Dokumenteditor geöffnet. SID- und Bilddateien
werden an die im Betriebssystem registrierte Anwendung übergeben.

Zum Einfügen kann entweder ein zuvor kopierter Projekteintrag oder ein normaler
Dateipfad aus der Zwischenablage verwendet werden.

## Hilfe-Themen

Themenknoten mit Unterthemen erhalten ein Ordnersymbol. Blattknoten ohne
Unterthemen erhalten ein Dateisymbol. Dadurch ist die Hierarchie bereits am
Icon erkennbar.

## Neue Dateien aus dem Projekt-Kontextmenü

Der erste Eintrag des Kontextmenüs lautet **Neu**. Die Aktion verwendet immer
die Kategorie des angeklickten Root- oder Dateiknotens und erzeugt im
Projektverzeichnis eine echte neue Datei.

Die Namen werden fortlaufend vergeben:

```text
Unbenannt_1.c
Unbenannt_2.c
Unbenannt_3.c
```

Vor der Vergabe werden sowohl alle sichtbaren Projekteinträge als auch bereits
vorhandene Dateien im Zielverzeichnis geprüft. Die Nummer wird so lange erhöht,
bis weder ein Projektknoten noch eine Datei kollidiert.

Standarderweiterungen:

| Kategorie | Erweiterung |
|---|---|
| BASIC - Programme | `.bas` |
| Assembler-Programme | `.asm` |
| Pascal-Programme | `.pas` |
| C-Programme | `.c` |
| Character Map's | `.chr` |
| Paletten | `.pal` |
| Char Screen's | `.scr` |
| Pixel Screen's | `.px16` |
| Textdateien | `.txt` |
| SID's | `.sid` |
| Bilder | `.png` |
| Sonstiges | `.dat` |

Character Maps, Paletten, Char-Screens und Pixel-Screens werden bereits mit
einer gültigen leeren Dateistruktur angelegt und direkt im zugehörigen
Spezialeditor geöffnet. Quelltexte und sonstige Textdateien öffnen sich im
zentralen Dokumenteditor. Für Bilder wird eine schwarze 320×200-PNG-Datei
erzeugt. Neue SID-Dateien erhalten einen minimalen PSID-v2-Rahmen.

## Hilfe-Schaltfläche und Dunkelmodus

In der Haupt-Toolbar befindet sich unmittelbar links neben der Lupe mit dem
Pluszeichen eine Hilfe-Schaltfläche. Das Fragezeichen-Icon passt seine Farbe an
Hell- und Dunkelmodus an und öffnet den vorhandenen CHM-Hilfedialog.

Der Projekt-Öffnen-Button links neben dem Projektpfad besitzt im Dunkelmodus
nun eine explizite dunkle Fläche mit passenden Hover-, Pressed- und
Disabled-Zuständen. Der native graue Windows-Hintergrund wird damit nicht mehr
verwendet.
