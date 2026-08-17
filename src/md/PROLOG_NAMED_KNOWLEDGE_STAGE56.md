# PROLOG – benannte Wissenswerte (Stage 56)

Stage 56 erweitert dBase2Many-PROLOG um benannte Wissenswerte für Wissensdatenbanken und Programme.

## Syntax

```prolog
_apfel = "Ein Apfel ist gesund".
_name = "Max Mustermann".
_alter = 46.
_diagnose = "Bluthochdruck".
```

Die Schreibweise ist eine dBase2Many-PROLOG-Erweiterung. Intern wird ein benannter Wissenswert als normale PROLOG-Klausel gespeichert:

```prolog
d64_knowledge_value(apfel, "Ein Apfel ist gesund").
```

Damit nutzt er dieselben Klauseltabellen, Database-IDs sowie Load/Save/Close-Mechanismen wie andere externe Fakten und Regeln.

## Abgrenzung zu PROLOG-Variablen

- `_` bleibt die anonyme PROLOG-Variable.
- `_Name` bleibt eine normale PROLOG-Variable.
- `_name` ist ein benannter Wissenswert, wenn nach `_` ein Kleinbuchstabe folgt.

## Verwendung

```prolog
_apfel = "Ein Apfel ist gesund".
_farbe = rot.

main :-
    writeln(_apfel),
    X = _farbe,
    writeln(X).
```

Ein Zugriff wird unmittelbar vor dem Goal aufgelöst, das den Wissenswert verwendet. Dadurch bleibt die Reihenfolge bei externen Datenbanken korrekt:

```prolog
main :-
    database_open("patient.pl", DB),
    writeln(_name),
    database_close(DB).
```

entspricht intern sinngemäß:

```prolog
database_open("patient.pl", DB),
d64_knowledge_value(name, K),
writeln(K),
database_close(DB).
```

## Expliziter Zugriff

Zusätzlich steht zur Verfügung:

```prolog
knowledge(Name, Value).
```

Beispiel:

```prolog
?- knowledge(apfel, X).
```

Das ist auch die portable explizite Form für die native interaktive Runtime-Konsole. Die Kurzschreibweise `_name` wird in kompilierten Quelldateien und dort enthaltenen Queries umgesetzt; der native Runtime-REPL-Parser verwendet derzeit für direkte interaktive Abfragen die explizite `knowledge/2`-Form.

## Externe Wissensdatenbanken

Eine Datei kann beispielsweise enthalten:

```prolog
_name = "Max Mustermann".
_alter = 46.
_diagnose = "Bluthochdruck".
_allergie = penicillin.

blutdruck(150, 90).
```

Beim Laden mit `database_open/..` wird jeder Wissenswert derselben Database-ID zugeordnet wie die übrigen Klauseln dieser Datei. `database_close(DB)` entfernt daher auch die benannten Wissenswerte dieser Datenbank wieder aus dem Arbeitsspeicher.

## Speichern

Intern gespeicherte Klauseln vom Typ

```prolog
d64_knowledge_value(name, "Max Mustermann").
```

werden beim `database_save/1` wieder in der benutzerfreundlichen Form geschrieben:

```prolog
_name = "Max Mustermann".
```

Die interne Implementierung wird also nicht in die Wissensdatei geleakt.

## Wissen-Datenbank-Browser

Der Stage-55-Browser erkennt benannte Wissenswerte direkt. Internes `d64_knowledge_value/2` wird ausgeblendet; sichtbar ist beispielsweise:

```text
_name
_apfel
_diagnose
```

Der jeweilige Wert erscheint als Alternative bzw. nächster Entscheidungslevel.

## Beispiele

- `examples/prolog/named_knowledge_values_stage56.pl`
- `examples/prolog_database/patient_named_values_stage56.pl`
- `examples/prolog_database/arzt_named_values_stage56.pl`

## Validierung

- Stage-56-spezifische Tests: 11/11
- gesamte PROLOG-Tests: 96/96
- vollständige Projekttests: 590/590
- interner PE32-Assembler/Linker: OK
- interner PE32+-Assembler/Linker: OK

Eine native Ausführung der erzeugten Windows-EXE wurde in der Entwicklungsumgebung dieser Änderung nicht durchgeführt.
