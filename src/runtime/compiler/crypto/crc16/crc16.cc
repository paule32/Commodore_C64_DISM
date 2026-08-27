// ---------------------------------------------------------------------------
// File: crc16.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "iostream.h"
# include "crc16.h"
# include "memory.h"

DLL_API VOID
crc16_init(CRC16_CTX *ctx)
{
    ctx->crc = 0xffff;
}

DLL_API VOID
crc16_update(CRC16_CTX *ctx, const void *data, size_t len)
{
    const uint8_t *p = (const uint8_t *)data;

    while (len--) {
        ctx->crc ^= ((uint16_t)(*p++) << 8);

        for (int i = 0; i < 8; i++) {
            if (ctx->crc & 0x8000)
                ctx->crc = (uint16_t)((ctx->crc << 1) ^ 0x1021);
            else
                ctx->crc = (uint16_t)(ctx->crc << 1);
        }
    }
}

uint16_t crc16_final(CRC16_CTX *ctx)
{
    return ctx->crc;
}

uint16_t crc16_calc(const void *data, size_t len)
{
    CRC16_CTX ctx;

    crc16_init(&ctx);
    crc16_update(&ctx, data, len);

    return crc16_final(&ctx);
}

DLL_API char*
_jit_crc16(char *str, int len)
{
    uint16_t crc = crc16_calc(str, (size_t)len);

    char *result = (char*)_jit_malloc(5);
    if (result == nullptr)
        return nullptr;

    _jit_snprintf(result, 5, "%04x", (unsigned int)crc);

    return result;
}
