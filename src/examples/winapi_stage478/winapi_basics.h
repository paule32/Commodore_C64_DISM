#ifndef DBASE_WINAPI_BASICS_H
#define DBASE_WINAPI_BASICS_H
#define kernel32 "kernel32.dll"
#define user32 "user32.dll"

extern DWORD GetLastError() kernel32 from "GetLastError"
extern DWORD GetCurrentProcessId() kernel32 from "GetCurrentProcessId"
extern HANDLE GetCurrentProcess() kernel32 from "GetCurrentProcess"
extern BOOL IsWindow(HWND) user32 from "IsWindow"
extern CINT MessageBoxW(HWND,LPCWSTR,LPCWSTR,UINT) user32 from "MessageBoxW"
extern CVOID SetLastError(DWORD) kernel32 from "SetLastError"

#endif
