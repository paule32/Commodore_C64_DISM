# Pascal OOP / TRY-FINALLY Fix

Diese Erweiterung behebt die Kombination aus Klassenmethoden-Implementierungen,
spaeten globalen VAR-Abschnitten, Konstruktor-Aufrufen und TRY-Bloecken.

Unterstuetzt ist jetzt insbesondere:

```pascal
obj := TObject.Create;
try
    WriteLn('work');
finally
    obj.Free;
end;
```

## Deklarationsreihenfolge

Der alte generierte Parser verlangte alle CONST/TYPE/VAR-Abschnitte vor der
ersten `TClass.Method`-Implementierung. Eine Kompatibilitaetsschicht verschiebt
nur den Parsertext spaeter globaler Deklarationsabschnitte. Lokale VAR-Abschnitte
in Methoden bleiben lokal. Die `.g4`-Quelle wurde parallel auf eine gemischte
Deklarations-/Implementierungsfolge erweitert.

## TRY / FINALLY / EXCEPT

`TryFinallyStatement` und `TryExceptStatement` sind eigene AST-Knoten. Fuer die
bereits vorhandenen generierten ANTLR-Dateien werden TRY-Bloecke zeilentreu in
interne Marker-Bloecke umgeschrieben und im AstBuilder wieder zusammengesetzt.
Nach einer Neugenerierung der Parser werden die neuen nativen Grammar-Regeln
verwendet.

`finally` wird auf dem normalen Ausfuehrungspfad ausgefuehrt und vor BREAK oder
CONTINUE aus einem geschuetzten Block eingefuegt.

`except` wird bereits als eigener Handler-Codeblock erzeugt. Ein echter
Exception-Transport (`raise`, Runtime-Unwind) ist noch eine getrennte
Ausbaustufe; ohne geworfene Exception wird der Handler korrekt uebersprungen.

## Constructor / Free

Das aktuelle Klassenmodell besitzt noch statischen Objektspeicher. Deshalb wird

```pascal
obj := TObject.Create;
```

als Konstruktion direkt im Speicher von `obj` umgesetzt. Parameterlose
Konstruktoren funktionieren mit und ohne `()`.

Solange keine explizite Methode `Free` deklariert ist, wird

```pascal
obj.Free;
```

als Sprachhelfer behandelt und ruft den geerbten bzw. eigenen Destruktor
`Destroy` auf. Eine echte Heap-Allokation/Freigabe ist weiterhin fuer das
spaetere Class-Reference-Modell vorgesehen.
