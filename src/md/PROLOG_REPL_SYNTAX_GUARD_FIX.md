# PROLOG REPL Syntax Guard Fix

## Problem

Die interaktive Eingabe

```prolog
?- X is 2 2 * 5, writeln(X).
```

wurde zuvor als gueltiges Praefix `X is 2` akzeptiert. Die nachfolgenden Tokens
`2 * 5, writeln(X).` blieben ungelesen. Dadurch konnte der Solver faelschlich
`X = 2` melden.

## Korrektur

`__rt_parse_goal_list` prueft nach dem vollstaendigen Ausdruck und einem optionalen
abschliessenden Punkt nun erneut die Eingabe. Nach Whitespace darf nur das
Stringende folgen. Bleibt irgendein Token uebrig, liefert der Parser `INVALID`.
Der REPL gibt daraufhin `syntax_error.` aus und startet den Solver nicht.

Gueltig bleiben z. B.:

```prolog
?- X is 2 + 2 * 5.
?- X is 2 + 2 * 5
?- X is 2 + 2 * 5, writeln(X).
```

Ungueltig sind z. B.:

```prolog
?- X is 2 2 * 5.
?- X is 2 + 3 foo.
?- X = 1. trailing
```

Zusaetzlich muss ein mit `?` begonnenes Query-Praefix jetzt wirklich `?-` sein.

## Erwartetes Verhalten

```text
?- X is 2 2 * 5, writeln(X).
syntax_error.
?-
```

Es darf insbesondere keine Teil-Loesung `X = 2` mehr ausgegeben werden.

## Tests

- Python source parser rejects adjacent arithmetic terms.
- Native REPL assembly contains end-of-input validation.
- `?-` prefix is validated.
- PE32 COFF/link path succeeds.
- PE32+ COFF/link path succeeds.
- Full LISP/PROLOG regression suite: 40 tests OK.
