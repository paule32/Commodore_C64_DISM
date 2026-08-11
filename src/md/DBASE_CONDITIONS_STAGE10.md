# dBase Bedingungen – Stage 10

Diese Stufe erweitert den dBase-Compiler fuer Windows PE32 und PE32+ um echte,
verschachtelbare Laufzeitbedingungen.

## Member-Ende

Explizite Endmarker fuer Member sind nicht mehr Bestandteil der Sprache.

Eine Procedure endet ausschliesslich mit einem nackten `RETURN`:

```dbase
procedure show(value)
    ? value
    return
```

Eine Function endet ausschliesslich mit `RETURN <expr>`:

```dbase
function add(a, b)
    return a + b
```

`ENDPROC`, `ENDPROCEDURE`, `ENDFUNC` und `ENDFUNCTION` werden abgewiesen.

## IF

```dbase
IF X >= 10
    ? "X ist mindestens 10"
ENDIF
```

## IF / ELSE

```dbase
IF X == 10
    ? "genau 10"
ELSE
    ? "nicht 10"
ENDIF
```

## IF / ELSEIF / ELSE

```dbase
IF X < 0
    ? "negativ"
ELSEIF X == 0
    ? "null"
ELSEIF X < 10
    ? "kleiner 10"
ELSE
    ? "mindestens 10"
ENDIF
```

Bloecke duerfen beliebig ineinander verschachtelt werden.

## Vergleichsoperatoren

Unterstuetzt werden:

- `<`
- `<=`
- `==`
- `>`
- `>=`
- `<>` – ungleich
- `#` – ebenfalls ungleich, entsprechend `!=`

Ein einzelnes `=` bleibt der Zuweisungsoperator und ist in einer IF-Bedingung
kein Gleichheitsvergleich.

## Werte

Beide Seiten des Vergleichs koennen normale dBase-Ausdruecke sein. Damit sind
unter anderem erlaubt:

```dbase
IF 2 + 3 * 4 == 14
IF 0x10 >= 15
IF 2.5 < 3.0
IF "abc" < "abd"
IF 'A' # 'B'
IF variable >= 5
IF foo() == 10
```

Zahl, Hex und Float werden numerisch verglichen. String und Char werden
lexikographisch verglichen. Ein Vergleich Zahl gegen String/Char wird als
Typfehler abgewiesen.

## Native Codeerzeugung

Numerische Vergleiche werden im erzeugten IA-32/AMD64-Code ueber x87
`FUCOMIP` und bedingte Spruenge umgesetzt. Textvergleiche verwenden `memcmp`
und bei gleichem Prefix zusaetzlich die Textlaenge.

IF-Code wird fuer PE32 und PE32+ mit dem internen Assembler/Linker getestet.
