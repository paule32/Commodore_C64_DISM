% Stage 56 - die Werte existieren nur solange die Akte geladen ist.

main :-
    database_open("patient_named_values_stage56.pl", read_write, record, DB),
    writeln(_name),
    writeln(_alter),
    writeln(_diagnose),
    writeln(_allergie),
    database_save(DB),
    database_close(DB).
