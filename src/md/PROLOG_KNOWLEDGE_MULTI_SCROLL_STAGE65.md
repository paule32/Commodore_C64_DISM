# PROLOG Wissen-Datenbank-Browser – Stage 65

Stage 65 erweitert den Wissen-Datenbank-Browser um mehrere voneinander unabhängige Abfragebereiche.

## Oberfläche

Die rechte Browserhälfte besitzt jetzt eine äußere Haupt-ScrollArea. Darin liegen beliebig viele Zeilen mit folgender Struktur:

```text
[ Hinzufügen ]  ┌──────────────────────────────────────────────┐
[ Löschen    ]  │ innere ScrollArea / Wissens-Abfrage 1       │
                │ Eingabe, Prüfen+, Fakten-Level, Alternativen │
                └──────────────────────────────────────────────┘

[ Hinzufügen ]  ┌──────────────────────────────────────────────┐
[ Löschen    ]  │ innere ScrollArea / Wissens-Abfrage 2       │
                │ unabhängiger Entscheidungsweg               │
                └──────────────────────────────────────────────┘
```

Die Buttons liegen links, die jeweilige innere ScrollArea rechts.

## Hinzufügen

`Hinzufügen` erzeugt direkt unter dem angeklickten Bereich eine neue leere Wissens-Abfrage und aktiviert sie. Bereits bestehende Abfragen bleiben vollständig erhalten.

Jede Abfrage speichert separat:

- ausgewähltes Prädikat/Fakt
- Level-Werte und Level-Buttons
- aktiven Level
- Parent-Prefix der Alternativen
- Alternativ-ComboBox und lokalen `Prüfen`-Zustand
- grün/rotes Alternativen-Statuslabel
- manuelle Eingabe und Statusanzeige

Ein Klick in der Faktenliste wirkt auf die aktuell aktive Abfrage. Der aktive Bereich wird mit einem grünen Rahmen markiert.

## Löschen

`Löschen` entfernt nur den zugehörigen Abfragebereich. Andere Lösungen bleiben bestehen.

Mindestens ein Bereich bleibt immer vorhanden. Wird der letzte Bereich gelöscht, wird er stattdessen geleert, damit der `Hinzufügen`-Button weiterhin erreichbar bleibt.

## Dynamische Höhe

Die innere ScrollArea passt ihre Höhe an den Inhalt an:

- Mindesthöhe: 170 px
- Maximalhöhe: 430 px
- bis 430 px wächst der Bereich mit seinen Buttons/ComboBoxen/Labels
- erst oberhalb davon scrollt die innere ScrollArea selbst
- die äußere Haupt-ScrollArea übernimmt das Scrollen über mehrere Abfragebereiche

## Erhaltene Stage-61..64-Logik

Unverändert bleiben:

- Parent-`▼` öffnet nur passende Kinder-Alternativen
- ComboBox erscheint direkt unter dem selektierten Parent-Button
- bereits im aktuellen Entscheidungsweg verwendete Werte werden nicht erneut angeboten
- lokaler `Prüfen`-Button validiert die ausgewählte Alternative
- bei Erfolg verschwinden ComboBox und `Prüfen`, der neue Level-Button bleibt
- `weitere Alternativen vorhanden` bleibt grün
- `keine weiteren Alternativen` bleibt rot
- Faktenname-/Stelligkeitsfilter sowie Dark-Mode-Header bleiben erhalten

## Datenbankwechsel

Beim Öffnen einer anderen Wissen-Datenbank bleiben Anzahl und Anordnung der inneren Abfragebereiche bestehen, ihre alten Query-Inhalte werden aber zurückgesetzt, weil sie zur vorherigen Datenbank gehören.

## Tests

Stage-65-spezifisch: 10/10 erfolgreich.

Vollständige Regression: 662/662 erfolgreich.

Die PyQt5-GUI konnte in der Containerumgebung nicht nativ/visuell gestartet werden; die GUI-Struktur wurde deshalb über Quellcode-/Regressionsprüfungen abgesichert.
