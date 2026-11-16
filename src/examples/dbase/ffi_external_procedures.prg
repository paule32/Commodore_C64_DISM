** Stage 594: dBASE imports for a Windows DLL procedure (no return value).
** The DLL is imported by the PE linker; no runtime LoadLibrary is needed.
#ifndef DEBUG_DLL
#define DEBUG_DLL "kernel32.dll"
#else
#undef DEBUG_DLL
#define DEBUG_DLL "kernel32.dll"
#endif

** PROCEDURE = CVOID; stdcall is the default for old dBASE headers.
extern PROCEDURE OutputDebugStringA(LPCSTR); stdcall; DEBUG_DLL; from "OutputDebugStringA"

** Equivalently, with the optional return type omitted:
** extern OutputDebugStringA(LPCSTR) stdcall DEBUG_DLL from "OutputDebugStringA"

OutputDebugStringA("dBASE: externe Prozedur erfolgreich aufgerufen")
