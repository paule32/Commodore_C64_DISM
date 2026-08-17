% Beispiel 1: Eine Patientenakte laden, abfragen, ergaenzen, speichern
% und danach wieder vollstaendig aus dem Runtime-Wissensbestand entladen.

main :-
    database_open("patient_4711.pl", read_write, record, DB),

    name(4711, Name),
    writeln(Name),

    blutdruck(4711, Sys, Dia),
    writeln(Sys),
    writeln(Dia),

    database_assert(DB, untersuchung(4711, kontrolle)),
    database_assert(DB, notiz(4711, wiedervorstellung)),

    database_save(DB),
    database_close(DB).
