# PROLOG Wissen-Browser – Stage 74

Stage 74 erweitert den Stage-73-Wissen-Browser um persistente Abfragezustände.
Die PROLOG-Wissensdateien selbst werden dabei nicht verändert.

## Persistenter Zustand pro Wissensdatenbank

Für jede geöffnete `*.pl`/`*.prolog`-Wissensdatenbank wird ein eigener Zustand
in den vorhandenen Qt-Anwendungseinstellungen (`QSettings`, Organisation
`paule32`, Anwendung `Qt5D64Explorer`) abgelegt.

Gespeichert werden:

- Anzahl und Reihenfolge aller inneren Query-ScrollAreas/Lanes
- aktuell aktive Lane
- ausgewähltes Prädikat/Fakt mit Name und Stelligkeit
- alle bereits bestätigten Level-/Alternativwerte
- aktiver Level-Button
- noch nicht bestätigter Text im Eingabefeld
- ob die Alternativen-ComboBox geöffnet war
- Parent-Level der geöffneten Alternativen-ComboBox
- aktuell ausgewählter ComboBox-Eintrag

Die Speicherung erfolgt automatisch nach Query-Aktionen, beim Wechsel der
Wissensdatenbank sowie beim Schließen/Ausblenden des Wissen-Docks.

## Wiederherstellung

Beim erneuten Öffnen derselben Wissensdatenbank wird der gespeicherte Zustand
automatisch geladen. Die Multi-ScrollArea-Struktur wird wieder aufgebaut und
für jede Lane werden Fakt/Prädikat und die bereits bestätigten Level als
Buttons dargestellt.

War beim Speichern die Alternativen-ComboBox geöffnet, wird auch dieser Parent-
Kontext wiederhergestellt. Ein noch vorhandener ComboBox-Wert wird wieder
selektiert.

## Schutz bei geänderten Wissensdateien

Gespeicherte Werte werden nicht blind übernommen. Jeder gespeicherte Term wird
über `PrologKnowledgeBase.parse_value()` erneut geparst. Danach wird jeder
Präfix mit `PrologKnowledgeBase.accepts()` erneut gegen die aktuell geladene
Wissensdatenbank geprüft.

Ist nach einer Änderung der Wissensdatei ein alter Level nicht mehr gültig,
wird der Pfad ab diesem Level abgeschnitten. Davor weiterhin gültige Level
bleiben erhalten.

## Umlaute

Die Zustandsdaten werden als JSON mit `ensure_ascii=False` gespeichert. Namen
und Werte wie `äpfel`, `größe`, `überreif` bleiben dadurch unverändert erhalten.

## Stage 73 bleibt erhalten

Die Stage-72/73-Korrekturen für Lane-State und `alternative_overlay_layout`
bleiben unverändert. Ebenso bleiben Haupt-ScrollArea, mehrere innere Lanes,
Parent-▼, Alternativen-ComboBox und `Prüfen +` erhalten.

## Tests

- Stage-74-spezifisch: 7/7
- Wissen-Browser-Regressionsgruppe: 106/106
- Gesamtsuite: 727/727

Die native Windows/PyQt5-Oberfläche wurde in der Containerumgebung nicht
visuell ausgeführt.
