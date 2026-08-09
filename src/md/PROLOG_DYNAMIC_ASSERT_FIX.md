# PROLOG Dynamic Assert/Lookup Fix

## Reproduktionsfall

```prolog
main :-
    assert(parent(tom, lisa)),
    assert(parent(lisa, emma)),
    parent(tom, X),
    writeln(X),
    retract(parent(tom, X)),
    repl.
```

Erwartetes Verhalten vor dem REPL-Prompt:

```text
lisa
?- 
```

## Ursache

`__rt_dyn_clone_struct` baute mit `__rt_make_struct` den transienten Compound-Term korrekt auf,
fiel danach jedoch direkt in `__rt_dyn_clone_fail`. Dadurch wurde `EAX` auf `INVALID` gesetzt.
Jeder dynamische Compound-Term (z. B. `parent(tom,lisa)`) wurde beim Lookup daher verworfen.

## Korrektur

Nach erfolgreichem `__rt_make_struct` springt die Runtime nun explizit zu
`__rt_dyn_clone_done`. Das neu erzeugte Termhandle bleibt in `EAX` erhalten.

Die Korrektur betrifft damit gleichzeitig:

- Lookup von mit `assert/1`, `asserta/1`, `assertz/1` gespeicherten Compound-Fakten
- dynamische Regeln `(Head :- Body)`
- `retract/1` auf Compound-Termen
- Variablenbindungen aus dynamischen Fakten/Regeln

## Regression

Der exakte Reproduktionsfall wird für PE32 und PE32+ kompiliert, intern zu COFF assembliert
und zu einer Windows-EXE gelinkt. Zusätzlich wird geprüft, dass der STRUCT-Erfolgszweig vor
`__rt_dyn_clone_fail` ein `jmp __rt_dyn_clone_done` enthält.
