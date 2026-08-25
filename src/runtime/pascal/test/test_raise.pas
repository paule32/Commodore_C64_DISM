// ---------------------------------------------------------------------------
// File:   test_raise.pas
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
{$linklib libruntime_mini.dll.a}
program test_raise;

uses System.SysUtils;

begin
    try
        WriteLn('before raise');
        raise Exception.Create('fuzz');
        WriteLn('unreachable');
    except
        WriteLn('exception caught');
    end;

    WriteLn('after except');
    ReadLn;
end.
