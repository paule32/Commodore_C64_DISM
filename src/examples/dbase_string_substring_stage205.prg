* Stage 205: $() - Anfangsposition zaehlt ab 1.
STORE "Zeichenstring" TO Text
STORE 8 TO Anfang
STORE 6 TO Anzahl
? $("Zeichenstring", 8, 6)
* string
? $(Text, Anfang)
* string
? $(Text, Anfang, 999)
* string
? $(Text, 14)
* leerer String
? $("aäöß😀Z", 2, 4)
* äöß😀
? !($("klein groß", 7))
* GROß
STORE $(Text, Anfang, Anzahl) TO Ergebnis
? "Teilstring: " + Ergebnis
? Text
* Quelle bleibt erhalten: Zeichenstring
STORE $(Text, Anfang) TO Text
? Text
* string
