#include "linux_windows_compat.h"
? "Qt5 Dialog aus dBASE"
LOCAL ergebnis
* MB_YESNO | MB_ICONQUESTION = 0x24
* IDYES = 6, IDNO = 7
 ergebnis = MessageBoxA(0, "Linux und Windows?", "dBASE Beispiel", 0x24)
? ergebnis
