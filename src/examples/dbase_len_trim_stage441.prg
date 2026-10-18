// Stage 441: LEN, LTRIM, RTRIM, TRIM - Windows PE32 / PE32+
#define WORT "  Text durch Makro  "

// Zeichenkette, Memory-Variable und Makro-String
? LEN("Ein String")
STORE "   Ein dBASE-Text   " TO Text
? LEN(Text)
? LEN(WORT)

// Fuehrende Leerzeichen (LTRIM)
? "[" + LTRIM(Text) + "]"
// Abschliessende Leerzeichen sowie \t, \r, \n, \b (RTRIM)
? "[" + RTRIM(Text) + "]"
// Fuehrende und abschliessende Leer-/Steuerzeichen (TRIM)
? "[" + TRIM(Text) + "]"

// Ergebnis von TRIM ist ein String, LEN liefert eine Zahl.
STORE TRIM(Text) TO Ergebnis
STORE LEN(Ergebnis) TO Laenge
? "[" + Ergebnis + "]"
? Laenge

// Eine dBASE FUNCTION endet mit RETURN <Ausdruck>.
FUNCTION BeispielText()
    RETURN "   Funktionswert   "
? LEN(BeispielText())
? TRIM(BeispielText())
? LEN(TRIM(BeispielText()))
