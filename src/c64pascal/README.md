# C64 Pascal

Die Pipeline besteht aus zwei getrennten Stufen:

1. `C64PascalLexer.g4` und `C64PascalParser.g4` parsen Pascal mit ANTLR 4.13.2.
2. `compiler.py` erzeugt lesbaren MOS-6510-Assembler. Der in
   `d64_dism(5).py` integrierte Assembler erzeugt daraus das C64-PRG.

## Installation

```powershell
py -m pip install antlr4-python3-runtime==4.13.2
```

Der Ordner `c64pascal` muss neben `d64_dism(5).py` liegen.

## Aktueller Sprachumfang

- `program`, `const`, `var`, `begin` und `end`
- `Integer` (16 Bit), `Byte`, `Char`, `Boolean`
- benannte skalare Typaliase
- Aufzählungstypen mit automatisch vergebenen Werten ab `0`
- Records mit verschachtelbaren Feldern und festem Speicherlayout
- statische Arrays mit frei wählbarer Unter- und Obergrenze
- Arrays aus Skalaren, Enums, Records und statischen Klassen
- statische Klassen mit Feldern, einfacher Vererbung, Konstruktoren,
  Destruktoren, Prozedurmethoden und Funktionsmethoden
- `Self`, implizite Feldzugriffe, Methodenparameter und lokale
  Methodenvariablen
- Zuweisungen und Konstantenausdrücke
- `+`, `-`, `*`, `div`, `mod`, `and`, `or`, `xor`, `not`
- `=`, `<>`, `<`, `<=`, `>`, `>=`
- `if/then/else`, `while/do`, `repeat/until`, `for/to/downto`
- `break`, `continue`
- `Write`, `WriteLn`, `ClrScr`, `Poke`, `Inc`, `Dec`, `Halt`
- `Peek`, `Chr`, `Ord`, `Lo`, `Hi`
- Dezimalzahlen sowie C64-typische Hex- (`$`) und Binärliterale (`%`)

`DIV` und `MOD` arbeiten weiterhin vorzeichenlos. Klasseninstanzen werden auf
dem C64 statisch im Programm reserviert; `Create` initialisiert deshalb ein
bereits vorhandenes Objekt und fordert noch keinen Heap-Speicher an. Dynamische
Arrays, Klassenzeiger, virtuelle Methoden, Overloads, `inherited`, Properties,
allgemeine benutzerdefinierte Prozeduren/Funktionen und Units sind noch nicht
enthalten. `const`- und `var`-Methodenparameter werden syntaktisch akzeptiert,
in dieser Stufe aber als Wertparameter übergeben.

## Beispiel für zusammengesetzte Typen

```pascal
program AdvancedTypes;

type
  TColor = (Red, Green, Blue);

  TPoint = record
    X, Y: Integer;
    Color: TColor;
  end;

  TPoints = array[1..3] of TPoint;

  TCounter = class
  private
    FValue: Integer;
  public
    constructor Create(AValue: Integer);
    procedure Inc;
    function GetValue: Integer;
  end;

var
  Point: TPoint;
  Points: TPoints;
  Counter: TCounter;

constructor TCounter.Create(AValue: Integer);
begin
  FValue := AValue;
end;

procedure TCounter.Inc;
begin
  FValue := FValue + 1;
end;

function TCounter.GetValue: Integer;
begin
  Result := FValue;
end;

begin
  Point.X := 10;
  Point.Color := Green;
  Points[1].X := Point.X;
  Points[1].Color := Point.Color;
  Counter.Create(4);
  Counter.Inc;
  WriteLn(Counter.GetValue());
end.
```

Ein variabler Arrayindex wird zur Laufzeit geprüft. Ein konstanter Index
außerhalb des deklarierten Bereichs führt bereits beim Übersetzen zu einem
Fehler. Ein einzelner Record wird feldweise kopiert; eine Zuweisung des gesamten
Records oder Arrays ist noch nicht implementiert.

## Parser neu erzeugen

```powershell
py c64pascal\generate_parser.py T:\Tools\antlr-4.13.2-complete.jar
```
