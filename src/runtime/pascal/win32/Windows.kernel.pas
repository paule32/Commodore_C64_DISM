// ---------------------------------------------------------------------------
// File:   Windows.kernel.pas
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
unit Windows.kernel;

interface
uses System;

const DLL_KERNEL32 = 'kernel32.dll';

function GetModuleHandleA(
    lpModuleName: PAnsiChar
    ): HMODULE; stdcall; external
    DLL_KERNEL32 name 'GetModuleHandleA';

procedure ExitProcess(
    AValue: DWord
    ); stdcall; external
    DLL_KERNEL32 name 'ExitProcess';

implementation

end.
