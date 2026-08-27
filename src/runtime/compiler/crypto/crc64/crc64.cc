// ---------------------------------------------------------------------------
// File: crc64.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "iostream.h"
# include "crc64.h"
# include "memory.h"

#define CRC64_POLY 0x42F0E1EBA9EA3693ULL

DLL_API VOID
crc64_init(CRC64_CTX *ctx)
{
    ctx->crc = 0x0000000000000000ULL;
}

DLL_API VOID
crc64_update(CRC64_CTX *ctx, const void *data, size_t len)
{
    const uint8_t *p = (const uint8_t *)data;

    while (len--)
    {
        ctx->crc ^= ((uint64_t)(*p++) << 56);

        for (int i = 0; i < 8; i++)
        {
            if (ctx->crc & 0x8000000000000000ULL)
                ctx->crc = (ctx->crc << 1) ^ CRC64_POLY;
            else
                ctx->crc <<= 1;
        }
    }
}

uint64_t crc64_final(CRC64_CTX *ctx)
{
    return ctx->crc;
}

uint64_t crc64_calc(const void *data, size_t len)
{
    CRC64_CTX ctx;

    crc64_init(&ctx);
    crc64_update(&ctx, data, len);

    return crc64_final(&ctx);
}

DLL_API char*
_jit_crc64(char *str, int len)
{
    uint64_t crc = crc64_calc(str, (size_t)len);

    char *result = (char*)_jit_malloc(17);
    if (result == nullptr)
        return nullptr;

    _jit_snprintf(
        result,
        17,
        "%016llX",
        (unsigned long long)crc
    );

    return result;
}
