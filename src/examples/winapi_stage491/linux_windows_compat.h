#ifndef DBASE_LINUX_WINDOWS_COMPAT_H
#define DBASE_LINUX_WINDOWS_COMPAT_H

* WINDOWS und LINUX werden vom Compiler passend zum Ziel vordefiniert.
#ifdef WINDOWS
#define user32  "user32.dll"
#define shell32 "shell32.dll"
#else
#ifdef LINUX
#define user32  "user32.so"
#define shell32 "shell32.so"
#endif
#endif

extern CINT MessageBoxA(HWND,LPCSTR,LPCSTR,UINT) user32 from "MessageBoxA"
extern CINT MessageBoxW(HWND,LPCWSTR,LPCWSTR,UINT) user32 from "MessageBoxW"
extern HINSTANCE ShellExecute(HWND,LPCSTR,LPCSTR,LPCSTR,LPCSTR,CINT) shell32 from "ShellExecuteA"

#endif
