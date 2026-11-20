// Stage 647: original user example, including multiline string + numeric DWORD
#ifndef SYSTEM_SYSUTILS_PRG
#define SYSTEM_SYSUTILS_PRG
#include "System.Objects"

CLASS Exception OF TObject
    PUBLIC Message = "Error."
    PUBLIC Code    = 0
    procedure __ini__(AMessage)
        super().__ini__(self)
        Message = Message + ": " + AMessage
        return Message
ENDCLASS

CLASS DbException OF Exception ENDCLASS

CLASS Win32Exception OF Exception
    PROCEDURE __ini__(AMessage)
        Message = "Windows Fehler" + "\n"
        + "Code: " + super().Code + "\n"
        + "Text: " + AMessage
        RETURN Message
ENDCLASS
CLASS Win32FileException OF Win32Exception ENDCLASS
#endif
