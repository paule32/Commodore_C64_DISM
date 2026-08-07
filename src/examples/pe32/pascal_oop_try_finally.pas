program Unbenannt;

type
    TObject = class
    public
        constructor Create;
        destructor Destroy;
    end;

constructor TObject.Create;
begin
    WriteLn('TObject: Create');
end;

destructor TObject.Destroy;
begin
    WriteLn('TObject: Destroy');
end;

var
    obj: TObject;

begin
    WriteLn('Test Application');
    obj := TObject.Create;
    try
        WriteLn('in finally');
    finally
        obj.Free;
    end;
    ReadLn;
end.
