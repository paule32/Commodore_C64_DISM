program OOPRecordsSetsArraysClasses;

type
  TColor = (Red, Green, Blue, Yellow);
  TColors = set of TColor;

  TPoint = record
    X, Y: Integer;
    Color: TColor;
  end;

  TPoints = array[0..3] of TPoint;

  TShape = class
  private
    FValue: Integer;
  protected
    FStep: Integer;
  public
    constructor Create(AValue: Integer);
    procedure Step;
    procedure Show; virtual;
  published
    property Value: Integer read FValue write FValue;
  end;

  TMovingShape = class(TShape)
  private
    FExtra: Integer;
  public
    procedure Show; override;
    procedure SetExtra(AValue: Integer);
  end;

var
  Shape: TMovingShape;
  Point: TPoint;
  Points: TPoints;
  Colors: TColors;

constructor TShape.Create(AValue: Integer);
begin
  FValue := AValue;
  FStep := 1;
end;

procedure TShape.Step;
begin
  FValue := FValue + FStep;
end;

procedure TShape.Show;
begin
  WriteLn('TShape.Value = ', FValue);
end;

procedure TMovingShape.Show;
begin
  FStep := FStep + 1;
  WriteLn('TMovingShape.Value = ', Value);
end;

procedure TMovingShape.SetExtra(AValue: Integer);
begin
  FExtra := AValue;
end;

begin
  Point.X := 10;
  Point.Y := 20;
  Point.Color := Green;

  Points[0].X := Point.X;
  Points[0].Y := Point.Y;
  Points[0].Color := Point.Color;

  Colors := [Red, Blue];
  Include(Colors, Green);
  Exclude(Colors, Red);

  Shape := TMovingShape.Create(7);
  Shape.Value := 11;
  Shape.SetExtra(3);
  Shape.Show;

  if Blue in Colors then
    WriteLn('Blue ist gesetzt');
end.
