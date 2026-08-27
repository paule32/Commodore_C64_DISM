// ---------------------------------------------------------------------------
// File: packed_dll_test.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "stddef.h"
# include "windows.h"
# include "packed_dll_loader.h"

# define IDR_DBASE2MANY_RUNTIME 101

typedef void (__cdecl *JitPrintIntProc)(int value);

extern "C" DLL_API int  JIT_CDECL printf(const char *format, ...);

int
mainCRTStartup(void)
{
    PackedDllHandle runtime;
    JitPrintIntProc print_int;

    if (!packed_dll_load_resource(
        GetModuleHandleA(nullptr),
        IDR_DBASE2MANY_RUNTIME,
        &runtime
    ))  {
        printf(
            "Runtime konnte nicht geladen werden: %lu\n",
            (unsigned long)GetLastError()
        );
        return 1;
    }

    /*
     * Aktuelle DEF-Zuordnung:
     * _jit_print_int = Ordinal 46
     */
    print_int = (JitPrintIntProc)GetProcAddress(
        runtime.module,
        MAKEINTRESOURCEA(46)
    );

    if (print_int == nullptr) {
        printf(
            "Ordinal 46 wurde nicht gefunden: %lu\n",
            (unsigned long)GetLastError()
        );
        packed_dll_unload(&runtime);
        return 2;
    }

    print_int(1234);
    packed_dll_unload(&runtime);
    return 0;
}
