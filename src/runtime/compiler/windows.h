// ---------------------------------------------------------------------------
// File: windows.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_WINDOWS_HH__
#define __DBASE2MANY_WINDOWS_HH__

# pragma once
# include "stddef.h"

extern "C" {

// --------------------------------------------------------------------
// historical constant's ...
// --------------------------------------------------------------------
constexpr WORD MAX_PATH = 260;

// --------------------------------------------------------------------
// GetLastError()
// --------------------------------------------------------------------
constexpr DWORD NO_ERROR                     =   0;
constexpr DWORD ERROR_SUCCESS                =   0;
constexpr DWORD ERROR_FILE_NOT_FOUND         =   2;
constexpr DWORD ERROR_PATH_NOT_FOUND         =   3;
constexpr DWORD ERROR_ACCESS_DENIED          =   5;
constexpr DWORD ERROR_INVALID_HANDLE         =   6;
constexpr DWORD ERROR_NOT_ENOUGH_MEMORY      =   8;
constexpr DWORD ERROR_BAD_FORMAT             =  11;
constexpr DWORD ERROR_INVALID_DRIVE          =  15;
constexpr DWORD ERROR_NOT_READY              =  21;
constexpr DWORD ERROR_CRC                    =  23;
constexpr DWORD ERROR_WRITE_FAULT            =  29;
constexpr DWORD ERROR_SHARING_VIOLATION      =  32;
constexpr DWORD ERROR_FILE_EXISTS            =  80;
constexpr DWORD ERROR_INVALID_PARAMETER      =  87;
constexpr DWORD ERROR_INSUFFICIENT_BUFFER    = 122;
constexpr DWORD ERROR_BAD_COMPRESSION_BUFFER = 605;

// --------------------------------------------------------------------
// resource types ...
// --------------------------------------------------------------------
# define MAKEINTRESOURCEA(value) ((LPSTR)(ULONG_PTR)((WORD)(value)))
# define RT_RCDATA MAKEINTRESOURCEA(10)

// --------------------------------------------------------------------
// dll loader main
// --------------------------------------------------------------------
constexpr DWORD DLL_PROCESS_DETACH = 0;
constexpr DWORD DLL_PROCESS_ATTACH = 1;
constexpr DWORD DLL_THREAD_ATTACH  = 2;
constexpr DWORD DLL_THREAD_DETACH  = 3;

DLL_API BOOL JIT_STDCALL DllMain(
    HINSTANCE hinstDLL,
    DWORD     fdwReason,
    LPVOID    lpvReserved);

DLL_API BOOL JIT_STDCALL DllMainCRTStartup(
    HINSTANCE hinstDLL,
    DWORD     fdwReason,
    LPVOID    lpvReserved);

// --------------------------------------------------------------------
// GetDriveType()
// --------------------------------------------------------------------
enum DriveType {
    DRIVE_UNKNOWN      = 0,
    DRIVE_NO_ROOT_DIR  = 1,
    DRIVE_REMOVABLE    = 2,
    DRIVE_FIXED        = 3,
    DRIVE_REMOTE       = 4,
    DRIVE_CDROM        = 5,
    DRIVE_RAMDISK      = 6
};

// --------------------------------------------------------------------
// important file system constant's ...
// --------------------------------------------------------------------
constexpr DWORD FILE_CASE_SENSITIVE_SEARCH    = 0x00000001;
constexpr DWORD FILE_CASE_PRESERVED_NAMES     = 0x00000002;
constexpr DWORD FILE_UNICODE_ON_DISK          = 0x00000004;
constexpr DWORD FILE_PERSISTENT_ACLS          = 0x00000008;
constexpr DWORD FILE_FILE_COMPRESSION         = 0x00000010;
constexpr DWORD FILE_VOLUME_QUOTAS            = 0x00000020;
constexpr DWORD FILE_SUPPORTS_SPARSE_FILES    = 0x00000040;
constexpr DWORD FILE_SUPPORTS_REPARSE_POINTS  = 0x00000080;
constexpr DWORD FILE_ATTRIBUTE_TEMPORARY      = 0x00000100;
constexpr DWORD FILE_VOLUME_IS_COMPRESSED     = 0x00008000;
constexpr DWORD FILE_SUPPORTS_OBJECT_IDS      = 0x00010000;
constexpr DWORD FILE_SUPPORTS_ENCRYPTION      = 0x00020000;
constexpr DWORD FILE_NAMED_STREAMS            = 0x00040000;
constexpr DWORD FILE_READ_ONLY_VOLUME         = 0x00080000;

constexpr DWORD GENERIC_WRITE                 = 0x40000000;
constexpr DWORD CREATE_ALWAYS                 = 2U;
// --------------------------------------------------------------------
// console handle's ...
// --------------------------------------------------------------------
constexpr DWORD STD_OUTPUT_HANDLE = -11;
constexpr DWORD STD_INPUT_HANDLE  = -10;

// --------------------------------------------------------------------
// handle constants ...
// --------------------------------------------------------------------
static const HANDLE INVALID_HANDLE_VALUE =
    reinterpret_cast<HANDLE>(
        static_cast<intptr_t>(-1)
    );

// --------------------------------------------------------------------
// pre-loader stuff ...
// --------------------------------------------------------------------
typedef HMODULE (JIT_STDCALL *PFN_LoadLibraryA)(LPCSTR);
typedef FARPROC (JIT_STDCALL *PFN_GetProcAddress)(HMODULE, LPCSTR);
typedef VOID    (JIT_STDCALL *PFN_ExitProcess)(DWORD);

typedef int     (JIT_STDCALL *PFN_MessageBoxA)(HANDLE, LPCSTR, LPCSTR, UINT);

typedef DWORD   (JIT_STDCALL *PFN_GetLastError)();
typedef VOID    (JIT_STDCALL *PFN_SetLastError)(DWORD error);

typedef LPSTR   (JIT_STDCALL *PFN_GetCommandLineA)(VOID);
typedef HANDLE  (JIT_STDCALL *PFN_GetStdHandle)(DWORD);

typedef LCID    (JIT_STDCALL *PFN_GetUserDefaultLCID)(VOID);
typedef LCID    (JIT_STDCALL *PFN_GetSystemDefaultLCID)(VOID);

typedef BOOL    (JIT_STDCALL *PFN_WriteFile)(HANDLE, const void *, DWORD, DWORD *, void *);
typedef BOOL    (JIT_STDCALL *PFN_ReadFile )(HANDLE, const void *, DWORD, DWORD *, void *);

typedef UINT    (JIT_STDCALL *PFN_GetDriveTypeA)(const char *rootPath);
typedef BOOL    (JIT_STDCALL *PFN_GetDiskFreeSpaceExA)(
    LPCSTR,
    PULARGE_INTEGER,
    PULARGE_INTEGER,
    PULARGE_INTEGER
);
typedef BOOL    (JIT_STDCALL *PFN_GetDiskFreeSpaceA)(
    LPCSTR  lpRootPathName,
    LPDWORD lpSectorsPerCluster,
    LPDWORD lpBytesPerSector,
    LPDWORD lpNumberOfFreeClusters,
    LPDWORD lpTotalNumberOfClusters
);
typedef BOOL    (JIT_STDCALL *PFN_GetVolumeInformationA)(
    LPCSTR  lpRootPathName,
    LPSTR   lpVolumeNameBuffer,
    DWORD   nVolumeNameSize,
    LPDWORD lpVolumeSerialNumber,
    LPDWORD lpMaximumComponentLength,
    LPDWORD lpFileSystemFlags,
    LPSTR   lpFileSystemNameBuffer,
    DWORD   nFileSystemNameSize
);

typedef DWORD   (JIT_STDCALL *PFN_WNetGetConnectionA)(
    LPCSTR  lpLocalName,
    LPSTR   lpRemoteName,
    LPDWORD lpnLength
);

extern PFN_LoadLibraryA    p_LoadLibraryA;
extern PFN_GetProcAddress  p_GetProcAddress;
extern PFN_ExitProcess     p_ExitProcess;

extern PFN_GetLastError    p_GetLastError;
extern PFN_SetLastError    p_SetLastError;

extern PFN_GetCommandLineA p_GetCommandLineA;
extern PFN_GetStdHandle    p_GetStdHandle;

extern PFN_GetUserDefaultLCID   p_GetUserDefaultLCID;
extern PFN_GetSystemDefaultLCID p_GetSystemDefaultLCID;

extern PFN_WriteFile       p_WriteFile;
extern PFN_ReadFile        p_ReadFile;

extern PFN_MessageBoxA     p_MessageBoxA;
extern PFN_GetDriveTypeA   p_GetDriveTypeA;

extern PFN_GetDiskFreeSpaceExA   p_GetDiskFreeSpaceExA;
extern PFN_GetDiskFreeSpaceA     p_GetDiskFreeSpaceA;
extern PFN_GetVolumeInformationA p_GetVolumeInformationA;

extern PFN_WNetGetConnectionA    p_WNetGetConnectionA;

// --------------------------------------------------------------------
// win32api function's ...
// --------------------------------------------------------------------
typedef UINT    (JIT_STDCALL *PFN_GetDriveType)(void* dest, const void* src, size_t count);

// --------------------------------------------------------------------
DLL_API HMODULE JIT_STDCALL LoadLibraryA(LPCSTR  lpLibFileName);
DLL_API BOOL    JIT_STDCALL FreeLibrary (HMODULE hModule);
DLL_API VOID    JIT_STDCALL ExitProcess (DWORD   uExitCode);

// --------------------------------------------------------------------
// Windows error handling
// --------------------------------------------------------------------
DLL_API DWORD   JIT_STDCALL GetLastError(void);
DLL_API VOID    JIT_STDCALL SetLastError(DWORD error);

// --------------------------------------------------------------------
// Windows Command Line (console) ...
// --------------------------------------------------------------------
DLL_API LPSTR   JIT_STDCALL GetCommandLineA(VOID);

// --------------------------------------------------------------------
// locale supported win32api members ...
// --------------------------------------------------------------------
DLL_API LCID    JIT_STDCALL GetUserDefaultLCID(VOID);
DLL_API LCID    JIT_STDCALL GetSystemDefaultLCID(VOID);

// --------------------------------------------------------------------
// Windows file input / output ...
// --------------------------------------------------------------------
DLL_API BOOL    JIT_STDCALL WriteFile(HANDLE, const void *, DWORD, DWORD *, void *);
DLL_API BOOL    JIT_STDCALL ReadFile (HANDLE, const void *, DWORD, DWORD *, void *);

typedef struct _SECURITY_ATTRIBUTES {
    DWORD  nLength;
    LPVOID lpSecurityDescriptor;
    BOOL   bInheritHandle;
    
}   SECURITY_ATTRIBUTES;

typedef SECURITY_ATTRIBUTES * PSECURITY_ATTRIBUTES;
typedef SECURITY_ATTRIBUTES * LPSECURITY_ATTRIBUTES;

DLL_API HANDLE  JIT_STDCALL CreateFileA(
    LPCSTR                lpFileName,
    DWORD                 dwDesiredAccess,
    DWORD                 dwShareMode,
    LPSECURITY_ATTRIBUTES lpSecurityAttributes,
    DWORD                 dwCreationDisposition,
    DWORD                 dwFlagsAndAttributes,
    HANDLE                hTemplateFile
);
DLL_API BOOL    JIT_STDCALL DeleteFileA(LPCSTR lpFileName);

DLL_API HANDLE  JIT_STDCALL GetStdHandle(DWORD);
DLL_API HMODULE JIT_STDCALL GetModuleHandleA(LPCSTR lpModuleName);
DLL_API BOOL    JIT_STDCALL CloseHandle(HANDLE);

DLL_API FARPROC JIT_STDCALL GetProcAddress(
    HMODULE hModule,
    LPCSTR lpProcName
);

// --------------------------------------------------------------------
// user notification
// --------------------------------------------------------------------
DLL_API int JIT_STDCALL MessageBoxA(
    HANDLE hwnd,
    const char* text,
    const char* caption,
    unsigned int type
);

// --------------------------------------------------------------------
// resources ...
// --------------------------------------------------------------------
DLL_API HGLOBAL JIT_STDCALL LoadResource(
    HMODULE hModule,
    HRSRC   hResInfo
);
DLL_API HRSRC JIT_STDCALL FindResourceA(
    HMODULE hModule,
    LPCSTR  lpName,
    LPCSTR  lpType
);
DLL_API DWORD JIT_STDCALL SizeofResource(
    HMODULE hModule,
    HRSRC   hResInfo
);
DLL_API LPVOID JIT_STDCALL LockResource(
    HGLOBAL hResData
);

// --------------------------------------------------------------------
// memory
// --------------------------------------------------------------------
DLL_API HANDLE JIT_STDCALL GetProcessHeap(void);
DLL_API VOID   JIT_STDCALL RtlZeroMemory(
    PVOID  Destination,
    SIZE_T Length
);
DLL_API LPVOID JIT_STDCALL HeapAlloc(
    HANDLE hHeap,
    DWORD  dwFlags,
    SIZE_T dwBytes
);
DLL_API BOOL JIT_STDCALL HeapFree(
    HANDLE hHeap,
    DWORD  dwFlags,
    LPVOID lpMem
);

// --------------------------------------------------------------------
// temporary file stuff ...
// --------------------------------------------------------------------
DLL_API DWORD JIT_STDCALL GetTempPathA(
    DWORD nBufferLength,
    LPSTR lpBuffer
);
DLL_API UINT  JIT_STDCALL GetTempFileNameA(
    LPCSTR lpPathName,
    LPCSTR lpPrefixString,
    UINT   uUnique,
    LPSTR  lpTempFileName
);

// --------------------------------------------------------------------
// disk information's ...
// --------------------------------------------------------------------
DLL_API UINT JIT_STDCALL GetDriveTypeA(const char *rootPath);
DLL_API BOOL JIT_STDCALL GetDiskFreeSpaceExA(
    LPCSTR,
    PULARGE_INTEGER,
    PULARGE_INTEGER,
    PULARGE_INTEGER
);
DLL_API BOOL JIT_STDCALL GetDiskFreeSpaceA(
    LPCSTR  lpRootPathName,
    LPDWORD lpSectorsPerCluster,
    LPDWORD lpBytesPerSector,
    LPDWORD lpNumberOfFreeClusters,
    LPDWORD lpTotalNumberOfClusters
);
DLL_API BOOL JIT_STDCALL GetVolumeInformationA(
    LPCSTR  lpRootPathName,
    LPSTR   lpVolumeNameBuffer,
    DWORD   nVolumeNameSize,
    LPDWORD lpVolumeSerialNumber,
    LPDWORD lpMaximumComponentLength,
    LPDWORD lpFileSystemFlags,
    LPSTR   lpFileSystemNameBuffer,
    DWORD   nFileSystemNameSize
);

DLL_API DWORD JIT_STDCALL WNetGetConnectionA(
    LPCSTR  lpLocalName,
    LPSTR   lpRemoteName,
    LPDWORD lpnLength
);
};

#endif
