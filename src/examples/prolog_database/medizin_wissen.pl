% Externe KNOWLEDGE-Datenbank: allgemeine Regeln, keine Patientendaten.

hoher_blutdruck(Patient) :-
    blutdruck(Patient, Systolisch, _),
    Systolisch > 140.

hoher_blutzucker(Patient) :-
    blutzucker(Patient, Wert),
    Wert > 126.

kontrolle_empfohlen(Patient) :-
    hoher_blutdruck(Patient).

kontrolle_empfohlen(Patient) :-
    hoher_blutzucker(Patient).
