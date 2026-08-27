// ---------------------------------------------------------------------------
// File:   System.Types.pas
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
{$define VERSION 1}
{$define VERSION_TEXT '1.0.0'}
{$define VERSION_NAME 'Community'}
{$define PRODUCT_NAME 'dBase2Many'}

unit System.Types;

interface

type
    Boolean     = 0..1;
    Byte        = 0..255;
    Char        = 0..255;
    Word        = 0..65535;
    DWord       = 0..4294967295;
    
    ShortInt    = -128..127;
    SmallInt    = -32768..32767;
    Int32       = -2147483648..2147483647;
    
    Cardinal    = DWORD;

    UInt32      = DWord;
    
    LongInt     = Int32;
    LongWord    = DWORD;
    
    Real        = Double;  // todo !!
    Extended    = Double;  // todo !!

    PChar       = ^Char;
    
    AnsiChar    =  Char;
    PAnsiChar   = ^AnsiChar;
    
    AnsiString  = String;
    PAnsiString = ^AnsiString;
    
    PByte       = ^Byte;

implementation

begin
end.
