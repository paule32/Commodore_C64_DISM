#include "winapi_shell.h"

&& Null-HWND; ShellExecuteA verarbeitet LPCSTR als Windows-ANSI (CP1252).
result = ShellExecute(0, "open", "notepad.exe", 0, 0, 1)
? result
