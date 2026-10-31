/* Native D64PK001 decoder: no Python dependency, zlib/DEFLATE with CRC32.
 * Can be linked directly into an EXE or compiled as a DLL for x86 / x64.
 */
#include "d64resource.h"
#include <string.h>
#include <limits.h>
#include <zlib.h>

static uint16_t d64_u16(const unsigned char *p) {
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}
static uint32_t d64_u32(const unsigned char *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static int d64_info_valid(D64ResourceInfo *info) {
    return info && info->struct_size == (uint32_t)sizeof(D64ResourceInfo);
}
static int d64_parse(const void *record, uint32_t record_size, D64ResourceInfo *info) {
    const unsigned char *p = (const unsigned char *)record;
    if (!record || !d64_info_valid(info)) return D64RES_INVALID_ARGUMENT;
    if (record_size <= D64RES_HEADER_SIZE ||
        memcmp(p, "D64PK001", 8) != 0) return D64RES_INVALID_HEADER;
    info->original_type = d64_u16(p + 8);
    info->original_id = d64_u16(p + 10);
    info->language = d64_u16(p + 12);
    info->reserved = 0;
    info->codepage = d64_u32(p + 14);
    info->size = d64_u32(p + 18);
    info->crc32 = d64_u32(p + 22);
    if (info->size > D64RES_MAX_UNPACKED) return D64RES_TOO_LARGE;
    return D64RES_OK;
}
int D64RES_CALL D64ResourceInspect(
    const void *record, uint32_t record_size, D64ResourceInfo *info) {
    return d64_parse(record, record_size, info);
}
int D64RES_CALL D64ResourceDecode(
    const void *record, uint32_t record_size, void *output,
    uint32_t output_capacity, D64ResourceInfo *info) {
    z_stream stream;
    int zr, result = d64_parse(record, record_size, info);
    uint32_t consumed;
    uint32_t crc;
    if (result != D64RES_OK) return result;
    if (!output || output_capacity < info->size) return D64RES_BUFFER_TOO_SMALL;
    /* zlib's size/type may vary across ABIs; avoid any truncation. */
    if (sizeof(uInt) < sizeof(uint32_t) &&
        (record_size - D64RES_HEADER_SIZE > UINT_MAX || info->size > UINT_MAX))
        return D64RES_TOO_LARGE;
    memset(&stream, 0, sizeof(stream));
    stream.next_in = (Bytef *)((const unsigned char *)record + D64RES_HEADER_SIZE);
    stream.avail_in = (uInt)(record_size - D64RES_HEADER_SIZE);
    stream.next_out = (Bytef *)output;
    stream.avail_out = (uInt)info->size;
    zr = inflateInit(&stream);
    if (zr != Z_OK) return D64RES_INFLATE_ERROR;
    zr = inflate(&stream, Z_FINISH);
    consumed = (uint32_t)stream.total_in;
    if (zr != Z_STREAM_END || stream.total_out != info->size ||
        consumed != record_size - D64RES_HEADER_SIZE || stream.avail_in != 0) {
        result = D64RES_INFLATE_ERROR;
    } else {
        crc = (uint32_t)crc32(0L, Z_NULL, 0);
        crc = (uint32_t)crc32((uLong)crc, (const Bytef *)output, (uInt)info->size);
        if (crc != info->crc32) result = D64RES_CHECKSUM_ERROR;
    }
    inflateEnd(&stream);
    return result;
}

#if defined(_WIN32)
/* Windows-only module lookup: all state on the caller's stack (thread-safe). */
typedef struct D64FindContext {
    uint16_t original_type, original_id, language;
    const unsigned char *data;
    uint32_t length;
    D64ResourceInfo header;
} D64FindContext;

static BOOL d64_try_resource(HMODULE module, LPCWSTR type, LPCWSTR name,
                              WORD lang, D64FindContext *context) {
    HRSRC resource = FindResourceExW(module, type, name, lang);
    HGLOBAL loaded;
    const unsigned char *data;
    DWORD length;
    D64ResourceInfo info;
    if (!resource) return TRUE;
    length = SizeofResource(module, resource);
    loaded = LoadResource(module, resource);
    data = loaded ? (const unsigned char *)LockResource(loaded) : NULL;
    if (!data) return TRUE;
    memset(&info, 0, sizeof(info));
    info.struct_size = sizeof(info);
    if (D64ResourceInspect(data, length, &info) == D64RES_OK &&
        info.original_type == context->original_type &&
        info.original_id == context->original_id &&
        (context->language == 0 || info.language == context->language) &&
        info.language == lang) {
        context->data = data;
        context->length = length;
        context->header = info;
        return FALSE;
    }
    return TRUE;
}
static BOOL CALLBACK d64_lang_callback(HMODULE module, LPCWSTR type, LPCWSTR name,
                                      WORD lang, LONG_PTR param) {
    return d64_try_resource(module, type, name, lang, (D64FindContext *)param);
}
static BOOL CALLBACK d64_name_callback(HMODULE module, LPCWSTR type, LPWSTR name,
                                      LONG_PTR param) {
    D64FindContext *context = (D64FindContext *)param;
    if (!IS_INTRESOURCE(name)) return TRUE;
    if (context->language) {
        return d64_try_resource(module, type, name, context->language, context);
    }
    EnumResourceLanguagesW(module, type, name, d64_lang_callback, param);
    return context->data == NULL;
}
static BOOL CALLBACK d64_plain_lang_callback(HMODULE module, LPCWSTR type,
                                             LPCWSTR name, WORD lang, LONG_PTR param) {
    D64FindContext *context = (D64FindContext *)param;
    HRSRC res = FindResourceExW(module, type, name, lang);
    HGLOBAL handle;
    if (!res) return TRUE;
    handle = LoadResource(module, res);
    if (!handle) return TRUE;
    context->data = (const unsigned char *)LockResource(handle);
    context->length = SizeofResource(module, res);
    context->header.language = lang;
    return !context->data;
}
int D64RES_CALL D64ResourceReadModuleW(
    HMODULE module, uint16_t original_type, uint16_t original_id,
    uint16_t language, void *output, uint32_t output_capacity,
    D64ResourceInfo *info) {
    D64FindContext context;
    LPCWSTR type, name;
    int result;
    if (!module || !d64_info_valid(info)) return D64RES_INVALID_ARGUMENT;
    if (original_type == D64RES_PACKED_TYPE) return D64RES_INVALID_ARGUMENT;
    type = MAKEINTRESOURCEW(original_type);
    name = MAKEINTRESOURCEW(original_id);
    memset(&context, 0, sizeof(context));
    context.original_type = original_type;
    context.original_id = original_id;
    context.language = language;
    context.header.struct_size = sizeof(D64ResourceInfo);
    /* Native/plain resources are left unchanged by Stage 517. */
    if (language) {
        d64_plain_lang_callback(module, type, name, language, (LONG_PTR)&context);
    } else {
        EnumResourceLanguagesW(module, type, name, d64_plain_lang_callback,
                               (LONG_PTR)&context);
    }
    if (context.data) {
        uint32_t size = context.length;
        info->struct_size = sizeof(*info);
        info->original_type = original_type;
        info->original_id = original_id;
        info->language = context.header.language;
        info->reserved = 0;
        info->codepage = 0; /* Not present in Win32 resource directory. */
        info->size = size;
        info->crc32 = 0;
        if (!output || output_capacity < size) return D64RES_BUFFER_TOO_SMALL;
        if (size) memcpy(output, context.data, size);
        return D64RES_OK;
    }
    /* Compressed entries use a packer-generated ID under type 0xF117.
       Search by *original* type and ID; no Python-generated index needed. */
    EnumResourceNamesW(module, MAKEINTRESOURCEW(D64RES_PACKED_TYPE),
                       d64_name_callback, (LONG_PTR)&context);
    if (!context.data) return D64RES_NOT_FOUND;
    result = D64ResourceDecode(context.data, context.length, output,
                               output_capacity, info);
    return result;
}
#endif
