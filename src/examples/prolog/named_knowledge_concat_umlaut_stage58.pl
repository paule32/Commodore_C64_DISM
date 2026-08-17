% Stage 58: benannte Wissenswerte, String-Verkettung und deutsche Umlaute.

_apfel        = "Ein Apfel ist ".
_apfel_gesund = _apfel + "gesund".
_apfel_essbar = _apfel + "essbar".
_apfel_obst   = _apfel + "Obstsorte".

_äpfel = "sind gesund".

main :-
    writeln(_apfel_gesund),
    writeln(_apfel_essbar),
    writeln(_apfel_obst),
    writeln(_äpfel).
