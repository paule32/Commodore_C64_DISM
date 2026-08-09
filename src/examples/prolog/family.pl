% Rekursive PROLOG-Demo fuer Windows PE32 / PE32+
parent(john, mary).
parent(mary, susan).
parent(susan, anna).

ancestor(X, Y) :- parent(X, Y).
ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).

?- ancestor(john, Who).
