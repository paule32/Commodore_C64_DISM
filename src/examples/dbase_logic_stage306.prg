** Stage 306: Logische dBase-Operatoren, Rangfolge und Klammern
A = 5
B = 9
C = 0
IF A > 0 .AND. B < 10
    ? "AND: OK"
ENDIF
IF .NOT. (A < 0 .OR. B >= 10)
    ? "NOT/OR: OK"
ENDIF
IF (A > 0) .XOR. (C <> 0)
    ? "XOR: OK"
ENDIF
IF (A > 0 .AND. B < 10) .OR. C > 0
    ? "KLAMMERN: OK"
ENDIF
ERGEBNIS = (A > 0 .AND. B < 10)
? ERGEBNIS
