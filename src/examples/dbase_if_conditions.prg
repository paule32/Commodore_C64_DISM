// Stage 103 - dBase IF / ELSE / ENDIF und Verschachtelung
A = 10
B = 25
NAME = "dBase"

IF A = 10
    ? "A ist 10"

    IF B >= 20
        ? "B ist mindestens 20"

        IF NAME = "dBase"
            ? "dBase Bedingung OK"
        ELSE
            ? "anderer Name"
        ENDIF
    ELSE
        ? "B ist kleiner als 20"
    ENDIF
ELSE
    ? "A ist nicht 10"
ENDIF

IF A + 5 < B
    ? "Ausdruecke in Bedingungen funktionieren"
ENDIF
