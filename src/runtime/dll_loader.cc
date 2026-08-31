// ---------------------------------------------------------------------------
// File: packed_dll_loader.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#include "dll_loader.h"

# include "stddef.h"
# include "string.h"
# include "dll_inflate.h"
# include "windows.h"

#define DBDLLZ_VERSION 1u

typedef struct PackedDllHeader {
    unsigned char magic[8];
    uint32_t      version;
    uint32_t      original_size;
    uint32_t      compressed_size;
    uint32_t      crc32_value;
    
}   PackedDllHeader;

static const unsigned char DBDLLZ_MAGIC[8] = {
    'D', 'B', 'D', 'L', 'L', 'Z', '1', '\0'
};

/* Local volatile clear; no Windows helper import is required. */
static void secure_zero_memory(
    void  *memory,
    SIZE_T size
) {
    volatile unsigned char *cursor;

    cursor = (volatile unsigned char *)memory;

    while (size > 0) {
        *cursor++ = 0;
        --size;
    }
}

static int
memory_equal(
    const unsigned char *left,
    const unsigned char *right,
    SIZE_T               size
) {
    while (size > 0) {
        if (*left++ != *right++) {
            return 0;
        }

        --size;
    }

    return 1;
}

static BOOL write_all(
    HANDLE               file,
    const unsigned char *data,
    DWORD                size
) {
    DWORD offset = 0;

    while (offset < size) {
        DWORD written = 0;

        if (!WriteFile(
            file,
            data + offset,
            size - offset,
            &written,
            nullptr
        )) {
            return FALSE;
        }

        if (written == 0) {
            SetLastError(ERROR_WRITE_FAULT);
            return FALSE;
        }

        offset += written;
    }

    return TRUE;
}

static BOOL create_temporary_dll(
    const unsigned char *image,
    DWORD                image_size,
    char                *path,
    DWORD                path_capacity
) {
    char temp_directory[MAX_PATH];
    char temp_name[MAX_PATH];
    DWORD directory_length;
    HANDLE file;
    BOOL ok;

    if (path == nullptr || path_capacity < MAX_PATH) {
        SetLastError(ERROR_INSUFFICIENT_BUFFER);
        return FALSE;
    }

    directory_length = GetTempPathA(
        MAX_PATH,
        temp_directory
    );

    if (
        directory_length == 0 ||
        directory_length >= MAX_PATH
    ) {
        return FALSE;
    }

    if (GetTempFileNameA(
        temp_directory,
        "dbm",
        0,
        temp_name
    ) == 0) {
        return FALSE;
    }

    file = CreateFileA(
        temp_name,
        GENERIC_WRITE,
        0,
        nullptr,
        CREATE_ALWAYS,
        FILE_ATTRIBUTE_TEMPORARY,
        nullptr
    );

    if (file == INVALID_HANDLE_VALUE) {
        DeleteFileA(temp_name);
        return FALSE;
    }

    ok = write_all(
        file,
        image,
        image_size
    );

    if (!CloseHandle(file)) {
        ok = FALSE;
    }

    if (!ok) {
        DWORD error = GetLastError();
        DeleteFileA(temp_name);
        SetLastError(error);
        return FALSE;
    }

    lstrcpynA(
        path,
        temp_name,
        (int)path_capacity
    );

    return TRUE;
}

BOOL packed_dll_load_resource(
    HMODULE          resource_module,
    int              resource_id,
    PackedDllHandle *result
) {
    HRSRC resource;
    HGLOBAL loaded_resource;
    const unsigned char *blob;
    DWORD blob_size;
    const PackedDllHeader *header;
    const unsigned char *compressed;
    unsigned char *image;
    HANDLE heap;
    size_t output_size;
    int inflate_result;
    uint32_t actual_crc;
    HMODULE module;

    if (result == nullptr) {
        SetLastError(ERROR_INVALID_PARAMETER);
        return FALSE;
    }

    secure_zero_memory(
        result,
        sizeof(*result)
    );

    resource = FindResourceA(
        resource_module,
        MAKEINTRESOURCEA(resource_id),
        RT_RCDATA
    );

    if (resource == nullptr) {
        return FALSE;
    }

    blob_size = SizeofResource(
        resource_module,
        resource
    );

    if (blob_size < sizeof(PackedDllHeader)) {
        SetLastError(ERROR_BAD_FORMAT);
        return FALSE;
    }

    loaded_resource = LoadResource(
        resource_module,
        resource
    );

    if (loaded_resource == nullptr) {
        return FALSE;
    }

    blob = (const unsigned char *)LockResource(
        loaded_resource
    );

    if (blob == nullptr) {
        SetLastError(ERROR_BAD_FORMAT);
        return FALSE;
    }

    header = (const PackedDllHeader *)blob;

    if (
        !memory_equal(
            header->magic,
            DBDLLZ_MAGIC,
            sizeof(DBDLLZ_MAGIC)
        ) ||
        header->version != DBDLLZ_VERSION
    ) {
        SetLastError(ERROR_BAD_FORMAT);
        return FALSE;
    }

    if (
        header->original_size == 0 ||
        header->compressed_size == 0 ||
        header->compressed_size >
            blob_size - sizeof(PackedDllHeader)
    ) {
        SetLastError(ERROR_BAD_FORMAT);
        return FALSE;
    }

    compressed = blob + sizeof(PackedDllHeader);
    heap = GetProcessHeap();

    image = (unsigned char *)HeapAlloc(
        heap,
        0,
        header->original_size
    );

    if (image == nullptr) {
        SetLastError(ERROR_NOT_ENOUGH_MEMORY);
        return FALSE;
    }

    output_size = 0;

    inflate_result = db_inflate_raw(
        compressed,
        header->compressed_size,
        image,
        header->original_size,
        &output_size
    );

    if (
        inflate_result != DB_INFLATE_OK ||
        output_size != header->original_size
    ) {
        HeapFree(heap, 0, image);
        SetLastError(ERROR_BAD_COMPRESSION_BUFFER);
        return FALSE;
    }

    actual_crc = db_crc32(
        image,
        header->original_size
    );

    if (
        (uint32_t)actual_crc !=
        header->crc32_value
    ) {
        HeapFree(heap, 0, image);
        SetLastError(ERROR_CRC);
        return FALSE;
    }

    if (!create_temporary_dll(
        image,
        header->original_size,
        result->temporary_file,
        MAX_PATH
    )) {
        DWORD error = GetLastError();
        HeapFree(heap, 0, image);
        SetLastError(error);
        return FALSE;
    }

    secure_zero_memory(
        image,
        header->original_size
    );

    HeapFree(
        heap,
        0,
        image
    );

    module = LoadLibraryA(
        result->temporary_file
    );

    if (module == nullptr) {
        DWORD error = GetLastError();
        DeleteFileA(result->temporary_file);
        secure_zero_memory(
            result,
            sizeof(*result)
        );
        SetLastError(error);
        return FALSE;
    }

    result->module = module;
    return TRUE;
}

void packed_dll_unload(
    PackedDllHandle *handle
) {
    if (handle == nullptr) {
        return;
    }

    if (handle->module != nullptr) {
        FreeLibrary(
            handle->module
        );

        handle->module = nullptr;
    }

    if (handle->temporary_file[0] != '\0') {
        DeleteFileA(
            handle->temporary_file
        );

        handle->temporary_file[0] = '\0';
    }
}
