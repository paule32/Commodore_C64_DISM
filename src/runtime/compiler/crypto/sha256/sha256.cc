// ---------------------------------------------------------------------------
// File: sha256.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "stddef.h"
# include "memory.h"
# include "sha256.h"

#define SHR(x,n)  ((x) >> (n))
#define ROTR(x,n) (((x) >> (n)) | ((x) << (32 - (n))))

#define CH(x,y,z)  (((x) & (y)) ^ (~(x) & (z)))
#define MAJ(x,y,z) (((x) & (y)) ^ ((x) & (z)) ^ ((y) & (z)))

#define BSIG0(x) (ROTR((x), 2) ^ ROTR((x),13) ^ ROTR((x),22))
#define BSIG1(x) (ROTR((x), 6) ^ ROTR((x),11) ^ ROTR((x),25))
#define SSIG0(x) (ROTR((x), 7) ^ ROTR((x),18) ^ SHR((x), 3))
#define SSIG1(x) (ROTR((x),17) ^ ROTR((x),19) ^ SHR((x),10))

static const uint32_t sha256_k[64] = {
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,
    0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,
    0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,
    0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,
    0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,
    0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,
    0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,
    0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,
    0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};

static void sha256_transform(uint32_t state[8], const uint8_t block[64])
{
    uint32_t w[64];
    uint32_t a,b,c,d,e,f,g,h;
    uint32_t t1,t2;

    for (int i = 0; i < 16; i++) {
        w[i] =
            ((uint32_t)block[i * 4 + 0] << 24) |
            ((uint32_t)block[i * 4 + 1] << 16) |
            ((uint32_t)block[i * 4 + 2] << 8)  |
            ((uint32_t)block[i * 4 + 3]);
    }

    for (int i = 16; i < 64; i++)
        w[i] = SSIG1(w[i - 2]) + w[i - 7] + SSIG0(w[i - 15]) + w[i - 16];

    a = state[0];
    b = state[1];
    c = state[2];
    d = state[3];
    e = state[4];
    f = state[5];
    g = state[6];
    h = state[7];

    for (int i = 0; i < 64; i++) {
        t1 = h + BSIG1(e) + CH(e,f,g) + sha256_k[i] + w[i];
        t2 = BSIG0(a) + MAJ(a,b,c);

        h = g;
        g = f;
        f = e;
        e = d + t1;
        d = c;
        c = b;
        b = a;
        a = t1 + t2;
    }

    state[0] += a;
    state[1] += b;
    state[2] += c;
    state[3] += d;
    state[4] += e;
    state[5] += f;
    state[6] += g;
    state[7] += h;
}

DLL_API VOID
sha256_init(SHA256_CTX *ctx)
{
    ctx->bit_count = 0;

    ctx->state[0] = 0x6a09e667;
    ctx->state[1] = 0xbb67ae85;
    ctx->state[2] = 0x3c6ef372;
    ctx->state[3] = 0xa54ff53a;
    ctx->state[4] = 0x510e527f;
    ctx->state[5] = 0x9b05688c;
    ctx->state[6] = 0x1f83d9ab;
    ctx->state[7] = 0x5be0cd19;
}

DLL_API VOID
sha256_update(SHA256_CTX *ctx, const void *data, size_t len)
{
    const uint8_t *input = (const uint8_t *)data;
    size_t index = (size_t)((ctx->bit_count >> 3) & 63);

    ctx->bit_count += ((uint64_t)len << 3);

    size_t part_len = 64 - index;
    size_t i = 0;

    if (len >= part_len) {
        _jit_memcpy(&ctx->buffer[index], input, part_len);
        sha256_transform(ctx->state, ctx->buffer);

        for (i = part_len; i + 63 < len; i += 64)
            sha256_transform(ctx->state, &input[i]);

        index = 0;
    }

    _jit_memcpy(&ctx->buffer[index], &input[i], len - i);
}

DLL_API VOID
sha256_final(SHA256_CTX *ctx, uint8_t digest[32])
{
    static const uint8_t padding[64] = { 0x80 };
    uint8_t bits[8];

    for (int i = 0; i < 8; i++)
        bits[7 - i] = (uint8_t)((ctx->bit_count >> (8 * i)) & 0xff);

    size_t index = (size_t)((ctx->bit_count >> 3) & 63);
    size_t pad_len = (index < 56) ? (56 - index) : (120 - index);

    sha256_update(ctx, padding, pad_len);
    sha256_update(ctx, bits, 8);

    for (int i = 0; i < 8; i++) {
        digest[i * 4 + 0] = (uint8_t)((ctx->state[i] >> 24) & 0xff);
        digest[i * 4 + 1] = (uint8_t)((ctx->state[i] >> 16) & 0xff);
        digest[i * 4 + 2] = (uint8_t)((ctx->state[i] >> 8)  & 0xff);
        digest[i * 4 + 3] = (uint8_t)( ctx->state[i]        & 0xff);
    }
}

DLL_API char*
_jit_sha256(char *str, int len)
{
    static const char hex[] = "0123456789abcdef";
    SHA256_CTX ctx;
    uint8_t digest[32];

    char *result = (char*)_jit_malloc(32 * 2 + 1);
    if (result == nullptr)
        return nullptr;

    sha256_init  (&ctx);
    sha256_update(&ctx, str, (size_t)len);
    sha256_final (&ctx, digest);

    for (int i = 0; i < 32; i++) {
        result[i * 2 + 0] = hex[(digest[i] >> 4) & 0x0f];
        result[i * 2 + 1] = hex[ digest[i]       & 0x0f];
    }
    
    result[32 * 2] = '\0';
    return result;
}
