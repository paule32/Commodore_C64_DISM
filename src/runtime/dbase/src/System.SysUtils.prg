// ---------------------------------------------------------------------------
// File:   System.SysUtils.prg
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
#ifndef SYSTEM_SYSUTILS_PRG
#define SYSTEM_SYSUTILS_PRG

#include "System.Objects.prg"

CLASS Exception OF TObject
    Message = "Exception"
    procedure __ini__(AMessage)
        super().__ini__()
        Message = Message + ": " + AMessage
    return Message
ENDCLASS

#endif    // SYSTEM_SYSUTILS_PRG
