% Beispiel 2: Regelwissen und Patientenakte getrennt laden.
% Normale Abfragen duerfen Wissen + Patientendaten kombinieren.
% Die Aenderung wird dagegen explizit der Patienten-Database-ID zugeordnet.

main :-
    database_open("medizin_wissen.pl", read_only, knowledge, Wissen),
    database_open("patient_4711.pl", read_write, record, Patient),

    kontrolle_empfohlen(4711),
    writeln("Kontrolle empfohlen"),

    with_database(
        Patient,
        assert(empfehlung(4711, kontrolle))
    ),

    database_retract(Patient, blutdruck(4711, 150, 90)),
    database_assert(Patient, blutdruck(4711, 145, 85)),

    database_save(Patient),
    database_close(Patient),
    database_close(Wissen).
