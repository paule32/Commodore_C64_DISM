# Pascal Records, Arrays, Sets und OOP-Klassen

Die Pascal-Frontend-Erweiterung baut auf der vorhandenen `c64pascal`-Struktur auf.

Unterstützt werden jetzt:

- `record` mit verschachtelten Feldern,
- statische `array[low..high] of Type`-Typen,
- kleine plattformübergreifende `set of`-Typen (Boolean oder Enum, maximal 16 Werte),
- Set-Literale wie `[Red, Blue]`, Bereiche `[Red..Blue]`, `+`/`-`/`*` für Union/Differenz/Schnittmenge und einfache Membership-Ausdrücke `Red in Flags`,
- Klassenvererbung `TChild = class(TBase)`,
- `private`, `protected`, `public`, `published`,
- Properties mit Feld- oder Methodenaccessoren,
- `virtual` und `override` mit VMT-Slots,
- virtuelle Aufrufe für C64, Amiga und Windows PE32.

Die aktuelle Klassenrepräsentation bleibt kompatibel zum bisherigen Compiler: Klassenvariablen besitzen statischen Objektspeicher. Am Anfang jedes Klassenobjekts liegt nun der zielabhängige VMT-Zeiger (16 Bit C64, 32 Bit Amiga/PE32). Ein Heap-/Reference-Class-Modell kann darauf später aufbauen.

Beispiel:

```pascal
program OOPDemo;

type
  TColor = (Red, Green, Blue);
  TColors = set of TColor;

  TBase = class
  private
    FValue: Integer;
  protected
    procedure SetValue(AValue: Integer);
  public
    procedure Show; virtual;
    property Value: Integer read FValue write SetValue;
  published
    property PublishedValue: Integer read FValue write FValue;
  end;

  TChild = class(TBase)
  public
    procedure Show; override;
  end;

procedure TBase.SetValue(AValue: Integer);
begin
  FValue := AValue;
end;

procedure TBase.Show;
begin
  WriteLn(Value);
end;

procedure TChild.Show;
begin
  WriteLn(Value + 1);
end;

var
  Obj: TChild;
  Flags: TColors;

begin
  Obj.Value := 10;
  Obj.Show;
  Flags := [Red, Blue];
  if Red in Flags then
    WriteLn('Red');
end.
```

Hinweis: Die `.g4`-Dateien dokumentieren die neue Syntax ebenfalls. Für die aktuell mitgelieferten generierten ANTLR-Dateien besitzt `compiler.py` eine kompatible Erweiterungsschicht, damit die neue Syntax ohne Änderung der grundlegenden Parser-Architektur verarbeitet werden kann.
