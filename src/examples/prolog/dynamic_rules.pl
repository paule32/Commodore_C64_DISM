base(a).
base(b).

main :-
    asserta((dyn(X) :- base(X))),
    assertz(dyn(c)),
    dyn(X),
    writeln(X),
    retract((dyn(Y) :- Body)),
    gc,
    repl.
