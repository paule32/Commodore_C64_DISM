// ---------------------------------------------------------------------------
// File:   System.Strings.pas
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
{$L inttostr.o}
{$L strtoint.o}
unit System.Strings;
interface
uses System.Types, System.Objects;

function IntToStr(AValue: Integer): String;
function StrToInt(S: String): Integer;

implementation
//const DLL_FILE = 'libruntime_mini.dll';
function jit_dynstring_from_cstr(AText: Pointer): String; cdecl; external;

//DLL_FILE name '_jit_dynstring_from_cstr' ordinal 52;

function _IntToStr(AValue: Integer): Pointer; cdecl; external;
function _StrToInt(S: String): Integer;       cdecl; external;

function  IntToStr(AValue: Integer): String;
begin
    result := jit_dynstring_from_cstr(_IntToStr(AValue));
end;

function  StrToInt(S: String): Integer;
begin
    result := _StrToInt(S);
end;

end.
