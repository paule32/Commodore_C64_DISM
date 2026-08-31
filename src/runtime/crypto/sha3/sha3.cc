// ---------------------------------------------------------------------------
// File: sha3.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "stddef.h"
# include "memory.h"
# include "sha3.h"

#define ROTL64(x,n) (((x) << (n)) | ((x) >> (64 - (n))))

static const uint64_t keccakf_rndc[24] = {
    0x0000000000000001ULL,0x0000000000008082ULL,
    0x800000000000808aULL,0x8000000080008000ULL,
    0x000000000000808bULL,0x0000000080000001ULL,
    0x8000000080008081ULL,0x8000000000008009ULL,
    0x000000000000008aULL,0x0000000000000088ULL,
    0x0000000080008009ULL,0x000000008000000aULL,
    0x000000008000808bULL,0x800000000000008bULL,
    0x8000000000008089ULL,0x8000000000008003ULL,
    0x8000000000008002ULL,0x8000000000000080ULL,
    0x000000000000800aULL,0x800000008000000aULL,
    0x8000000080008081ULL,0x8000000000008080ULL,
    0x0000000080000001ULL,0x8000000080008008ULL
};

static const int keccakf_rotc[24] = {
     1,  3,  6, 10, 15, 21,
    28, 36, 45, 55,  2, 14,
    27, 41, 56,  8, 25, 43,
    62, 18, 39, 61, 20, 44
};

static const int keccakf_piln[24] = {
    10,  7, 11, 17, 18,  3,
     5, 16,  8, 21, 24,  4,
    15, 23, 19, 13, 12,  2,
    20, 14, 22,  9,  6,  1
};

static uint64_t load_le64(const uint8_t *p)
{
    return ((uint64_t)p[0])       |
           ((uint64_t)p[1] << 8)  |
           ((uint64_t)p[2] << 16) |
           ((uint64_t)p[3] << 24) |
           ((uint64_t)p[4] << 32) |
           ((uint64_t)p[5] << 40) |
           ((uint64_t)p[6] << 48) |
           ((uint64_t)p[7] << 56);
}

static void store_le64(uint8_t *p, uint64_t v)
{
    p[0] = (uint8_t)(v);
    p[1] = (uint8_t)(v >> 8);
    p[2] = (uint8_t)(v >> 16);
    p[3] = (uint8_t)(v >> 24);
    p[4] = (uint8_t)(v >> 32);
    p[5] = (uint8_t)(v >> 40);
    p[6] = (uint8_t)(v >> 48);
    p[7] = (uint8_t)(v >> 56);
}

static void keccakf(uint64_t st[25])
{
    uint64_t bc[5];
    uint64_t t;

    for (int round = 0; round < 24; round++) {
        for (int i = 0; i < 5; i++)
            bc[i] = st[i] ^ st[i + 5] ^ st[i + 10] ^ st[i + 15] ^ st[i + 20];

        for (int i = 0; i < 5; i++) {
            t = bc[(i + 4) % 5] ^ ROTL64(bc[(i + 1) % 5], 1);

            for (int j = 0; j < 25; j += 5)
                st[j + i] ^= t;
        }

        t = st[1];

        for (int i = 0; i < 24; i++) {
            int j = keccakf_piln[i];

            bc[0] = st[j];
            st[j] = ROTL64(t, keccakf_rotc[i]);
            t = bc[0];
        }

        for (int j = 0; j < 25; j += 5) {
            for (int i = 0; i < 5; i++)
                bc[i] = st[j + i];

            for (int i = 0; i < 5; i++)
                st[j + i] ^= (~bc[(i + 1) % 5]) & bc[(i + 2) % 5];
        }

        st[0] ^= keccakf_rndc[round];
    }
}

DLL_API VOID
sha3_init(SHA3_CTX *ctx, size_t rate, size_t digest_len)
{
    _jit_memset(ctx, 0, sizeof(*ctx));

    ctx->rate       = rate;
    ctx->digest_len = digest_len;
    ctx->pos        = 0;
}

DLL_API VOID
sha3_update(SHA3_CTX *ctx, const void *data, size_t len)
{
    const uint8_t *in = (const uint8_t *)data;

    while (len > 0) {
        size_t n = ctx->rate - ctx->pos;

        if (n > len)
            n = len;

        _jit_memcpy(ctx->buffer + ctx->pos, in, n);

        ctx->pos += n;
        in       += n;
        len      -= n;

        if (ctx->pos == ctx->rate) {
            for (size_t i = 0; i < ctx->rate / 8; i++)
                ctx->state[i] ^= load_le64(ctx->buffer + i * 8);

            keccakf(ctx->state);

            _jit_memset(ctx->buffer, 0, ctx->rate);
            ctx->pos = 0;
        }
    }
}

DLL_API VOID
sha3_final(SHA3_CTX *ctx, uint8_t *digest)
{
    ctx->buffer[ctx->pos] ^= 0x06;
    ctx->buffer[ctx->rate - 1] ^= 0x80;

    for (size_t i = 0; i < ctx->rate / 8; i++)
        ctx->state[i] ^= load_le64(ctx->buffer + i * 8);

    keccakf(ctx->state);

    uint8_t out[200];

    for (int i = 0; i < 25; i++)
        store_le64(out + i * 8, ctx->state[i]);

    _jit_memcpy(digest, out, ctx->digest_len);
}

DLL_API char*
_jit_sha3(char *str, int len)
{
    static const char hex[] = "0123456789abcdef";
    SHA3_CTX ctx;
    uint8_t digest[32];

    char *result = (char*)_jit_malloc(32 * 2 + 1);
    if (result == nullptr)
        return nullptr;

    sha3_init  (&ctx, 136, 32);
    sha3_update(&ctx, str, (size_t)len);
    sha3_final (&ctx, digest);

    for (int i = 0; i < 32; i++) {
        result[i * 2 + 0] = hex[(digest[i] >> 4) & 0x0f];
        result[i * 2 + 1] = hex[ digest[i]       & 0x0f];
    }

    result[32 * 2] = '\0';
    return result;
}
