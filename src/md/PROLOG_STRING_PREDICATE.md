# PROLOG string/1

`string/1` is a pure type predicate.

It succeeds only if its argument dereferences to a runtime `NODE_STRING` value.
It does not bind unbound variables and does not treat atoms or numbers as strings.

Examples:

```prolog
?- string("Hallo").
true.

?- X = "Hallo", string(X).
X = "Hallo".

?- string(X).
false.

?- string('Hallo').
false.

?- string(123).
false.

?- string(1.25).
false.
```

Double-quoted values are strings. Single-quoted values remain atoms.
