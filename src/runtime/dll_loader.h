// ---------------------------------------------------------------------------
// File: packed_dll_loader.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef DBASE2MANY_PACKED_DLL_LOADER_H
#define DBASE2MANY_PACKED_DLL_LOADER_H

# pragma once

# include "stddef.h"
# include "windows.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct PackedDllHandle {
    HMODULE module;
    char    temporary_file[MAX_PATH];
    
}   PackedDllHandle;

// ---------------------------------------------------------------------------
// Loads a DBDLLZ1 blob embedded as RCDATA.
//
// Returns TRUE on success. On failure, GetLastError() contains a Win32
// error code where possible.
// ---------------------------------------------------------------------------
BOOL packed_dll_load_resource(
    HMODULE          resource_module,
    int              resource_id,
    PackedDllHandle *result
);

// ---------------------------------------------------------------------------
// Frees the module and removes the temporary backing file.
// ---------------------------------------------------------------------------
void packed_dll_unload(PackedDllHandle *handle);

#ifdef __cplusplus
}
#endif

#endif
