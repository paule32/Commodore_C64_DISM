# C64-BASIC-Compiler: erweiterte Komponenten

Diese Erweiterung ergänzt die zuvor noch fehlenden Bestandteile des eigenen
C64-BASIC-Compilers. Der vorhandene Arbeitsablauf bleibt unverändert:

```text
BASIC -> MOS-6510-Assembler -> PRG -> VICE
```

## Numerische Typen

### Fließkomma

Normale numerische Variablen verwenden das 5-Byte-CBM-Fließkommaformat. Der
erzeugte 6510-Code bindet die arithmetischen Routinen des C64-BASIC-ROMs ein.
Unterstützt werden Fließkommakonstanten, Variablen, Arrayelemente und die
Operatoren `+`, `-`, `*`, `/` sowie Vergleiche.

```basic
10 X=1.5
20 Y=2.25
30 Z=X*Y+0.5
40 PRINT Z
```

### Ganzzahlen

Variablen und Arrays mit `%`-Suffix werden als 16-Bit-Ganzzahlen gespeichert.

```basic
10 I%=42
20 DIM A%(10)
30 A%(3)=I%
```

## Zeichenketten

Stringvariablen enden auf `$` und besitzen pro Variable beziehungsweise
Arrayelement einen festen Puffer von 255 Nutzbytes. Unterstützt werden
Zuweisung, Verkettung, Vergleich, Ausgabe, `CHR$`, `STR$`, `LEN`, `VAL` und
`ASC`.

```basic
10 A$="HELLO"
20 B$=A$+" C64"
30 PRINT B$
```

Die String-Laufzeit behandelt 16-Bit-Zeiger einschließlich Seitenwechseln.

## Arrays

`DIM` unterstützt ein- und zweidimensionale Arrays:

```basic
10 DIM F(20),I%(10,10),S$(5)
```

- normale numerische Elemente: 5 Bytes
- `%`-Elemente: 2 Bytes
- `$`-Elemente: 256 Bytes
- Untergrenzen sind 0, die DIM-Werte sind inklusive Obergrenzen
- nicht deklarierte Arrays werden kompatibel mit `0..10` automatisch angelegt
- statische Speicher- und Indexprüfungen verhindern Überläufe

## INPUT und GET

Von Tastatur oder aktuellem Eingabekanal:

```basic
10 INPUT "NAME";N$
20 INPUT "WERT";A
30 GET K$
40 GET C%
```

Kommagetrennte Felder können mehreren Variablen zugewiesen werden.

## DATA, READ und RESTORE

```basic
10 DATA 3.14,"TEXT",7
20 READ A,B$,I%
30 RESTORE 10
40 READ C
```

`RESTORE` ohne Argument setzt auf den Beginn des DATA-Bereichs zurück;
`RESTORE <Zeile>` setzt auf die erste DATA-Anweisung dieser Zeile.

## Datei- und Gerätekanäle

Unterstützt werden:

```basic
OPEN lfn,device,secondary,"name"
CLOSE lfn
CMD lfn
PRINT#lfn,...
INPUT#lfn,...
GET#lfn,...
```

Beispiel für Laufwerk 8:

```basic
10 OPEN 2,8,2,"TEST,S,W"
20 PRINT#2,"VALUE";12.5
30 CLOSE 2
40 OPEN 2,8,2,"TEST,S,R"
50 INPUT#2,A$,B
60 CLOSE 2
```

Die Implementierung verwendet die KERNAL-Sprungtabelle und stellt nach
kanalgebundenen Operationen den Standardkanal wieder her.

## Unterstützte Funktionen

```text
ABS  INT  SGN  PEEK  LEN  VAL  ASC  CHR$  STR$
```

## Beispiel

```text
examples/c64basic/basic_extended_demo.bas
examples/c64basic/basic_extended_demo.generated.asm
examples/c64basic/basic_extended_demo.prg
```

## Bewusste Grenzen dieses Standes

Die zuvor ausdrücklich fehlenden sechs Komponenten sind implementiert. Der
Compiler beansprucht dennoch noch keine vollständige Commodore-BASIC-V2-
Kompatibilität. Insbesondere fehlen momentan unter anderem:

- trigonometrische Funktionen und `SQR`, `LOG`, `EXP`, `RND`
- `LEFT$`, `RIGHT$`, `MID$`
- `ON ... GOTO/GOSUB`
- `DEF FN`
- BASIC-Befehle wie `LOAD`, `SAVE`, `VERIFY` und `LIST`
- dynamische String-Heap-Verwaltung; Strings besitzen statische 255-Byte-Puffer

Diese Einschränkungen betreffen nicht die in diesem Erweiterungsschritt
geforderten Fließkomma-, String-, Array-, Eingabe-, DATA- und Kanalbestandteile.
