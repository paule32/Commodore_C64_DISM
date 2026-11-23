// ---------------------------------------------------------------------------
// File:   System.SysUtils.prg
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
#ifndef SYSTEM_SYSUTILS_PRG
#define SYSTEM_SYSUTILS_PRG

#include "RuntimeDB"
#include "System.Objects"

CLASS Exception OF TObject
    PUBLIC Message = "Error."
    PUBLIC Code    = 0

    procedure __ini__(AMessage)
        super().__ini__(self)
        Message = Message + ": " + AMessage
        return Message
ENDCLASS

CLASS DbException     OF Exception ENDCLASS

CLASS EAbort          OF Exception ENDCLASS
CLASS EConvertError   OF Exception ENDCLASS
CLASS EOutOfMemory    OF Exception ENDCLASS

CLASS EInOutError     OF Exception ENDCLASS
CLASS EInvalidCast    OF Exception ENDCLASS
CLASS EInvalidPointer OF Exception ENDCLASS
CLASS EIntError       OF Exception ENDCLASS

CLASS EDivByZero      OF EIntError ENDCLASS
CLASS ERangeError     OF EIntError ENDCLASS
CLASS EIntOverflow    OF EIntError ENDCLASS
CLASS EMathError      OF Exception ENDCLASS

// ---------------------------------------------------------------------------
// A Win32 error is a DWORD returned by GetLastError, not an SEH status.
// The Code is preserved when THROW e propagates an existing instance.
// ---------------------------------------------------------------------------
CLASS Win32Exception OF Exception
    // -----------------------------------------------------------------------
    // Windows liefert bereits eine fertige Fehlermeldung via FormatMessage.
    // Daher nicht das benutzerdefinierte "Error.: " der Basisklasse addieren.
    // -----------------------------------------------------------------------
    PROCEDURE __ini__(AMessage)
        Message = "Windows Fehler" + "\n"
        + "Code: " + self.Code     + "\n"
        + "Text: " + AMessage
        RETURN Message
ENDCLASS

CLASS Win32FileException OF Win32Exception ENDCLASS

#endif // SYSTEM_SYSUTILS_PRG
