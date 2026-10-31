/* Standalone Windows EXE example: use either the native decoder as a DLL
 * or link d64resource.c directly. The D64PK001 compression format is stable.
 * Build commands: see build_windows.sh and README.md.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>
#include "d64resource.h"

#ifdef D64_DYNAMIC_LOADER
typedef int (__cdecl *D64ReadFn)(HMODULE, uint16_t, uint16_t, uint16_t,
                                void *, uint32_t, D64ResourceInfo *);
#endif
int wmain(int argc, wchar_t **argv) {
    HMODULE resource_module;
    int status;
    uint16_t resource_type, resource_id;
    unsigned char *buffer;
    D64ResourceInfo info;
#ifdef D64_DYNAMIC_LOADER
    HMODULE decoder_module;
    D64ReadFn read_fn;
#endif
    if (argc != 4) {
        fwprintf(stderr, L"Usage: demo_win.exe resource.dll ORIGINAL_TYPE ORIGINAL_ID\n");
        return 2;
    }
    resource_type = (uint16_t)wcstoul(argv[2], NULL, 0);
    resource_id = (uint16_t)wcstoul(argv[3], NULL, 0);
    resource_module = LoadLibraryExW(argv[1], NULL,
         LOAD_LIBRARY_AS_DATAFILE | LOAD_LIBRARY_AS_IMAGE_RESOURCE);
    if (!resource_module) {
        fwprintf(stderr, L"LoadLibraryExW failed: %lu\n", GetLastError());
        return 3;
    }
#ifdef D64_DYNAMIC_LOADER
    decoder_module = LoadLibraryW(L"d64resource.dll");
    if (!decoder_module) {
        fwprintf(stderr, L"Decoder-DLL not found: %lu\n", GetLastError());
        FreeLibrary(resource_module);
        return 4;
    }
    read_fn = (D64ReadFn)GetProcAddress(decoder_module, "D64ResourceReadModuleW");
    if (!read_fn) {
        fwprintf(stderr, L"Decoder export not found\n");
        FreeLibrary(decoder_module);
        FreeLibrary(resource_module);
        return 5;
    }
#else
#define read_fn D64ResourceReadModuleW
#endif
    info.struct_size = sizeof(info);
    status = read_fn(resource_module, resource_type, resource_id, 0,
                     NULL, 0, &info);
    if (status != D64RES_BUFFER_TOO_SMALL) {
        fwprintf(stderr, L"Resource query failed: %d\n", status);
        goto failure;
    }
    buffer = (unsigned char *)malloc(info.size ? info.size : 1u);
    if (!buffer) goto failure;
    info.struct_size = sizeof(info);
    status = read_fn(resource_module, resource_type, resource_id, 0,
                     buffer, info.size, &info);
    if (status == D64RES_OK) {
        wprintf(L"Resource %u:%u, language=0x%04X, codepage=%lu, bytes=%lu\n",
                (unsigned)info.original_type, (unsigned)info.original_id,
                (unsigned)info.language, (unsigned long)info.codepage,
                (unsigned long)info.size);
        /* `buffer` now holds the original (decompressed) binary resource.
           Interpret it as D64STR01, UTF-8, RCDATA, etc. depending on type. */
    } else {
        fwprintf(stderr, L"Resource decode failed: %d\n", status);
    }
    free(buffer);
#ifdef D64_DYNAMIC_LOADER
    FreeLibrary(decoder_module);
#endif
    FreeLibrary(resource_module);
    return status == D64RES_OK ? 0 : 6;
failure:
#ifdef D64_DYNAMIC_LOADER
    FreeLibrary(decoder_module);
#endif
    FreeLibrary(resource_module);
    return 7;
}
