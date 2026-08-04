program HelloAmiga;

type
  TCounter = class
  private
    FValue: Integer;
  public
    constructor Create(AValue: Integer);
    procedure Inc;
    function GetValue: Integer;
  end;

var
  Counter: TCounter;

constructor TCounter.Create(AValue: Integer);
begin
  FValue := AValue;
end;

procedure TCounter.Inc;
begin
  Inc(FValue);
end;

function TCounter.GetValue: Integer;
begin
  Result := FValue;
end;

begin
  Counter.Create(4);
  Counter.Inc;
  WriteLn('Counter = ', Counter.GetValue());
end.
