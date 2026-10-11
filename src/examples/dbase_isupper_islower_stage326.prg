** Stage 326: dBase-Zeichenklassifizierung (Windows-1252, Bool = 1/0)
STORE 'A' TO Letter
? ISUPPER(Letter)                 ** 1
? ISLOWER(Letter)                 ** 0
? ISUPPER('Ä')                  ** 1
? ISLOWER('ä')                  ** 1
? ISLOWER('ß')                  ** 1
? ISUPPER('7')                  ** 0
? ISUPPER("AB")                 ** 0, kein Einzelzeichen

FUNCTION CheckUpper(value)
    RETURN ISUPPER(value)
FUNCTION CheckLower(value)
    RETURN ISLOWER(value)

IF CheckUpper('Z') .AND. CheckLower('z')
    ? "Beide Zeichentests erfolgreich"
ENDIF
