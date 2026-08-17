% ----------------------------------------------------------------------------
% Apfel-Wissens-Datanbank für Windows PE32 / PE32+
% (c) Copyright 2026 by Jens Kallup - paule32
%  Alle Rechte vorbehalten.
% ----------------------------------------------------------------------------
parent(john, mary).
parent(mary, susan).
parent(susan, anna).

_error_double_facts = "doppelte Aussagen nicht erwünscht".

_apfel        = "Ein Apfel ist: ".
_apfel_gesund = _apfel + "gesund".
_apfel_essbar = _apfel + "essbar".
_apfel_obst   = _apfel + "Obstsorte".

_äpfel        = "Äpfel sind gesund".

% ----------------------------------------------------------------------------
% Apfel ist gesund ...
% ----------------------------------------------------------------------------
apfel(gesund, X, Y) :-
    ( X == Y ; X == gesund ; Y == gesund ), !,
    writeln(_error_double_facts), fail.
% ----------------------------------------------------------------------------
apfel(gesund, X, Y) :- writeln(_apfel_gesund), apfel(X, Y).
apfel(gesund, X)    :- writeln(_apfel_gesund), apfel(X).
apfel(gesund)       :- writeln(_apfel_gesund).

% ----------------------------------------------------------------------------
% Apfel ist essbar ...
% ----------------------------------------------------------------------------
apfel(essbar, X, Y) :-
    ( X == Y ; X == essbar ; Y == essbar ), !,
    writeln(_error_double_facts), fail.
% ----------------------------------------------------------------------------
apfel(essbar, X, Y) :- writeln(_apfel_gesund), apfel(X, Y).
apfel(essbar, X)    :- writeln(_apfel_essbar), apfel(X).
apfel(essbar)       :- writeln(_apfel_essbar).

% ----------------------------------------------------------------------------
% Apfel ist Obst ...
% ----------------------------------------------------------------------------
apfel(obst)         :- writeln(_apfel_obst).

% ----------------------------------------------------------------------------
ancestor(X, Y) :- parent(X, Y).
ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).

% ----------------------------------------------------------------------------
% start/entry point:
% ----------------------------------------------------------------------------
?- ancestor(john, Who).
?- apfel(essbar, essbar, obst).
?- repl.
