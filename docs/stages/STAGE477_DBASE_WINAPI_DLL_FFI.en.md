[Deutsch](STAGE477_DBASE_WINAPI_DLL_FFI.md) | [English](STAGE477_DBASE_WINAPI_DLL_FFI.en.md)

# Stage 477 – dBASE Windows DLL FFI

Introduces native Windows DLL calls from dBASE with typed declarations and a DLL macro. PE32 uses Windows `WINAPI`/`__stdcall` with reverse-order stack arguments; PE32+ follows the Microsoft x64 ABI (RCX, RDX, R8, R9 and 32-byte shadow space). Types such as `LPCSTR` represent NUL-terminated ANSI pointers. The compiler validates argument numbers and types, resolves imported DLL functions, and generates architecture-correct calls. Tests cover ABI registers/stack, type marshaling, declarations, and generated imports; real external DLL behavior needs Windows validation.

## Source code and command examples (unchanged)

```dbase
#define shell32 "shell32.dll"
extern HINSTANCE ShellExecute(HWND, LPCSTR, LPCSTR, LPCSTR, ;
    LPCSTR, CINT) shell32 ;
    from "ShellExecuteA"

result = ShellExecute(0, "open", "notepad.exe", 0, 0, 1)
? result
```

