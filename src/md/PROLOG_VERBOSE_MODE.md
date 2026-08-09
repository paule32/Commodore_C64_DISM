# PROLOG Verbose / Debug-Ausgabemodus

Der PROLOG-Compiler besitzt einen Runtime-Schalter `verbose` mit bewusst invertierter Ausgabesemantik:

- `verbose = false` (Standard): der interaktive Top-Level zeigt automatische Lösungen, z. B. `X = 14.` oder `true.`.
- `verbose = true`: automatische Top-Level-Lösungen werden unterdrückt. Explizite Ausgaben über `write/1`, `writeln/1` und `nl/0` bleiben sichtbar.
- Fehlschläge (`false.`) bleiben sichtbar.

## GUI

PROLOG-Editoren zeigen im Quell- und ASM-Panel eine Checkbox **Verbose**. Eine Änderung invalidiert den erzeugten ASM-/EXE-Stand und erfordert ein erneutes Compile/Assemble.

## Runtime

Der Schalter kann auch aus PROLOG geändert werden:

```prolog
?- verbose(true).
?- X is 2 + 3 * 4.
?- X is 2 + 3 * 4, writeln(X).
14
?- verbose(false).
true.
?- X is 2 + 3 * 4.
X = 14.
```

`verbose(true)` unterdrückt nur `__rt_emit_solution`; `write/writeln/nl` laufen unverändert durch die normale Ausgabe-Runtime.

## CLI

`--verbose` und `--prolog-verbose` aktivieren den PROLOG-Verbose-Modus beim Kompilieren.

## Targets

Geprüft für:

- Windows PE32 / COFF32
- Windows PE32+ / AMD64 COFF64
- Console und der gemeinsame Runtime-Ausgabepfad
