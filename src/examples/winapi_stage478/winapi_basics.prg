#include "winapi_basics.h"

? "Prozess-ID:"
? GetCurrentProcessId()
? "Prozess-Handle (als dBASE Zahl):"
? GetCurrentProcess()
? "Ist Fensterhandle 0 gueltig?"
? IsWindow(0)
SetLastError(0)
? GetLastError()
** Das nachstehende Beispiel zeigt eine native Unicode-Meldungsbox.
MessageBoxW(0, "Grüße aus dBASE", "Win32 API (Unicode)", 0)
