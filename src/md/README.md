# C64-/Amiga-Pascal

Die Pipeline besteht aus zwei getrennten Stufen:

1. `C64PascalLexer.g4` und `C64PascalParser.g4` parsen Pascal mit ANTLR 4.13.2.
2. `compiler.py` erzeugt je nach Ziel lesbaren MOS-6510- oder
   Motorola-68000-Assembler. Die internen Assembler erzeugen daraus ein
   C64-PRG beziehungsweise ein eigenständig bootfähiges Amiga-ADF.

## Installation

```powershell
py -m pip install antlr4-python3-runtime==4.13.2
```

Der Ordner `c64pascal` muss neben `d64_dism.py` liegen.

In der Oberfläche wird das Ziel mit den RadioButtons `C-64` und `Amiga`
gewählt. Die Python-Schnittstelle verwendet entsprechend
`compile_pascal_to_assembly(..., target="c64")` oder `target="amiga"`.
`include_paths=[...]` ergänzt die Suchpfade für Units und PUI-Dateien;
`predefined_macros={"NAME": "WERT"}` setzt Makros des Präprozessors.

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
- `Write`, `WriteLn`, `ClrScr`, `SetTextColor`, `Poke`, `Inc`, `Dec`, `Halt`
- `Peek`, `Chr`, `Ord`, `Lo`, `Hi`
- Dezimalzahlen sowie C64-typische Hex- (`$`) und Binärliterale (`%`)
- `uses` mit rekursiven Pascal-Units
- bevorzugte Pascal Unit Interfaces (`.pui`)
- `{$define}`, `{$undef}`, `{$ifdef}`, `{$ifndef}`, `{$if}`, `{$else}` und
  `{$endif}` mit rekursiver Makroauflösung
- Präprozessorvergleiche `==`, `=`, `!=`, `<>`, `>=`, `<=`, `<` und `>`
- `{$info}`, `{$warn}`/`{$warning}` und `{$error}`

`DIV` und `MOD` arbeiten weiterhin vorzeichenlos. Klasseninstanzen werden auf
dem C64 statisch im Programm reserviert; `Create` initialisiert deshalb ein
bereits vorhandenes Objekt und fordert noch keinen Heap-Speicher an. Dynamische
Arrays, Klassenzeiger, virtuelle Methoden, Overloads, `inherited`, Properties
und allgemeine globale Pascal-Prozeduren/Funktionen mit eigenem
`implementation`-Code sind noch nicht enthalten. Units können Konstanten,
Typen, globale Variablen und statische Klassen samt Methodenimplementierungen
bereitstellen. PUI-Dateien können zusätzlich globale externe Routinen mit
Parameter- und Rückgabetypen sowie zielabhängige ASM-Implementierungsmodule
exportieren. `System.Graphics` verwendet diesen Weg. `const`- und
`var`-Methodenparameter werden syntaktisch akzeptiert, in dieser Stufe aber als
Wertparameter übergeben.

## Units und PUI

Nach dem Programmkopf bindet `uses` eine oder mehrere Units ein:

```pascal
program UnitDemo;
uses BuildInfo, DisplayTypes;
begin
  WriteLn(BuildVersion);
end.
```

Die Suche erfolgt zuerst im Verzeichnis der Hauptdatei, danach in allen
`include_paths`. Für jede Unit wird über alle Suchpfade hinweg zuerst eine
gleichnamige `.pui` gesucht. Ist sie vorhanden, wird ihr Interface auch dann
bevorzugt, wenn daneben eine neuere `.pas`- oder `.pp`-Datei liegt. Die
Quelldatei wird dann nur noch für den Implementation-Teil verwendet. Fehlt die
PUI, erzeugt der Compiler sie atomar aus dem vorverarbeiteten Interface-Teil.
Eine PUI enthält Formatversion, Unit-Name, Interface-`uses`, den bereinigten
Interface-Quelltext, exportierte Symbolnamen und den SHA-256-Wert der
Quelldatei. Version 2 speichert außerdem globale Routinen mit Parametern,
Rückgabetypen, externen Symbolnamen und optionalen zielabhängigen
ASM-Implementierungsdateien. Reine Interface-Units funktionieren auch nur mit
ihrer PUI.
Ein Unit-Guard nach dem Muster `{$ifndef NAME}` / `{$define NAME}` / `{$endif}`
wird in der PUI gespeichert. Bei einem direkten oder indirekten erneuten
`uses` bleibt der Guard-Inhalt inaktiv; ein Zyklus ohne wirksamen Guard wird als
Fehler gemeldet.

## Pascal-Präprozessor

```pascal
{$define VERSION 2}
{$info Übersetze Version VERSION}
{$if VERSION >= 2}
const FeatureEnabled = 1;
{$else}
{$error Diese Version ist zu alt}
{$endif}
```

Makros werden rekursiv in aktivem Pascal-Code und in Bedingungen expandiert,
nicht jedoch in Zeichenketten oder Kommentaren. `{$error}` in einem aktiven
Zweig beendet die Kompilierung mit Datei und Zeile; `info` und `warn` erscheinen
in den Compilerhinweisen.

Für Amiga werden Textausgaben direkt als 8x8-Bitmasken in eine 320x200-
Bitplane geschrieben. Die Unit `System.Graphics` richtet zusätzlich einen
320x200-Bildschirm mit vier Bitplanes und 16 Farben ein. Ihre Routinen liegen
in `c64pascal/units/System/Graphics.amiga.asm` und werden über die PUI als
normale externe 68000-Unterprogramme verbunden. Der erzeugte Code greift direkt
auf `$DFF000` zu und verwendet weder Workbench noch `dos.library` oder
`graphics.library`. `Peek` und `Poke` bleiben bewusst C64-spezifisch und führen
beim Amiga-Ziel zu einer Compilerdiagnose. Das Amiga-Backend erzeugt
ausschließlich Code für den originalen Motorola 68000.

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
