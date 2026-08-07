# C64 IndexSelector constructor fix

## Fehler

Beim Absenken eines C-Arrayzugriffs in die gemeinsame AST-Zwischenform wurde
`IndexSelector` mit nur dem Ausdruck erzeugt:

```python
IndexSelector(flat_index)
```

`IndexSelector` erbt jedoch das Feld `position` von `DesignatorSelector` und
besitzt zusätzlich das Feld `expression`. Der gültige Konstruktor lautet daher:

```python
IndexSelector(position, flat_index)
```

## Auswirkung

Der Fehler trat insbesondere beim FloodFill-Ausdruck auf:

```c
GfxFloodXHigh[index] << 8
```

Nach der Array- und Shift-Absenkung wurde der Designator erzeugt, bevor die
Codeerzeugung beginnen konnte. Python meldete deshalb:

```text
IndexSelector.__init__() missing 1 required positional argument: 'expression'
```

## Korrektur

Die Array-Absenkung übergibt nun Quellposition und Indexausdruck. Dadurch bleibt
die Quellzuordnung für Fehlermeldungen erhalten und der Arrayzugriff erreicht
regulär die C64-/Amiga-Codeerzeugung.
