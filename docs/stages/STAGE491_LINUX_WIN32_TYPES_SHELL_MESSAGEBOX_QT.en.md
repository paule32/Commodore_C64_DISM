[Deutsch](STAGE491_LINUX_WIN32_TYPES_SHELL_MESSAGEBOX_QT.md) | [English](STAGE491_LINUX_WIN32_TYPES_SHELL_MESSAGEBOX_QT.en.md)

# Stage 491 – Platform Macros, Linux Win32 Types, and Qt5 FFI

Adds `WINDOWS=1` when compiling `pe32`/`pe64` and `LINUX=1` for `linux32`/`linux64` through the preprocessor. Common Win32-style types and handles (`HWND` and related aliases) are mapped appropriately for Linux compatibility, and `ShellExecuteA`, `MessageBoxA/W`, and `THIS.HWND` use platform-aware FFI routes. The Linux implementation relies on a native Qt5 shared library rather than loading Windows DLLs. Python-level tests cover macro expansion, includes, type checking, `.prg`/`.wfm`, and both ELF architectures. Real `QMessageBox` display and building `libd64_qt5.so` were unavailable without Qt5 development files.

## Source code and command examples (unchanged)

```text
#ifdef WINDOWS
#define shell32 "shell32.dll"
#define user32  "user32.dll"
#else
#ifdef LINUX
#define shell32 "shell32.so"
#define user32  "user32.so"
#endif
#endif
extern HINSTANCE ShellExecute(HWND,LPCSTR,LPCSTR,LPCSTR,LPCSTR,CINT) shell32 from "ShellExecuteA"
extern CINT MessageBoxA(HWND,LPCSTR,LPCSTR,UINT) user32 from "MessageBoxA"
```


```c
int MessageBoxA(uintptr_t hwnd, const char *text, const char *caption, unsigned int type);
int MessageBoxW(uintptr_t hwnd, const uint16_t *text, const uint16_t *caption, unsigned int type);
```


```bash
sudo apt install build-essential qtbase5-dev qt5-qmake
cd d64qt5
./build_linux.sh
```

