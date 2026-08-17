% Stage 55: kleine Wissen-Datenbank für den GUI-Browser.
% Der doppelte Fakt wird im Browser nur einmal als Alternative angezeigt.

apfel(gesund).
apfel(gesund).
apfel(rot).
apfel(gruen).

obst(apfel, gesund).
obst(birne, gesund).
obst(banane, gelb).

% Regel: kann ebenfalls über den Browser geprüft werden.
gesundes_obst(Name) :- obst(Name, gesund).

% Mehr als zehn Alternativen: im Alternativdialog erscheint das Suchfeld.
farbe(rot).
farbe(gruen).
farbe(gelb).
farbe(blau).
farbe(weiss).
farbe(schwarz).
farbe(braun).
farbe(orange).
farbe(violett).
farbe(rosa).
farbe(grau).
farbe(tuerkis).
