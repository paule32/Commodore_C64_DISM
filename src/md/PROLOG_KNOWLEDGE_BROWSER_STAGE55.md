# Stage 55 – PROLOG Wissen-Datenbank-Browser

## Projekt-Tree

Unter `PROLOG-Programme` wird der geschützte Unterknoten `Wissen-Datenbanken`
angelegt. Per Rechtsklick können vorhandene `*.pl`/`*.prolog`-Dateien über
einen File-Open-Dialog hinzugefügt werden. Die Referenzen werden getrennt vom
normalen PROLOG-Programmcode unter `Category.prolog.knowledge` in der `*.pro`
Projektdatei gespeichert.

Die Wissen-Datenbanken werden nicht automatisch als normale PROLOG-Module in
den F2-Linkpfad aufgenommen. Damit bleiben Programmcode und externe
Wissensbestände getrennt.

Kontextmenü am Knoten:

- `Wissensdatenbank hinzufügen …`
- `Wissensdatenbank-Browser öffnen`
- `Alle Referenzen entfernen`
- `Hilfe`

Kontextmenü an einer Datenbankdatei:

- `Im Wissensdatenbank-Browser öffnen`
- `Quelltext öffnen`
- `Aus Projekt entfernen`

Ein Doppelklick auf eine Wissen-Datenbank öffnet sie direkt im Browser.

## Wissen-Datenbank-Browser

Oben befindet sich das Verzeichnis der Wissen-Datenbanken. Alle `*.pl` und
`*.prolog` aus diesem Verzeichnis werden in einer ComboBox angezeigt. Rechts
neben der ComboBox liegt der Button `Öffnen`.

Projekt-Wissen-Datenbanken aus anderen Verzeichnissen bleiben ebenfalls in der
ComboBox erreichbar und werden mit ihrem Verzeichnispfad gekennzeichnet.

## Fakten-/Regelbaum

Die linke `QTreeWidget`-TreeList zeigt jede Prädikat-Signatur nur einmal.
Mehrfach vorhandene identische Fakten führen daher nicht zu doppelten
sichtbaren Einträgen. Falls derselbe Name mit mehreren Stelligkeiten existiert,
wird die Stelligkeit im Namen ergänzt.

Beispiel:

```prolog
apfel(gesund).
apfel(gesund).
apfel(rot).
```

Im Baum erscheint `apfel` nur einmal. Die möglichen Werte `gesund` und `rot`
werden als eindeutige Alternativen behandelt.

## Abfrage-Level

Wird `apfel` gewählt, entsteht der erste Button-Level:

```text
apfel
```

Steht im Eingabefeld `gesund` und `Prüfen +` wird betätigt, prüft der vorhandene
PROLOG-Resolver die Teil-/Vollabfrage. Nur wenn sie wahr ist, entsteht:

```text
apfel  →  gesund
```

Jeder Button entspricht einem Level. Ein angeklickter Level erhält einen
grünen Rahmen. Die Entscheidung wird nach jedem Hinzufügen, Entfernen oder
Ersetzen eines Levels neu ausgewertet.

Bei mehrstelligen Prädikaten wächst die Kette weiter:

```text
obst  →  apfel  →  gesund
```

## Flow-/ScrollArea

Die Level-Buttons liegen in einem eigenen Flow-Layout innerhalb einer
`QScrollArea`. Reicht die verfügbare horizontale Breite nicht mehr aus, wird in
die nächste Zeile umgebrochen. Die ScrollArea kann anschließend vertikal
scrollen.

## Löschen von Levels

Rechtsklick auf einen Level-Button öffnet:

```text
Diesen Level und alle folgenden Level löschen
```

Wird beispielsweise Level 1 gelöscht, werden auch alle von Level 1 abhängigen
Sub-Level entfernt. Die verbleibende Abfrage wird danach neu aufgelöst.

## Alternativen

Besitzt ein Level mehr als eine mögliche Alternative, erscheint rechts am
Button ein `▼`-Button. Er öffnet einen Auswahldialog.

- bis 10 Alternativen: direkte Liste
- mehr als 10 Alternativen: zusätzliches Suchfeld
- `OK`: gewählte Alternative übernimmt diesen Level

Beim Wechsel einer Alternative werden alle nachfolgenden Sub-Level entfernt,
weil deren Gültigkeit von der alten Auswahl abhängig war. Anschließend startet
die Entscheidungsfindung erneut.

## Regeln

Der GUI-Browser verwendet nicht nur einen Stringvergleich auf Fakten, sondern
den vorhandenen Python-seitigen PROLOG-Parser und SLD-Resolver. Dadurch sind
auch Regeln im unterstützten Compiler-Subset abfragbar, zum Beispiel:

```prolog
blutdruck(4711, 150, 90).
hoher_blutdruck(Patient) :-
    blutdruck(Patient, Systolisch, _),
    Systolisch > 140.
```

Die Browser-Abfrage `hoher_blutdruck(4711)` ist damit wahr.

## Dark-/Light-Mode

Der Browser folgt dem globalen Programm-Theme. Level-Buttons, TreeList,
ComboBox, Eingabefeld, ScrollArea und Alternativdialog besitzen eigene
Dark-/Light-Styles. Der aktive Level verwendet in beiden Modi einen grünen
Rahmen.

## Beispiele

- `examples/prolog_database/obst_wissen_stage55.pl`
- `examples/prolog_database/wissen_browser_stage55.pro`

`obst_wissen_stage55.pl` enthält absichtlich einen doppelten Fakt sowie mehr
als zehn `farbe/1`-Alternativen, um Deduplizierung und Suchfeld direkt testen zu
können.
