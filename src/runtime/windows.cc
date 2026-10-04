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

// ---------------------------------------------------------------------------
// Stage 271 - Workstation DEBUG mirror
// ---------------------------------------------------------------------------
// Der dBase/WFM-Pfad besitzt bereits das DOW1-Protokoll zum residenten
// Workstation Runner. Pascal Write/WriteLn benutzt denselben Empfangskanal als
// zusaetzlichen Spiegel. STD_OUTPUT_HANDLE bleibt unangetastet, so dass ein
// Console-Target und ReadLn weiterhin normal funktionieren.
namespace {
constexpr const char D64_WORKSTATION_DEBUG_ENV[] =
    "D64_WORKSTATION_DEBUG_OUTPUT";
constexpr const char D64_WORKSTATION_PIPE_NAME[] =
    "\\\\.\\pipe\\dBase2Many.D64Workstation.Runner.v1";
constexpr DWORD D64_WORKSTATION_OUTPUT_MAGIC = 0x31574F44u; // "DOW1"
constexpr DWORD D64_WORKSTATION_OUTPUT_LATIN1 = 0x00000010u;
constexpr DWORD D64_GENERIC_WRITE = 0x40000000u;
constexpr DWORD D64_OPEN_EXISTING = 3u;
constexpr DWORD D64_ERROR_FILE_NOT_FOUND = 2u;
constexpr DWORD D64_ERROR_PIPE_BUSY = 231u;

struct D64WorkstationOutputHeader {
    DWORD magic;
    DWORD flags;
    DWORD textBytes;
    DWORD processId;
};

typedef DWORD  (JIT_STDCALL *D64PFN_GetEnvironmentVariableA)(LPCSTR, LPSTR, DWORD);
typedef HANDLE (JIT_STDCALL *D64PFN_CreateFileA)(
    LPCSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
typedef BOOL   (JIT_STDCALL *D64PFN_CloseHandle)(HANDLE);
typedef VOID   (JIT_STDCALL *D64PFN_Sleep)(DWORD);
typedef DWORD  (JIT_STDCALL *D64PFN_GetCurrentProcessId)(VOID);
typedef BOOL   (JIT_STDCALL *D64PFN_WaitNamedPipeA)(LPCSTR, DWORD);

struct D64WorkstationDebugApi {
    bool initialized;
    bool enabled;
    D64PFN_GetEnvironmentVariableA getEnvironmentVariableA;
    D64PFN_CreateFileA createFileA;
    D64PFN_CloseHandle closeHandle;
    D64PFN_Sleep sleep;
    D64PFN_GetCurrentProcessId getCurrentProcessId;
    D64PFN_WaitNamedPipeA waitNamedPipeA;
};

D64WorkstationDebugApi g_d64WorkstationDebugApi = {
    false, false, nullptr, nullptr, nullptr, nullptr, nullptr, nullptr
};

bool d64_init_workstation_debug_api()
{
    if (g_d64WorkstationDebugApi.initialized)
        return g_d64WorkstationDebugApi.enabled;

    g_d64WorkstationDebugApi.initialized = true;
    if (!p_LoadLibraryA || !p_GetProcAddress)
        return false;

    HMODULE kernel = p_LoadLibraryA("kernel32.dll");
    if (!kernel)
        return false;

    g_d64WorkstationDebugApi.getEnvironmentVariableA =
        reinterpret_cast<D64PFN_GetEnvironmentVariableA>(
            p_GetProcAddress(kernel, "GetEnvironmentVariableA"));
    g_d64WorkstationDebugApi.createFileA =
        reinterpret_cast<D64PFN_CreateFileA>(
            p_GetProcAddress(kernel, "CreateFileA"));
    g_d64WorkstationDebugApi.closeHandle =
        reinterpret_cast<D64PFN_CloseHandle>(
            p_GetProcAddress(kernel, "CloseHandle"));
    g_d64WorkstationDebugApi.sleep =
        reinterpret_cast<D64PFN_Sleep>(
            p_GetProcAddress(kernel, "Sleep"));
    g_d64WorkstationDebugApi.getCurrentProcessId =
        reinterpret_cast<D64PFN_GetCurrentProcessId>(
            p_GetProcAddress(kernel, "GetCurrentProcessId"));
    g_d64WorkstationDebugApi.waitNamedPipeA =
        reinterpret_cast<D64PFN_WaitNamedPipeA>(
            p_GetProcAddress(kernel, "WaitNamedPipeA"));

    if (!g_d64WorkstationDebugApi.getEnvironmentVariableA ||
        !g_d64WorkstationDebugApi.createFileA ||
        !g_d64WorkstationDebugApi.closeHandle ||
        !g_d64WorkstationDebugApi.sleep ||
        !g_d64WorkstationDebugApi.getCurrentProcessId) {
        return false;
    }

    char enabled[8] = {};
    const DWORD length = g_d64WorkstationDebugApi.getEnvironmentVariableA(
        D64_WORKSTATION_DEBUG_ENV,
        enabled,
        static_cast<DWORD>(sizeof(enabled))
    );
    g_d64WorkstationDebugApi.enabled =
        length == 1 && enabled[0] == '1';
    return g_d64WorkstationDebugApi.enabled;
}

bool d64_workstation_pipe_write_exact(HANDLE pipe, const void *data, DWORD size)
{
    const BYTE *cursor = static_cast<const BYTE *>(data);
    DWORD total = 0;
    while (total < size) {
        DWORD written = 0;
        if (!p_WriteFile ||
            !p_WriteFile(pipe, cursor + total, size - total, &written, nullptr) ||
            written == 0) {
            return false;
        }
        total += written;
    }
    return true;
}
} // namespace

extern "C" void d64_workstation_debug_mirror(const char *text, DWORD length)
{
    if (!text || length == 0 || !d64_init_workstation_debug_api())
        return;

    HANDLE pipe = INVALID_HANDLE_VALUE;
    for (int attempt = 0; attempt < 40; ++attempt) {
        pipe = g_d64WorkstationDebugApi.createFileA(
            D64_WORKSTATION_PIPE_NAME,
            D64_GENERIC_WRITE,
            0,
            nullptr,
            D64_OPEN_EXISTING,
            0,
            nullptr
        );
        if (pipe != INVALID_HANDLE_VALUE)
            break;

        const DWORD error = p_GetLastError ? p_GetLastError() : 0;
        if (error != D64_ERROR_PIPE_BUSY && error != D64_ERROR_FILE_NOT_FOUND)
            return;
        if (g_d64WorkstationDebugApi.waitNamedPipeA)
            g_d64WorkstationDebugApi.waitNamedPipeA(D64_WORKSTATION_PIPE_NAME, 25);
        g_d64WorkstationDebugApi.sleep(5);
    }

    if (pipe == INVALID_HANDLE_VALUE)
        return;

    D64WorkstationOutputHeader header{};
    header.magic = D64_WORKSTATION_OUTPUT_MAGIC;
    // Pascal-Stringliterale werden vom Compiler als Latin-1 Bytes abgelegt.
    // dBase/WFM sendet weiterhin UTF-8 ohne dieses Flag.
    header.flags = D64_WORKSTATION_OUTPUT_LATIN1;
    header.textBytes = length;
    header.processId = g_d64WorkstationDebugApi.getCurrentProcessId();

    bool ok = d64_workstation_pipe_write_exact(
        pipe, &header, static_cast<DWORD>(sizeof(header))
    );
    if (ok)
        d64_workstation_pipe_write_exact(pipe, text, length);

    g_d64WorkstationDebugApi.closeHandle(pipe);
}

extern "C" void _jit_print_text(const char *s)
{
    if (!s) return;
    const DWORD length = _jit_strlen_local(s);
    HANDLE h = p_GetStdHandle(STD_OUTPUT_HANDLE);
    if (h) {
        DWORD written = 0;
        p_WriteFile(h, s, length, &written, 0);
    }
    d64_workstation_debug_mirror(s, length);
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

