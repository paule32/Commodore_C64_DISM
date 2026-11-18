// System.SysUtils.prg - native dBASE exception class (Stage 612)
#ifndef SYSTEM_SYSUTILS_PRG
#define SYSTEM_SYSUTILS_PRG
#include "System.Objects"
CLASS Exception OF TObject
    PUBLIC
    Message = "Error."
    procedure __ini__(AMessage)
        super().__ini__(self)
        Message = Message + ": " + AMessage
        return Message
ENDCLASS
#endif // SYSTEM_SYSUTILS_PRG
