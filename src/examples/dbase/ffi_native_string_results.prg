** Stage 595: native ANSI char* return is automatically copied as dBASE string.
** Windows 32/64 - GetCommandLineA exports LPSTR (DLL owns pointer).
extern LPSTR GetCommandLineA() stdcall "kernel32.dll" from "GetCommandLineA"

STORE GetCommandLineA() TO command_line
? command_line
? "Befehlszeilenlänge: " + LEN(command_line)

** For a custom C DLL returning const char*:
** extern LPCSTR get_text() cdecl "mydll.dll" from "get_text"
** ? get_text() + "!"
** PVOID remains a numeric address, never automatic string conversion:
** extern PVOID get_raw_pointer() cdecl "mydll.dll" from "get_raw_pointer"
