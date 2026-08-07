program HeapExceptionDemo;

type
    TWorker = class
    private
        FName: String;
    public
        constructor Create;
        destructor Destroy;
        procedure Fail;
    end;

constructor TWorker.Create;
begin
    WriteLn('TWorker.Create');
end;

destructor TWorker.Destroy;
begin
    WriteLn('TWorker.Destroy');
end;

procedure TWorker.Fail;
begin
    WriteLn('TWorker.Fail');
    raise Exception.Create('Fehler aus TWorker.Fail');
end;

var
    Worker: TWorker;

begin
    Worker := TWorker.Create;
    try
        try
            Worker.Fail;
        finally
            WriteLn('inner finally');
        end;
    except
        WriteLn('outer except:');
        WriteLn(ExceptionMessage());
    end;

    Worker.Free;
    ReadLn;
end.
