head([H|_], H).

append([], X, X).
append([H|T], X, [H|R]) :- append(T, X, R).

?- head([a,b,c], X).
?- append([a,b], [c,d], X).
