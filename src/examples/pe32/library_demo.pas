// ---------------------------------------------------------------------------
// Interne PE32-DLL ohne externen Assembler/Linker
// ---------------------------------------------------------------------------
library DemoMath;

function Add(A: Integer; B: Integer): Integer;
begin
    Add := A + B;
end;

function Subtract(A: Integer; B: Integer): Integer;
begin
    Subtract := A - B;
end;

exports
    Add,
    Subtract name 'Sub';

begin
end.
