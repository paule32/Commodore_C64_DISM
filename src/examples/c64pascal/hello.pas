// ---------------------------------------------------------------------------
// (c) 2026 by Jens Kallup - paule32
// Alle Rechte vorbehalten.
// ---------------------------------------------------------------------------
program HelloC64;

var
  I: Integer;

begin
  ClrScr;
  WriteLn('C64 PASCAL');

  for I := 0 to 25 do
  begin
    Poke($0400 + I, 1 + I);
    Poke($D800 + I, 1);
  end;
end.

