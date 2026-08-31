// ---------------------------------------------------------------------------
// File: crc32c.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "iostream.h"
# include "crc32c.h"
# include "memory.h"

static uint32_t crc32c_table[256];
static int crc32c_initialized = 0;

static void crc32c_build_table(void)
{
    for (uint32_t i = 0; i < 256; i++)
    {
        uint32_t crc = i;

        for (int j = 0; j < 8; j++)
        {
            if (crc & 1)
                crc = (crc >> 1) ^ 0x82F63B78UL;
            else
                crc >>= 1;
        }

        crc32c_table[i] = crc;
    }

    crc32c_initialized = 1;
}

DLL_API VOID
crc32c_init(CRC32C_CTX *ctx)
{
    if (!crc32c_initialized)
        crc32c_build_table();

    ctx->crc = 0xFFFFFFFFUL;
}

DLL_API VOID
crc32c_update(CRC32C_CTX *ctx,
                   const void *data,
                   size_t len)
{
    const uint8_t *p = (const uint8_t *)data;

    while (len--)
    {
        ctx->crc =
            crc32c_table[(ctx->crc ^ *p++) & 0xFF] ^
            (ctx->crc >> 8);
    }
}

uint32_t crc32c_final(CRC32C_CTX *ctx)
{
    return ctx->crc ^ 0xFFFFFFFFUL;
}

uint32_t crc32c_calc(const void *data,
                     size_t len)
{
    CRC32C_CTX ctx;

    crc32c_init(&ctx);
    crc32c_update(&ctx, data, len);

    return crc32c_final(&ctx);
}

DLL_API char*
_jit_crc32c(char *str, int len)
{
    uint32_t crc = crc32c_calc(str, (size_t)len);

    char *result = (char*)_jit_malloc(9);
    if (result == nullptr)
        return nullptr;

    _jit_snprintf(
        result,
        9,
        "%08x",
        (unsigned long long)crc
    );

    return result;
}
