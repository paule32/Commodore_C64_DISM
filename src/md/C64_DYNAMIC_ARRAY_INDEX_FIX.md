# C64 dynamic array index fix

## Fehlerbild

Beim Kompilieren der gemeinsamen Grafik-Laufzeit meldete das C-Frontend an
`GfxFloodXLow[index]`:

```text
Konstanter Bezeichner nicht gefunden: index.
```

## Ursache

Die gemeinsame Speicherauflösung versuchte einen Arrayindex zunächst als
Konstantenausdruck auszuwerten. Der Pascal-Codegenerator meldet dabei
`C64PascalError`, der C-Codegenerator hingegen `C64CError`. Abgefangen wurde
nur die Pascal-Fehlerklasse. Ein gültiger lokaler C-Parameter wie `index`
verließ deshalb die Konstantenprüfung als Compilerfehler.

## Korrektur

`_is_constant_expression()` prüft jetzt ohne Ausnahmen, ob ein Ausdruck nur
aus Literalen und bereits bekannten Konstanten besteht. Nur dann wird
`_evaluate_constant()` aufgerufen. Lokale Variablen und Parameter werden direkt
als dynamische Arrayindizes behandelt.

Damit funktionieren insbesondere:

```c
array[index]
array[index] = value;
array[CONST_INDEX]
array[2 + CONST_INDEX]
```

Die Änderung gilt für C64 und Amiga, ohne die Prüfung echter konstanter
Arraygrenzen zu lockern.
