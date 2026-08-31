// ---------------------------------------------------------------------------
// File: blake2.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "blake2.h"
# include "memory.h"

static const uint32_t blake2s_iv[8] = {
    0x6A09E667UL, 0xBB67AE85UL,
    0x3C6EF372UL, 0xA54FF53AUL,
    0x510E527FUL, 0x9B05688CUL,
    0x1F83D9ABUL, 0x5BE0CD19UL
};

static const uint8_t blake2s_sigma[10][16] = {
    { 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15 },
    {14,10, 4, 8, 9,15,13, 6, 1,12, 0, 2,11, 7, 5, 3 },
    {11, 8,12, 0, 5, 2,15,13,10,14, 3, 6, 7, 1, 9, 4 },
    { 7, 9, 3, 1,13,12,11,14, 2, 6, 5,10, 4, 0,15, 8 },
    { 9, 0, 5, 7, 2, 4,10,15,14, 1,11,12, 6, 8, 3,13 },
    { 2,12, 6,10, 0,11, 8, 3, 4,13, 7, 5,15,14, 1, 9 },
    {12, 5, 1,15,14,13, 4,10, 0, 7, 6, 3, 9, 2, 8,11 },
    {13,11, 7,14,12, 1, 3, 9, 5, 0,15, 4, 8, 6, 2,10 },
    { 6,15,14, 9,11, 3, 0, 8,12, 2,13, 7, 1, 4,10, 5 },
    {10, 2, 8, 4, 7, 6, 1, 5,15,11, 9,14, 3,12,13, 0 }
};

static uint32_t rotr32(uint32_t x, int n)
{
    return (x >> n) | (x << (32 - n));
}

static uint32_t load_le32(const uint8_t *p)
{
    return ((uint32_t)p[0]) |
           ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) |
           ((uint32_t)p[3] << 24);
}

static void store_le32(uint8_t *p, uint32_t v)
{
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
    p[2] = (uint8_t)(v >> 16);
    p[3] = (uint8_t)(v >> 24);
}

static void blake2s_increment_counter(BLAKE2S_CTX *ctx, uint32_t inc)
{
    ctx->t[0] += inc;

    if (ctx->t[0] < inc)
        ctx->t[1]++;
}

#define G(r,i,a,b,c,d)                                      \
    do {                                                    \
        a = a + b + m[blake2s_sigma[r][2 * i + 0]];          \
        d = rotr32(d ^ a, 16);                              \
        c = c + d;                                          \
        b = rotr32(b ^ c, 12);                              \
        a = a + b + m[blake2s_sigma[r][2 * i + 1]];          \
        d = rotr32(d ^ a, 8);                               \
        c = c + d;                                          \
        b = rotr32(b ^ c, 7);                               \
    } while (0)

#define ROUND(r)                                            \
    do {                                                    \
        G(r,0,v[0],v[4],v[ 8],v[12]);                       \
        G(r,1,v[1],v[5],v[ 9],v[13]);                       \
        G(r,2,v[2],v[6],v[10],v[14]);                       \
        G(r,3,v[3],v[7],v[11],v[15]);                       \
        G(r,4,v[0],v[5],v[10],v[15]);                       \
        G(r,5,v[1],v[6],v[11],v[12]);                       \
        G(r,6,v[2],v[7],v[ 8],v[13]);                       \
        G(r,7,v[3],v[4],v[ 9],v[14]);                       \
    } while (0)

static void blake2s_compress(BLAKE2S_CTX *ctx, const uint8_t block[64])
{
    uint32_t m[16];
    uint32_t v[16];

    for (int i = 0; i < 16; i++)
        m[i] = load_le32(block + i * 4);

    for (int i = 0; i < 8; i++)
        v[i] = ctx->h[i];

    for (int i = 0; i < 8; i++)
        v[i + 8] = blake2s_iv[i];

    v[12] ^= ctx->t[0];
    v[13] ^= ctx->t[1];
    v[14] ^= ctx->f[0];
    v[15] ^= ctx->f[1];

    ROUND(0);
    ROUND(1);
    ROUND(2);
    ROUND(3);
    ROUND(4);
    ROUND(5);
    ROUND(6);
    ROUND(7);
    ROUND(8);
    ROUND(9);

    for (int i = 0; i < 8; i++)
        ctx->h[i] ^= v[i] ^ v[i + 8];
}

DLL_API VOID
blake2s_init(BLAKE2S_CTX *ctx, size_t outlen)
{
    _jit_memset(ctx, 0, sizeof(*ctx));

    if (outlen == 0 || outlen > BLAKE2S_OUTBYTES)
        outlen = BLAKE2S_OUTBYTES;

    ctx->outlen = outlen;

    for (int i = 0; i < 8; i++)
        ctx->h[i] = blake2s_iv[i];

    ctx->h[0] ^= 0x01010000 ^ (uint32_t)outlen;
}

DLL_API VOID
blake2s_update(BLAKE2S_CTX *ctx, const void *data, size_t len)
{
    const uint8_t *in = (const uint8_t *)data;

    while (len > 0) {
        size_t left = ctx->buflen;
        size_t fill = BLAKE2S_BLOCKBYTES - left;

        if (len > fill) {
            _jit_memcpy(ctx->buf + left, in, fill);
            ctx->buflen = 0;

            blake2s_increment_counter(ctx, BLAKE2S_BLOCKBYTES);
            blake2s_compress(ctx, ctx->buf);

            in  += fill;
            len -= fill;
        } else {
            _jit_memcpy(ctx->buf + left, in, len);
            ctx->buflen = left + len;
            return;
        }
    }
}

DLL_API VOID
blake2s_final(BLAKE2S_CTX *ctx, uint8_t *out)
{
    uint8_t buffer[BLAKE2S_OUTBYTES];

    blake2s_increment_counter(ctx, (uint32_t)ctx->buflen);

    ctx->f[0] = 0xFFFFFFFFUL;

    _jit_memset(ctx->buf + ctx->buflen, 0, BLAKE2S_BLOCKBYTES - ctx->buflen);

    blake2s_compress(ctx, ctx->buf);

    for (int i = 0; i < 8; i++)
        store_le32(buffer + i * 4, ctx->h[i]);

    _jit_memcpy(out, buffer, ctx->outlen);
}

void blake2s_calc(const void *data, size_t len, uint8_t out[32])
{
    BLAKE2S_CTX ctx;

    blake2s_init  (&ctx, 32);
    blake2s_update(&ctx, data, len);
    blake2s_final (&ctx, out);
}

DLL_API char*
_jit_blake2(char *text, int length)
{
    static char hex[65];
    uint8_t digest[32];

    blake2s_calc(text, (size_t)length, digest);

    for (int i = 0; i < 32; i++) {
        static const char h[] = "0123456789abcdef";
        hex[i * 2 + 0] = h[(digest[i] >> 4) & 15];
        hex[i * 2 + 1] = h[digest[i] & 15];
    }

    hex[64] = 0;
    return hex;
}
