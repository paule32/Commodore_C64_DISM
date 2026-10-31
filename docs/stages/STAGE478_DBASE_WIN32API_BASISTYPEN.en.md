[Deutsch](STAGE478_DBASE_WIN32API_BASISTYPEN.md) | [English](STAGE478_DBASE_WIN32API_BASISTYPEN.en.md)

# Stage 478 – Win32 API Base Types for dBASE DLL Calls

Expands the Stage-477 FFI with common Win32 integral, pointer, handle, string, and Boolean types. Both PE32 `stdcall` and Microsoft Win64 conventions are supported. Windows uses the **LLP64** model: `LONG` and `DWORD` remain **32 bits even in PE64**, while pointer-sized aliases change width. Eight- and sixteen-bit returns are masked or sign-extended correctly; typed arguments and return values are validated. The source notes include sample Win32 API declarations and tests for both target architectures.

## Source code and command examples (unchanged)

```dbase
#define kernel32 "kernel32.dll"
#define user32 "user32.dll"
extern DWORD GetLastError() kernel32 from "GetLastError"
extern HANDLE GetCurrentProcess() kernel32 from "GetCurrentProcess"
extern BOOL IsWindow(HWND) user32 from "IsWindow"
extern CINT MessageBoxW(HWND,LPCWSTR,LPCWSTR,UINT) user32 from "MessageBoxW"

handle = GetCurrentProcess()
valid = IsWindow(0)
result = MessageBoxW(0, "Grüße", "Unicode", 0)
```

