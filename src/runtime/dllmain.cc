// ---------------------------------------------------------------------------
// File: dllmain.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "stddef.h"
# include "windows.h"

extern "C" int init_loader();

DLL_API BOOL JIT_STDCALL DllMain(
    HINSTANCE hinstDLL,
    DWORD fdwReason,
    LPVOID lpvReserved)
{
    if (fdwReason == DLL_PROCESS_ATTACH) {
        if (!init_loader())
            return FALSE;
    }
    return TRUE;
}

DLL_API BOOL JIT_STDCALL DllMainCRTStartup(
    HINSTANCE hinstDLL,
    DWORD fdwReason,
    LPVOID lpvReserved)
{
    return DllMain(hinstDLL, fdwReason, lpvReserved);
}
