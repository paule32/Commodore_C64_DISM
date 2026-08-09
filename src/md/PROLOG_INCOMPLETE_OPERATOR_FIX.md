# PROLOG REPL: fehlender rechter Operand

## Reproduktion

Die interaktive Eingabe

```prolog
?- X is 2 + 2 -.
```

konnte die native Runtime zum Absturz bringen.

## Ursache

Der Runtime-Präzedenzparser gab beim fehlenden rechten Operanden zwar `INVALID`
aus `__rt_parse_term` zurück, die darüberliegenden Operatorstufen prüften diesen
Wert jedoch nicht überall. Dadurch konnte beispielsweise `__rt_parse_add` einen
binären `-/2`-Term erzeugen, dessen rechter Kindknoten `INVALID` war. Erst der
Solver bzw. Arithmetic-Evaluator dereferenzierte diesen kaputten Term und griff
außerhalb des gültigen Term-Heaps zu.

## Korrektur

`INVALID` wird jetzt durch alle Operatorstufen propagiert:

- unary `+` / `-`
- `*`, `/`, `mod`
- `+`, `-`
- `is`, `=`, `==`, `\\=`, `<`, `=<`, `>`, `>=`
- Konjunktion `,`
- Disjunktion `;`
- Regeloperator `:-`
- Klammerausdrücke und List-Tails

Ein unvollständiger Ausdruck erreicht den Solver nicht mehr.

## Verhalten

```text
?- X is 2 + 2 -.
syntax_error.
?-
```

Ebenso werden zum Beispiel abgewiesen:

```prolog
?- X is 2 +.
?- X is 2 *.
?- X is.
?- X =.
?- X = 1,.
?- X = 1;.
```

## Regression

- 43 Tests bestanden
- 38 Subtests bestanden
- PE32 Assemble/COFF32/Link: OK
- PE32+ Assemble/COFF64/Link: OK
