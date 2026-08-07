# Pascal-Units: Parser, PUI und Zielmodul

## Ursprünglicher Fehler

Beim direkten Kompilieren einer Unit wurde immer die Grammar-Startregel für ein
Pascal-Programm verwendet. Deshalb entstand bei:

```pascal
unit System.Graphics;
```

die Meldung:

```text
missing 'PROGRAM' at 'unit'
```

## Quellformerkennung

`compile_pascal_to_assembly()` erkennt vor dem ANTLR-Programmparser die oberste
Pascal-Quellform:

- `program`
- `unit`
- `library`

Eine Unit wird nicht mehr als `PROGRAM` geparst.

## Direkte Unit-Kompilierung

Bei einer Unit werden:

1. `UNIT`, `INTERFACE` und `IMPLEMENTATION` getrennt,
2. die PUI-Datei erzeugt,
3. zielabhängige ASM-Implementierungen aus der PUI ermittelt,
4. ein getrenntes `.generated.amiga.asm`-Unitmodul geschrieben,
5. kein ADF oder PRG erzwungen.

Für `System.Graphics.pas` entstehen beim Amiga-Ziel:

```text
System.Graphics.pui
System.Graphics.generated.amiga.asm
```

## Verwendung durch andere Programme

Bei:

```pascal
uses System.Graphics;
```

importiert der Compiler aus der PUI:

- Konstanten und Typen,
- Prozeduren und Funktionen,
- Parameter und Rückgabetypen,
- externe Symbolnamen,
- die Amiga-Implementierungsdatei `Graphics.amiga.asm`.

Die Routinen werden als normale externe 68000-Unterprogramme aufgerufen und das
ASM-Modul wird vor dem Assemblieren statisch mit dem Programmquelltext
zusammengeführt. Es gibt keine Graphics-Intrinsics.
