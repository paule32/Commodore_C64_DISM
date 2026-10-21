#ifndef DBASE_WINAPI_SHELL_H
#define DBASE_WINAPI_SHELL_H
#define shell32 "shell32.dll"

extern HINSTANCE ShellExecute(HWND, LPCSTR, LPCSTR, LPCSTR, ;
    LPCSTR, CINT) shell32 ;
    from "ShellExecuteA"

#endif
