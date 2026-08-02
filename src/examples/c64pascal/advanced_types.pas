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
  Index: Integer;

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
  Point.Y := 20;
  Point.Color := Green;

  Points[1].X := Point.X;
  Points[1].Y := Point.Y;
  Points[1].Color := Point.Color;

  Index := 2;
  Points[Index].X := 30;
  Points[Index].Y := 40;
  Points[Index].Color := Blue;

  Counter.Create(4);
  Counter.Inc;
  WriteLn('Counter = ', Counter.GetValue());
end.
