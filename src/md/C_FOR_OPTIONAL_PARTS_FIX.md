# C-FOR mit optionalen Bestandteilen

## Fehler

Der C64-Codegenerator wies die gueltige C-Endlosschleife

```c
for (;;) {
    /* ... */
}
```

mit folgender Meldung ab:

```text
FOR erwartet Initialisierung, Vergleich und ++/-- Schritt.
```

Die Grammar war bereits korrekt und erlaubte alle drei optionalen Teile. Die
AST-Erzeugung versuchte jedoch jede C-FOR-Schleife in die eingeschraenkte
Pascal-FOR-Struktur mit Laufvariable und Endwert umzuwandeln.

## Korrektur

Der C-Compiler verwendet nun einen eigenen allgemeinen `_CForStatement`-Knoten:

- `initializers`: null, eine Zuweisung oder Deklarationsinitialisierungen
- `condition`: optional; fehlt sie, gilt die Schleife als wahr
- `update`: optional
- `body`: Schleifenkoerper

Unterstuetzt werden damit unter anderem:

```c
for (;;) { }
for (; i < 10;) { i++; }
for (i = 0;; i++) { if (i == 10) break; }
for (int i = 0; i < 10; i++) { }
```

## Sprungziele

- `break` springt zum Ende der FOR-Schleife.
- `continue` springt zuerst zum Update-Teil.
- Fehlt der Update-Teil, folgt von dort direkt der Sprung zur Bedingung.
- Fehlt die Bedingung, wird kein Test erzeugt; die Schleife endet nur ueber
  `break`, `return` oder einen anderen expliziten Sprung.

Die Korrektur liegt im gemeinsamen C-Frontend und gilt deshalb fuer C64 und
Amiga. Die vorhandene `runtime/graphics/common/graphics_api.c` kann unveraendert
`for (;;)` verwenden.
