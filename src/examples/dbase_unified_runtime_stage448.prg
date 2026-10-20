** Stage 448: Gemeinsame Windows Runtime fuer Konsole + Zeichenpruefung
SET FORMAT TO CONSOLE
STORE "ä" TO Letter
? "Klein: " + ISLOWER(Letter)
? "Gross: " + ISUPPER(Letter)

FUNCTION CheckLower(value)
    RETURN ISLOWER(value)

FUNCTION CheckUpper(value)
    RETURN ISUPPER(value)

? CheckLower(Letter)
? CheckUpper(Letter)
