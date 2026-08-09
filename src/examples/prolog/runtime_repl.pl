parent(john, mary).
parent(mary, susan).
parent(susan, anna).

ancestor(X, Y) :- parent(X, Y).
ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).

main :-
    writeln('Interactive PROLOG runtime'),
    repl.
