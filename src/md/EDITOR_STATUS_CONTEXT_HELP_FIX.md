# Editor-, Statusleisten- und Kontexthilfe-Erweiterung

## Protokoll-Dock

Der bisher unterhalb des Protokollfensters angeordnete Button wurde entfernt.
`Protokoll löschen` befindet sich nun direkt in der Dock-Titelleiste neben dem
Schriftzug `Protokoll`.

Alle drei Dock-Fenster verwenden eine eigene Titelleiste mit weißen Symbolen
für:

- Andocken beziehungsweise Abdocken
- Schließen

Die Titelleiste kann mit der Maus gezogen und per Doppelklick zwischen
angedocktem und frei schwebendem Zustand umgeschaltet werden.

## Statusleiste

Die Statusleiste enthält drei dauerhafte Bereiche:

### Tastaturstatus

- `INS` ist grün, wenn der Einfügemodus aktiv ist.
- `INS` ist rot, wenn der Überschreibmodus aktiv ist.
- `CAPS` zeigt den Zustand von Caps Lock an.
- `NUM` zeigt den Zustand von Num Lock an.

Unter Windows werden Caps Lock und Num Lock direkt über `GetKeyState`
abgefragt. Für andere Plattformen existiert eine ereignisbasierte
Fallback-Verfolgung.

### Dateiinformation

Die aktuelle Größe der zu speichernden Datei wird in Bytes angezeigt. Die
Anzeige wird bei Texteingaben, Hex-Änderungen und zusätzlich alle 250 ms
aktualisiert.

### Cursorposition

Für Texteditoren werden die aktuelle Zeile und Spalte angezeigt. Im
Hex-Editor werden Byte-Zeile und Byte-Spalte auf Basis des aktuellen
Cursorindex angezeigt.

## Kontextmenü der Dokumentregisterkarten

Ein Rechtsklick auf eine Registerkarte öffnet:

1. Neu
2. Hilfe
3. Speichern
4. Speichern unter...
5. Schließen
6. Umbenennen

Die Aktionen beziehen sich immer auf die angeklickte Registerkarte.
`Umbenennen` ändert bei gespeicherten Dokumenten auch den Dateinamen auf dem
Datenträger. Vorhandene Projektverweise werden entsprechend aktualisiert. Bei
ungespeicherten Dokumenten wird zunächst nur der Registerkartenname geändert.

Die Schließen-Symbole der Registerkarten sind als weiße X-Symbole auf einem
dunklen Button ausgeführt und bleiben damit auch im Dunkelmodus gut sichtbar.

## Datei -> Neu

Das Hauptmenü enthält nun das Untermenü `Datei -> Neu` mit:

- BASIC-Programm
- Assembler-Programm
- Pascal-Programm
- C-Programm
- C-64 Character Map
- C-64 Text Screen
- C-64 Pixel Screen
- Textdatei

BASIC, Assembler, Pascal und C erhalten einen kleinen sprachspezifischen
Startquelltext und eine passende vorgeschlagene Dateiendung. Die C64-Einträge
öffnen den vorhandenen Spezialeditor mit einem neuen leeren Dokument.

## F1-Kontexthilfe

`F1` ermittelt den Bezeichner direkt am Cursor. Die Hilfesprache wird anhand
der aktuellen Datei gewählt:

- `.bas`, `.basic` -> BASIC
- `.asm`, `.s`, `.a65`, `.m68k`, `.inc` -> Assembler
- `.pas`, `.pp` -> Pascal
- `.c`, `.h` -> C

Im erzeugten ASM-Tab wird immer die Assembler-Hilfe verwendet.

Vor dem Öffnen der Hilfe wird vorläufig eine MessageBox mit dem erzeugten
CHM-Link angezeigt. Der zu entfernende Debugbereich ist im Quelltext deutlich
markiert:

```python
# DEBUG: Diese MessageBox zeigt vorläufig den erzeugten CHM-Link.
# Nach Abschluss der Hilfethemen-Zuordnung kann sie entfernt werden.
```

Das Linkformat lautet beispielsweise:

```text
mk:@MSITStore:T:\Pfad\Hilfe.chm::/pascal/Create.html
```

Nach Bestätigung öffnet der integrierte CHM-Viewer die zuletzt verwendete
Hilfedatei. Er sucht das Cursorwort zuerst im Schlüsselwortindex und danach im
Themenbaum. Sprache, Thementitel, Dateiname und HTML-Pfad fließen in die
Trefferbewertung ein.
