// ---------------------------------------------------------------------------
// File:   System.Strings.pas
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved.
// Stage:  578 - native PE32 runtime imports for integer/string conversion
// ---------------------------------------------------------------------------
// For PE32, both routines return/accept Pascal dynamic-string data pointers.
// The return value of jit_pas_inttostr is already a Pascal String; do NOT
// pass it through jit_dynstring_from_cstr a second time.
{$ifndef __D64_TARGET_PE32__}
{$L inttostr.o}
{$L strtoint.o}
{$endif}
unit System.Strings;
interface
uses System.Types, System.Objects;

{$ifdef __D64_TARGET_PE32__}
function IntToStr(AValue: Integer): String; cdecl;
    external 'libd64_runtime.dll' name 'jit_pas_inttostr';
function StrToInt(S: String): Integer; cdecl;
    external 'libd64_runtime.dll' name 'jit_pas_strtoint';
{$else}
function IntToStr(AValue: Integer): String;
function StrToInt(S: String): Integer;
{$endif}

implementation
{$ifndef __D64_TARGET_PE32__}
// Legacy implementations for targets other than PE32, unchanged.
function jit_dynstring_from_cstr(AText: Pointer): String; cdecl; external;
function _IntToStr(AValue: Integer): Pointer; cdecl; external;
function _StrToInt(S: String): Integer;       cdecl; external;

function IntToStr(AValue: Integer): String;
begin
    result := jit_dynstring_from_cstr(_IntToStr(AValue));
end;

function StrToInt(S: String): Integer;
begin
    result := _StrToInt(S);
end;
{$endif}
end.
