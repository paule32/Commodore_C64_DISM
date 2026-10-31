/* Stage 518: Native D64PK001 resource decoder (C ABI, x86/x64).
 * Copyright (c) 2026 dBase2Many contributors.
 * Caller's buffer owns the result; no Python runtime is required.
 */
#ifndef D64RESOURCE_H_INCLUDED
#define D64RESOURCE_H_INCLUDED
#include <stdint.h>
#if defined(_WIN32)
#include <windows.h>
#endif
#if defined(_WIN32)
# if defined(D64RESOURCE_BUILD)
#  define D64RES_API __declspec(dllexport)
# elif defined(D64RESOURCE_STATIC)
#  define D64RES_API
# else
#  define D64RES_API __declspec(dllimport)
# endif
# define D64RES_CALL __cdecl
#else
# define D64RES_API __attribute__((visibility("default")))
# define D64RES_CALL
#endif

#ifdef __cplusplus
extern "C" {
#endif

enum {
    D64RES_OK = 0,
    D64RES_BUFFER_TOO_SMALL = 1,
    D64RES_INVALID_ARGUMENT = -1,
    D64RES_INVALID_HEADER = -2,
    D64RES_TOO_LARGE = -3,
    D64RES_INFLATE_ERROR = -4,
    D64RES_CHECKSUM_ERROR = -5,
    D64RES_NOT_FOUND = -6,
    D64RES_WINDOWS_ERROR = -7
};

/* Native C layout is the same for x86 and x64 (all fixed-width fields).
 * On success, size is the uncompressed payload length (not record length).
 * `codepage` is the original 20127/65001/1200 or custom Windows codepage.
 */
typedef struct D64ResourceInfo {
    uint32_t struct_size;
    uint16_t original_type;
    uint16_t original_id;
    uint16_t language;
    uint16_t reserved;
    uint32_t codepage;
    uint32_t size;
    uint32_t crc32;
} D64ResourceInfo;

#define D64RES_PACKED_TYPE 0xF117u
#define D64RES_MAX_UNPACKED (128u * 1024u * 1024u)
#define D64RES_HEADER_SIZE 26u

/* Pure in-memory APIs (Windows and non-Windows). Inspect validates only the
 * record envelope, Decode validates zlib stream length/trailing bytes and CRC.
 * If output is NULL, Decode returns BUFFER_TOO_SMALL and fills *info.
 * In all cases set info->struct_size=sizeof(*info) before calling.
 */
D64RES_API int D64RES_CALL D64ResourceInspect(
    const void *record, uint32_t record_size, D64ResourceInfo *info);
D64RES_API int D64RES_CALL D64ResourceDecode(
    const void *record, uint32_t record_size, void *output,
    uint32_t output_capacity, D64ResourceInfo *info);

#if defined(_WIN32)
/* Look up by ORIGINAL type/id/language, even when the packer remapped the
 * record to an internal 0xF117 ID. If the item was left plain by the packer,
 * its unchanged bytes are copied. language=0 selects the first available
 * language; otherwise language is matched exactly. A caller-owned buffer is
 * required; BUFFER_TOO_SMALL permits a two-pass size-query/read.
 * module is a DLL loaded with LOAD_LIBRARY_AS_DATAFILE/AS_IMAGE_RESOURCE.
 */
D64RES_API int D64RES_CALL D64ResourceReadModuleW(
    HMODULE module, uint16_t original_type, uint16_t original_id,
    uint16_t language, void *output, uint32_t output_capacity,
    D64ResourceInfo *info);
#endif

#ifdef __cplusplus
}
#endif
#endif
