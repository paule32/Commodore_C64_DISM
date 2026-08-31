// ---------------------------------------------------------------------------
// File: dll_runtime_bindings.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "stddef.h"
# include "windows.h"
# include "dll_loader.h"
# include "dll_runtime_ordinals.h"

static PackedDllHandle runtime_handle;

extern "C" {

// Index zero remains unused.  Each NASM thunk jumps through the slot that
// has the same number as the DLL export ordinal.
void *dbm_runtime_proc_table[DBM_RUNTIME_MAX_ORDINAL + 1];

static void
clear_runtime_table(void)
{
    /*
     * Volatile verhindert, dass GCC diese Schleife durch einen
     * externen memset()-Aufruf ersetzt.
     *
     * Die Funktion läuft bereits vor dem Laden der Runtime-DLL.
     */
    void * volatile *table =
        dbm_runtime_proc_table;

    unsigned int ordinal;

    for (
        ordinal = 0;
        ordinal <= DBM_RUNTIME_MAX_ORDINAL;
        ++ordinal
    ) {
        table[ordinal] = nullptr;
    }
}

unsigned int check_ordinal(unsigned int ordinal)
{
    if (ordinal >= 1 && ordinal <= 3)
        return 1;

    if (ordinal == 16)
        return 1;

    if (ordinal >= 31 && ordinal <= 98)
        return 1;

    if (ordinal >= 129 && ordinal <= 144)
        return 1;

    if (ordinal >= 150 && ordinal <= 153)
        return 1;
    
    return 0;
}

BOOL
packed_runtime_init(void)
{
    HMODULE executable;
    unsigned int ordinal;

    clear_runtime_table();

    executable = GetModuleHandleA(
        nullptr
    );

    if (executable == nullptr) {
        return FALSE;
    }

    if (!packed_dll_load_resource(
        executable,
        101,
        &runtime_handle
    )) {
        return FALSE;
    }

    for (
        ordinal = 1;
        ordinal <= DBM_RUNTIME_MAX_ORDINAL;
        ++ordinal
    ) {
        if (!check_ordinal(ordinal)) {
            continue;
        }
        FARPROC address = GetProcAddress(
            runtime_handle.module,
            MAKEINTRESOURCEA(ordinal)
        );

        if (address == nullptr) {
            packed_dll_unload(
                &runtime_handle
            );

            clear_runtime_table();
            return FALSE;
        }

        dbm_runtime_proc_table[ordinal] = (void *)address;
    }

    return TRUE;
}

void
packed_runtime_shutdown(void)
{
    packed_dll_unload(
        &runtime_handle
    );

    clear_runtime_table();
}

} // extern "C"
