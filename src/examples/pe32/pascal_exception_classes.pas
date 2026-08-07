program PascalExceptionClasses;

type
    EMyException = class(Exception)
    end;

    EOtherException = class(Exception)
    end;

begin
    try
        raise EMyException.Create('Das ist eine EMyException');
    except
        on E: EOtherException do
        begin
            WriteLn('Other:');
            WriteLn(E.Message);
        end;

        on E: EMyException do
        begin
            WriteLn('My exception:');
            WriteLn(E.Message);
        end;

        on E: Exception do
        begin
            WriteLn('Fallback Exception:');
            WriteLn(E.Message);
        end;
    end;

    ReadLn;
end.
