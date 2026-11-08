unit UFoo;

interface
uses System;

type
  {$export TFoo}
  TFoo = class(TObject)
  private
    FValue: Integer;
  protected
    FProtected: Integer;
  public
    constructor Create(AValue: Integer);
    destructor Destroy; override;
    procedure SetValue(AValue: Integer);
    function GetValue: Integer;
  published
    property Value: Integer read FValue write FValue;
  end;

implementation

constructor TFoo.Create(AValue: Integer);
begin
  inherited Create;
  FValue := AValue;
end;

procedure TFoo.SetValue(AValue: Integer);
begin
  FValue := AValue;
end;

function TFoo.GetValue: Integer;
begin
  Result := FValue;
end;

destructor TFoo.Destroy;
begin
  inherited Destroy;
end;

end.
