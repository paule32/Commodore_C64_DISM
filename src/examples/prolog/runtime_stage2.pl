edge(a, b).
edge(b, c).
edge(c, d).

path(X, Y) :- edge(X, Y).
path(X, Y) :- edge(X, Z), path(Z, Y).

choose(X) :- (X = one ; X = two ; X = three).

calc(X) :- X is -(3 + 4) * 2.

main :-
    asserta((dynamic_path(X, Y) :- path(X, Y))),
    assertz(edge(d, e)),
    calc(N),
    writeln(N),
    gc,
    repl.
