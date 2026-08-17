# PROLOG Stage 50 - externe Wissensdatenbanken

Stage 50 erweitert die native PROLOG-Runtime um separat ladbare, speicherbare und
wieder entladbare Wissensbestaende. Eine geladene Datei bekommt eine stabile
**Database-ID**. Jede aus dieser Datei geladene oder gezielt dort angelegte dynamische
Klausel traegt intern genau diese Owner-ID.

## Zielmodell

```text
PROLOG-Runtime
  |
  +-- statischer Programmcode
  +-- lokale dynamische Klauseln (Database-ID 0)
  +-- DB 1: medizin_wissen.pl    [read_only, knowledge]
  +-- DB 2: patient_4711.pl      [read_write, record]
  +-- DB 3: ...
```

Normale Prädikatsaufrufe koennen Klauseln aus allen aktuell geladenen Datenbanken
verwenden. Destruktive Operationen sind dagegen an genau eine Database-ID gebunden.
Damit kann eine Patientenakte entladen werden, ohne das allgemeine Fachwissen oder
eine andere gleichzeitig geladene Akte zu entfernen.

## API

### Oeffnen

```prolog
database_open("patient.pl", DB).
```

Kurzform fuer:

```prolog
database_open("patient.pl", read_write, record, DB).
```

Mit Modus:

```prolog
database_open("wissen.pl", read_only, DB).
```

Mit Modus und Art:

```prolog
database_open("wissen.pl", read_only, knowledge, DB).
database_open("patient.pl", read_write, record, DB).
database_open("system.pl", read_only, system, DB).
```

`DB` ist eine positive, waehrend der Runtime stabile Integer-ID. `0` ist fuer den
prozesslokalen dynamischen Standardbestand reserviert.

### Datenbankarten

- `record` - veraenderlicher Datensatz, z. B. eine Patientenakte.
- `knowledge` - separat ladbares Regel-/Faktenwissen; kann read-only oder read-write sein.
- `system` - unveraenderlicher Systembestand; kann zur Laufzeit nicht geschlossen oder
  durch assert/retract veraendert werden.

### Modi

- `read_only` - keine Aenderung und kein Speichern.
- `read_write` - assert/retract und Speichern erlaubt (ausser `system`).

Eine fehlende `read_write`-Datei wird als leerer Datenbestand angelegt. Eine fehlende
`read_only`-Datei laesst `database_open` fehlschlagen.

## Abfragen

Geladene Fakten und Regeln nehmen an der normalen PROLOG-Suche teil:

```prolog
database_open("medizin_wissen.pl", read_only, knowledge, W),
database_open("patient_4711.pl", read_write, record, P),
kontrolle_empfohlen(4711).
```

Die Regel kann aus `W`, die Fakten koennen aus `P` stammen.

## Gezielte Aenderungen

Explizit:

```prolog
database_assert(DB, fakt(a)).
database_asserta(DB, fakt(a)).
database_assertz(DB, fakt(a)).
database_retract(DB, fakt(a)).
```

`database_assert/2` ist ein Alias fuer `database_assertz/2`.

Oder ueber einen aktiven Kontext:

```prolog
database_select(DB),
assert(fakt(a)),
retract(altes_fakt(a)),
database_select(0).
```

Kurzzeitig und automatisch wiederhergestellt:

```prolog
with_database(DB, assert(fakt(a))).
```

Der vorherige Datenbankkontext wird nach der synchronen Zielauswertung wiederhergestellt.

### Warum retract/1 nicht global loescht

`retract/1` durchsucht fuer destruktive Aenderungen nur Klauseln der aktuell ausgewaehlten
Owner-ID. Bei `database_select(0)` werden daher nur normale lokale Runtime-Assertions
veraendert. Eine externe Datenbank muss fuer Aenderungen explizit ausgewaehlt werden.

## Zustand

```prolog
current_database(DB).
database_modified(DB).
```

`database_modified/1` ist genau dann erfolgreich, wenn der Datenbestand seit Laden bzw.
letztem erfolgreichen Speichern veraendert wurde.

## Speichern

```prolog
database_save(DB).
database_save_as(DB, "patient_neu.pl").
```

Nur Klauseln mit der passenden Database-ID werden serialisiert. Regeln werden wieder als
PROLOG-Quelltext geschrieben. Laufzeitvariablen bekommen beim Speichern stabile kanonische
Namen `_V0`, `_V1`, ...; wiederholte Vorkommen derselben Klauselvariablen behalten denselben
Namen.

Das Speichern erfolgt atomar:

```text
Zieldatei bleibt bestehen
       |
       +--> <datei>.tmp schreiben
       +--> FlushFileBuffers
       +--> Datei schliessen
       +--> MoveFileExA(REPLACE_EXISTING | WRITE_THROUGH)
```

Bei einem Schreibfehler wird die temporaere Datei bestmoeglich geloescht und die alte
Zieldatei bleibt erhalten.

`database_close/1` speichert **nicht automatisch**. Dadurch ist sichtbar, wann persistente
Aenderungen committed werden. Fuer einen veraenderten RECORD ist der typische Ablauf:

```prolog
database_save(DB),
database_close(DB).
```

## Entladen

```prolog
database_close(DB).
```

Die Runtime markiert nur die dynamischen Klauseln mit genau dieser Owner-ID als inaktiv,
kompaktiert den dynamischen Klauselspeicher und fuehrt danach die vorhandene Dynamic-Heap-GC
aus. Andere geladene Wissensbestaende bleiben erhalten. War diese DB der aktive
`database_select`-Kontext, wird der Kontext auf `0` zurueckgesetzt.

`system`-Datenbanken koennen absichtlich nicht mit `database_close/1` entladen werden.

## Datei-Parser

Externe Dateien koennen Fakten und Regeln enthalten:

```prolog
patient(4711).

hoher_blutdruck(P) :-
    blutdruck(P, S, _),
    S > 140.
```

Unterstuetzt sind ausserdem `%`-Zeilenkommentare und `/* ... */`-Blockkommentare.
Der Loader verwendet eine eigene Variablentabelle, damit Variablen einer geladenen Regel
nicht mit Variablen einer gerade laufenden REPL-Anfrage kollidieren.

## Aktuelle Runtime-Grenzen

- maximal 32 gleichzeitig geoeffnete Datenbanken
- Dateiname maximal 259 Bytes plus Nullterminator
- Quelldatei derzeit knapp 1 MiB
- einzelne Klausel derzeit etwa 4 KiB Parserfenster
- Datenbankinhalt muss in den vorhandenen dynamischen Klausel-/Heap-Grenzen Platz finden

Diese Grenzen sind Runtime-Konstanten und koennen spaeter erweitert werden, ohne das
Database-ID-Konzept zu aendern.

## Sicherheit der Zuordnung

Die bestehende 16-Byte-Struktur des dynamischen Klauselrecords wurde absichtlich nicht
veraendert. Parallel dazu liegt eine Owner-Tabelle:

```text
DYN_DB record i       DYN_DB_OWNER[i]
----------------      ----------------
active                 Database-ID
functor
arity
persistent root
```

`asserta`, Kompaktierung und GC halten Record und Owner-ID in derselben Reihenfolge.
Dadurch bleiben bestehende Choice-Point-/Unification-/Dynamic-Heap-Pfade weitgehend
unveraendert.

## Beispiele

Siehe `examples/prolog_database/`:

1. `arzt_patient.pl` + `patient_4711.pl`
2. `arzt_mit_fachwissen.pl` + `medizin_wissen.pl` + `patient_4711.pl`
