# PROLOG Wissen-Browser – Stage 63

## Ziel

Bereits als Buttons dargestellte Fakten-/Argumentwerte dürfen im aktuellen
Entscheidungsweg nicht erneut als Alternative angeboten oder eingefügt werden.

Damit sind beispielsweise gültig:

- `apfel -> gesund -> essbar`
- `apfel -> essbar -> gesund`

Nicht mehr möglich ist:

- `apfel -> gesund -> essbar -> gesund`

## Umsetzung

`PrologKnowledgeDialog._used_decision_texts()` sammelt den sichtbaren Root-/Fakt-
Button und alle Werte in `level_values` normalisiert per `casefold()`.

`_remaining_alternatives()` filtert die vom PROLOG-Resolver gelieferten
Alternativen gegen diese Menge. Die logischen PROLOG-Lösungen selbst bleiben
unverändert; die Eindeutigkeitsregel ist eine GUI-/Entscheidungsweg-Regel.

Die Filterung wird verwendet bei:

1. Aufbau der Parent-Pfeile,
2. Öffnen der Alternativ-ComboBox,
3. grün/rotem Alternativen-Statuslabel,
4. zusätzlicher Prüfung bei manueller Eingabe über `Prüfen +`.

Beim Löschen eines Buttons werden wie bisher alle Sub-Level entfernt. Danach
wird der Pfad neu aufgebaut; dadurch werden gelöschte Werte wieder als mögliche
Alternativen verfügbar, sofern sie logisch zum verbliebenen Parent passen.

## Beispiel

Die Datei `stage63/examples/prolog_database/wissen_eindeutiger_pfad_stage63.pl`
enthält absichtlich einen logischen Pfad, in dem `gesund` später erneut
auftauchen könnte. Der PROLOG-Resolver kennt diese Lösung weiterhin, der
Wissen-Browser unterdrückt den zweiten `gesund`-Eintrag jedoch im aktuellen
sichtbaren Entscheidungsweg.
