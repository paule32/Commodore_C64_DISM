// ---------------------------------------------------------------------------
// File:   Crypto.sha256.pas
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
{$ifndef DLL_API}  // to go away from local linking, we use the DLL import
{$L sha256.o}      // when -D DLL_API is given from the command line; else
{$endif}           // link with a local copy of sha256.o

unit Crypto.sha256;
interface
uses System.Types;

function crypt(S: String; Len: Integer): String; cdecl;

implementation

function _jit_sha256(S: String; Len: Integer): String; cdecl; external;
function crypt(S: String; Len: Integer): String; cdecl;
begin
    result := _jit_sha256(S, Len);
end;

end.
