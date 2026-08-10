# dBase PROCEDURE / FUNCTION – Stage 7

Dieser Stand erweitert den vorhandenen dBase-Compiler fuer Windows PE32 und
Windows PE32+ um native Member (`PROCEDURE` und `FUNCTION`). Die Qt5-GUI aus
Stage 5/6 bleibt unveraendert erhalten.

## PROCEDURE

Eine Procedure liefert keinen Wert:

```dbase
procedure show(a, b)
    ? "Summe = " + (a + b)
    return

show(2, 3)
```

Erlaubt sind:

```dbase
return
endproc
endprocedure
```

`return` darf bei einer Procedure **keinen Ausdruck** besitzen. Diese Formen
sind Compilerfehler:

```dbase
return 123
return "foo"
return foo()
```

Eine Procedure kann auch ohne `return` mit `ENDPROC`/`ENDPROCEDURE` beendet
werden.

## FUNCTION

Eine Function liefert einen Wert:

```dbase
function foo(a, b)
    return a + b

? foo(2, 3)
```

`RETURN` ohne Ausdruck ist bei einer Function ein Compilerfehler. Eine Function
ohne Rueckgabewert ist ebenfalls ein Compilerfehler.

Rueckgabewerte koennen unter anderem sein:

```dbase
return 123
return 0xFF
return 'A'
return "foo"
return variable
return foo()
return a + b
return "Wert=" + a
```

## Beliebig viele Parameter

Der Parser und der interne dBase-Member-ABI setzen keine feste Obergrenze fuer
die Parameterzahl. Beispiel:

```dbase
function sum6(a,b,c,d,e,f)
    return a+b+c+d+e+f

? sum6(1,2,3,4,5,6)
```

Die Tests enthalten zusaetzlich einen Aufruf mit 20 Parametern.

## Typen und Spezialisierung

Da dBase keine Typangaben in der Parameterliste verlangt, wird fuer jede
verwendete Parameter-Typkombination eine passende native Member-Instanz
erzeugt. Dadurch kann dieselbe Function verschiedene Typen zurueckgeben:

```dbase
function identity(value)
    return value

? identity(123)
? identity("text")
? identity('A')
```

Der Compiler erzeugt beispielsweise:

```asm
__dbase_function_identity__number:
__dbase_function_identity__string:
__dbase_function_identity__char:
```

Die Parameter und Resultate werden in internen Value-Slots gespeichert. Ein
Slot besitzt Typ, 64-Bit-Zahl, Textzeiger und Textlaenge. Dadurch ist der
Member-ABI fuer Zahl, String und Char identisch.

## Verschachtelte Aufrufe

Verschachtelte Aufrufe werden ueber eigene Call-Site-Slots abgesichert:

```dbase
function add(a,b)
    return a+b

? add(1, add(2,3))
```

Ergebnis: `6`.

## String-Rueckgaben

Dynamische String-Rueckgaben werden ebenfalls unterstuetzt:

```dbase
function label(value)
    return "Wert=" + value

? label(14)
```

Hier verwendet der generierte Code `malloc` und `memcpy`, um den dynamischen
Rueckgabe-String aufzubauen. Reine `?`/`??`-Konkatenationen werden weiterhin
direkt in die Qt5-Ausgabe gestreamt und benoetigen keine Zwischenallokation.

## Member-Ende

Diese Schreibweise ist direkt gueltig:

```dbase
function foo(a,b)
    return a+b
? foo(2,3)
```

Ein zusaetzliches `ENDFUNC` nach `RETURN` wird ebenfalls akzeptiert. Entsprechend
gilt dies fuer `RETURN` + `ENDPROC`.

## Native Ziele

Der generierte Code wird fuer beide Ziele getestet:

- Windows PE32 / IA-32
- Windows PE32+ / AMD64

Die erzeugte Anwendung bleibt eine Windows-GUI-Anwendung und verwendet weiterhin
`d64qt5.dll` fuer die Tabs `Konsole` und `DEBUG`.

## Aktuelle Grenze

Direkte oder gegenseitige Rekursion von dBase-Membern wird in dieser Stufe
bewusst mit einem Compilerfehler abgewiesen. Die Parameterzahl ist davon
unabhaengig und nicht kuenstlich begrenzt.
