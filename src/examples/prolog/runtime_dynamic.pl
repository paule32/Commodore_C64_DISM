main :-
    assert(parent(tom, lisa)),
    assert(parent(lisa, emma)),
    parent(tom, X),
    writeln(X),
    retract(parent(tom, X)),
    repl.
