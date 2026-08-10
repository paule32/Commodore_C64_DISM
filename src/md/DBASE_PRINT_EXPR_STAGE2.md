# dBase Compiler – Ausbaustufe 2: `?` / `??` und Ausdrücke

## Zielsysteme

Der dBase-Compiler erzeugt ausschließlich Windows-Code für:

- `pe32` – IA-32 / Windows PE32
- `pe64` – AMD64 / Windows PE32+

## Ausgabeanweisungen

```dbase
? <expr>
?? <expr>
```

`?` gibt den ausgewerteten Ausdruck auf der Windows-Konsole aus und fügt
anschließend `CR/LF` (`\r\n`) an.

`??` gibt den ausgewerteten Ausdruck aus, fügt aber **kein** NewLine an. Mehrere
`??`-Anweisungen schreiben deshalb direkt hintereinander.

Beispiel:

```dbase
?? "Summe: "
? 1 + 2 + 3
?? "Text"
?? " direkt"
? " dahinter"
```

Erzeugte Ausgabe:

```text
Summe: 6
Text direkt dahinter
```

## Ausdrücke

Aktuell ausführbar:

- Integer- und Fließkommazahlen
- Strings in `"..."`
- Strings in `'...'`
- Klammern
- unäres `+` und `-`
- `+`, `-`, `*`, `/`
- übliche Operatorpriorität: `*` und `/` vor `+` und `-`
- `String + String` als Konkatenation

Beispiele:

```dbase
? 1 + 2 + 3
? 1 + 2 * 3
? (1 + 2) * 3
? 10 / 4
? "Hallo " + 'dBase'
? "Text ' text ' "
```

## Kommentare in Ausdrücken

Die Kommentarstufe bleibt vollständig erhalten. Ein C-artiger Blockkommentar
kann auch mitten im Ausdruck stehen und über mehrere physische Zeilen laufen:

```dbase
? 2 + /* Kommentar
über mehrere Zeilen */ 3
```

Ergebnis: `5` plus NewLine.

`//`, `**` und `&&` beenden dagegen den Rest der jeweiligen Quellzeile.

## Vorbereitung für Variablen und Funktionen

Der Parser besitzt bereits AST-Knoten für Bezeichner und Funktionsaufrufe:

```dbase
? variable + 3
? 2 + variable + 3
? test() + "text"
```

Diese Formen werden syntaktisch korrekt geparst. Die semantische Auflösung von
Variablen und das Ausführen von Funktionen folgt in der nächsten Ausbaustufe.
Bis dahin meldet der Compiler dafür bewusst einen präzisen Compilerfehler mit
Original-Zeile und -Spalte statt den Ausdruck falsch auszuwerten.

## Typregeln

`+` ist überladen:

```dbase
? 1 + 2             // Zahl + Zahl -> 3
? "a" + "b"         // String + String -> ab
```

Eine Mischung ist in dieser Stufe ein Typfehler:

```dbase
? 2 + "Text"
```

Damit kann die spätere Variablen-/Funktionsstufe dieselben AST- und Typregeln
weiterverwenden.
