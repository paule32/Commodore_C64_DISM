// ---------------------------------------------------------------------------
// \file windows.cc
// \note Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "stddef.h"
# include "windows.h"

// ---------------------------------------------------------------------------
// Windows error handling ...
// ---------------------------------------------------------------------------
PFN_GetLastError    p_GetLastError    = nullptr;
PFN_SetLastError    p_SetLastError    = nullptr;

PFN_GetProcAddress  p_GetProcAddress  = nullptr;
PFN_GetStdHandle    p_GetStdHandle    = nullptr;
PFN_ExitProcess     p_ExitProcess     = nullptr;

// ---------------------------------------------------------------------------
// Windows command line interface (console) ...
// ---------------------------------------------------------------------------
PFN_GetCommandLineA p_GetCommandLineA = nullptr;
PFN_MessageBoxA     p_MessageBoxA     = nullptr;

// ---------------------------------------------------------------------------
// locales language code identifiers ...
// ---------------------------------------------------------------------------
PFN_GetUserDefaultLCID   p_GetUserDefaultLCID   = nullptr;
PFN_GetSystemDefaultLCID p_GetSystemDefaultLCID = nullptr;

PFN_ReadFile        p_ReadFile        = nullptr;
PFN_WriteFile       p_WriteFile       = nullptr;
// ---------------------------------------------------------------------------
// disk drive proto types ...
// ---------------------------------------------------------------------------
PFN_GetDriveTypeA         p_GetDriveTypeA         = nullptr;

PFN_GetDiskFreeSpaceExA   p_GetDiskFreeSpaceExA   = nullptr;
PFN_GetDiskFreeSpaceA     p_GetDiskFreeSpaceA     = nullptr;

PFN_GetVolumeInformationA p_GetVolumeInformationA = nullptr;

// ---------------------------------------------------------------------------
// windows network stuff ...
// ---------------------------------------------------------------------------
PFN_WNetGetConnectionA    p_WNetGetConnectionA    = nullptr;

#ifdef __cplusplus
extern "C" {
#endif

DLL_API HMODULE JIT_STDCALL LoadLibraryA(LPCSTR  lpLibFileName) {
    return p_LoadLibraryA(lpLibFileName);
}

DLL_API int JIT_STDCALL MessageBoxA(
    HANDLE hwnd,
    const char* text,
    const char* caption,
    unsigned int type) {
    return p_MessageBoxA(hwnd, text, caption, type);
}

DLL_API VOID
_jit_ExitProcess(DWORD uExitCode) {
    p_ExitProcess(uExitCode);
}
DLL_API VOID
ExitProcess(DWORD uExitCode) {
    p_ExitProcess(uExitCode);
}
DLL_API DWORD
GetLastError(void){
    return p_GetLastError();
}

DLL_API VOID
SetLastError(DWORD error) {
    p_SetLastError(error);
}

DLL_API BOOL JIT_STDCALL WriteFile(HANDLE h, const void *b, DWORD l, DWORD *w, void *r) {
    return p_WriteFile(h, b, l, w, r);
}
DLL_API BOOL JIT_STDCALL ReadFile (HANDLE h, const void *b, DWORD l, DWORD *w, void *r) {
    return p_ReadFile (h, b, l, w, r);
}

static unsigned int _jit_strlen_local(const char *s)
{
    unsigned int n = 0;
    while (s && s[n])
        n++;
    return n;
}
extern "C" void _jit_print_text(const char *s)
{
    if (!s) return;
    HANDLE h = p_GetStdHandle(STD_OUTPUT_HANDLE);
    if (!h) return;

    DWORD written = 0;
    p_WriteFile(
        h,
        s,
        _jit_strlen_local(s),
        &written,
        0
    );
}

DLL_API LPSTR   JIT_STDCALL GetCommandLineA(VOID) {
    return p_GetCommandLineA();
}
DLL_API HANDLE  JIT_STDCALL GetStdHandle(DWORD h) {
    return p_GetStdHandle(h);
}

DLL_API FARPROC JIT_STDCALL GetProcAddress(
    HMODULE hModule,
    LPCSTR lpProcName) {
    return p_GetProcAddress(hModule, lpProcName);
}

DLL_API UINT
GetDriveTypeA(const char *rootPath) {
    return p_GetDriveTypeA(rootPath);
}

DLL_API BOOL
GetDiskFreeSpaceExA(
    LPCSTR          lpDirectoryName,
    PULARGE_INTEGER lpFreeBytesAvailableToCaller,
    PULARGE_INTEGER lpTotalNumberOfBytes,
    PULARGE_INTEGER lpTotalNumberOfFreeBytes) {
    
    return p_GetDiskFreeSpaceExA(
        lpDirectoryName,
        lpFreeBytesAvailableToCaller,
        lpTotalNumberOfBytes,
        lpTotalNumberOfFreeBytes
    );
}

DLL_API BOOL JIT_STDCALL GetDiskFreeSpaceA(
    LPCSTR  lpRootPathName,
    LPDWORD lpSectorsPerCluster,
    LPDWORD lpBytesPerSector,
    LPDWORD lpNumberOfFreeClusters,
    LPDWORD lpTotalNumberOfClusters) {
    
    return p_GetDiskFreeSpaceA(
        lpRootPathName,
        lpSectorsPerCluster,
        lpBytesPerSector,
        lpNumberOfFreeClusters,
        lpTotalNumberOfClusters
    );
}

DLL_API BOOL JIT_STDCALL GetVolumeInformationA(
    LPCSTR  lpRootPathName,
    LPSTR   lpVolumeNameBuffer,
    DWORD   nVolumeNameSize,
    LPDWORD lpVolumeSerialNumber,
    LPDWORD lpMaximumComponentLength,
    LPDWORD lpFileSystemFlags,
    LPSTR   lpFileSystemNameBuffer,
    DWORD   nFileSystemNameSize) {
    
    return p_GetVolumeInformationA(
        lpRootPathName,
        lpVolumeNameBuffer,
        nVolumeNameSize,
        lpVolumeSerialNumber,
        lpMaximumComponentLength,
        lpFileSystemFlags,
        lpFileSystemNameBuffer,
        nFileSystemNameSize
    );
}

DLL_API DWORD JIT_STDCALL WNetGetConnectionA(
    LPCSTR  lpLocalName,
    LPSTR   lpRemoteName,
    LPDWORD lpnLength) {
    
    return p_WNetGetConnectionA(
        lpLocalName,
        lpRemoteName,
        lpnLength
    );
}

#ifdef __cplusplus
};
#endif

