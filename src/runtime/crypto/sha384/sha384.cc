// ---------------------------------------------------------------------------
// File: sha384.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "stddef.h"
# include "memory.h"
# include "sha384.h"

#define ROTR64(x,n) (((x) >> (n)) | ((x) << (64 - (n))))
#define SHR64(x,n)  ((x) >> (n))

#define CH64(x,y,z)  (((x) & (y)) ^ (~(x) & (z)))
#define MAJ64(x,y,z) (((x) & (y)) ^ ((x) & (z)) ^ ((y) & (z)))

#define BSIG0_64(x) (ROTR64((x),28) ^ ROTR64((x),34) ^ ROTR64((x),39))
#define BSIG1_64(x) (ROTR64((x),14) ^ ROTR64((x),18) ^ ROTR64((x),41))
#define SSIG0_64(x) (ROTR64((x), 1) ^ ROTR64((x), 8) ^ SHR64((x), 7))
#define SSIG1_64(x) (ROTR64((x),19) ^ ROTR64((x),61) ^ SHR64((x), 6))

static const uint64_t sha384_k[80] = {
    0x428a2f98d728ae22ULL,0x7137449123ef65cdULL,
    0xb5c0fbcfec4d3b2fULL,0xe9b5dba58189dbbcULL,
    0x3956c25bf348b538ULL,0x59f111f1b605d019ULL,
    0x923f82a4af194f9bULL,0xab1c5ed5da6d8118ULL,
    0xd807aa98a3030242ULL,0x12835b0145706fbeULL,
    0x243185be4ee4b28cULL,0x550c7dc3d5ffb4e2ULL,
    0x72be5d74f27b896fULL,0x80deb1fe3b1696b1ULL,
    0x9bdc06a725c71235ULL,0xc19bf174cf692694ULL,
    0xe49b69c19ef14ad2ULL,0xefbe4786384f25e3ULL,
    0x0fc19dc68b8cd5b5ULL,0x240ca1cc77ac9c65ULL,
    0x2de92c6f592b0275ULL,0x4a7484aa6ea6e483ULL,
    0x5cb0a9dcbd41fbd4ULL,0x76f988da831153b5ULL,
    0x983e5152ee66dfabULL,0xa831c66d2db43210ULL,
    0xb00327c898fb213fULL,0xbf597fc7beef0ee4ULL,
    0xc6e00bf33da88fc2ULL,0xd5a79147930aa725ULL,
    0x06ca6351e003826fULL,0x142929670a0e6e70ULL,
    0x27b70a8546d22ffcULL,0x2e1b21385c26c926ULL,
    0x4d2c6dfc5ac42aedULL,0x53380d139d95b3dfULL,
    0x650a73548baf63deULL,0x766a0abb3c77b2a8ULL,
    0x81c2c92e47edaee6ULL,0x92722c851482353bULL,
    0xa2bfe8a14cf10364ULL,0xa81a664bbc423001ULL,
    0xc24b8b70d0f89791ULL,0xc76c51a30654be30ULL,
    0xd192e819d6ef5218ULL,0xd69906245565a910ULL,
    0xf40e35855771202aULL,0x106aa07032bbd1b8ULL,
    0x19a4c116b8d2d0c8ULL,0x1e376c085141ab53ULL,
    0x2748774cdf8eeb99ULL,0x34b0bcb5e19b48a8ULL,
    0x391c0cb3c5c95a63ULL,0x4ed8aa4ae3418acbULL,
    0x5b9cca4f7763e373ULL,0x682e6ff3d6b2b8a3ULL,
    0x748f82ee5defb2fcULL,0x78a5636f43172f60ULL,
    0x84c87814a1f0ab72ULL,0x8cc702081a6439ecULL,
    0x90befffa23631e28ULL,0xa4506cebde82bde9ULL,
    0xbef9a3f7b2c67915ULL,0xc67178f2e372532bULL,
    0xca273eceea26619cULL,0xd186b8c721c0c207ULL,
    0xeada7dd6cde0eb1eULL,0xf57d4f7fee6ed178ULL,
    0x06f067aa72176fbaULL,0x0a637dc5a2c898a6ULL,
    0x113f9804bef90daeULL,0x1b710b35131c471bULL,
    0x28db77f523047d84ULL,0x32caab7b40c72493ULL,
    0x3c9ebe0a15c9bebcULL,0x431d67c49c100d4cULL,
    0x4cc5d4becb3e42b6ULL,0x597f299cfc657e2aULL,
    0x5fcb6fab3ad6faecULL,0x6c44198c4a475817ULL
};

static uint64_t load_be64(const uint8_t *p)
{
    return ((uint64_t)p[0] << 56) |
           ((uint64_t)p[1] << 48) |
           ((uint64_t)p[2] << 40) |
           ((uint64_t)p[3] << 32) |
           ((uint64_t)p[4] << 24) |
           ((uint64_t)p[5] << 16) |
           ((uint64_t)p[6] << 8)  |
           ((uint64_t)p[7]);
}

static void store_be64(uint8_t *p, uint64_t v)
{
    p[0] = (uint8_t)(v >> 56);
    p[1] = (uint8_t)(v >> 48);
    p[2] = (uint8_t)(v >> 40);
    p[3] = (uint8_t)(v >> 32);
    p[4] = (uint8_t)(v >> 24);
    p[5] = (uint8_t)(v >> 16);
    p[6] = (uint8_t)(v >> 8);
    p[7] = (uint8_t)(v);
}

static void sha384_transform(uint64_t state[8], const uint8_t block[128])
{
    uint64_t w[80];
    uint64_t a,b,c,d,e,f,g,h;
    uint64_t t1,t2;

    for (int i = 0; i < 16; i++)
        w[i] = load_be64(block + i * 8);

    for (int i = 16; i < 80; i++)
        w[i] = SSIG1_64(w[i - 2]) + w[i - 7] + SSIG0_64(w[i - 15]) + w[i - 16];

    a = state[0];
    b = state[1];
    c = state[2];
    d = state[3];
    e = state[4];
    f = state[5];
    g = state[6];
    h = state[7];

    for (int i = 0; i < 80; i++) {
        t1 = h + BSIG1_64(e) + CH64(e,f,g) + sha384_k[i] + w[i];
        t2 = BSIG0_64(a) + MAJ64(a,b,c);

        h = g;
        g = f;
        f = e;
        e = d + t1;
        d = c;
        c = ROTR64(b, 2);
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
sha384_init(SHA384_CTX *ctx)
{
    ctx->bit_count_high = 0;
    ctx->bit_count_low  = 0;

    ctx->state[0] = 0xcbbb9d5dc1059ed8ULL;
    ctx->state[1] = 0x629a292a367cd507ULL;
    ctx->state[2] = 0x9159015a3070dd17ULL;
    ctx->state[3] = 0x152fecd8f70e5939ULL;
    ctx->state[4] = 0x67332667ffc00b31ULL;
    ctx->state[5] = 0x8eb44a8768581511ULL;
    ctx->state[6] = 0xdb0c2e0d64f98fa7ULL;
    ctx->state[7] = 0x47b5481dbefa4fa4ULL;
}

DLL_API VOID
sha384_update(SHA384_CTX *ctx, const void *data, size_t len)
{
    const uint8_t *input = (const uint8_t *)data;

    size_t index = (size_t)((ctx->bit_count_low >> 3) & 127);

    uint64_t bits = (uint64_t)len << 3;
    ctx->bit_count_low += bits;

    if (ctx->bit_count_low < bits)
        ctx->bit_count_high++;

    ctx->bit_count_high += ((uint64_t)len >> 61);

    size_t part_len = 128 - index;
    size_t i = 0;

    if (len >= part_len) {
        _jit_memcpy(&ctx->buffer[index], input, part_len);
        sha384_transform(ctx->state, ctx->buffer);

        for (i = part_len; i + 127 < len; i += 128)
            sha384_transform(ctx->state, &input[i]);

        index = 0;
    }

    _jit_memcpy(&ctx->buffer[index], &input[i], len - i);
}

DLL_API VOID
sha384_final(SHA384_CTX *ctx, uint8_t digest[48])
{
    static const uint8_t padding[128] = { 0x80 };
    uint8_t bits[16];

    store_be64(bits,     ctx->bit_count_high);
    store_be64(bits + 8, ctx->bit_count_low);

    size_t index = (size_t)((ctx->bit_count_low >> 3) & 127);
    size_t pad_len = (index < 112) ? (112 - index) : (240 - index);

    sha384_update(ctx, padding, pad_len);
    sha384_update(ctx, bits, 16);

    for (int i = 0; i < 6; i++)
        store_be64(digest + i * 8, ctx->state[i]);
}

DLL_API char*
_jit_sha384(char *str, int len)
{
    static const char hex[] = "0123456789abcdef";
    SHA384_CTX ctx;
    uint8_t digest[48];

    char *result = (char*)_jit_malloc(48 * 2 + 1);
    if (result == nullptr)
        return nullptr;

    sha384_init  (&ctx);
    sha384_update(&ctx, str, (size_t)len);
    sha384_final (&ctx, digest);

    for (int i = 0; i < 48; i++) {
        result[i * 2 + 0] = hex[(digest[i] >> 4) & 0x0f];
        result[i * 2 + 1] = hex[ digest[i]       & 0x0f];
    }
    
    result[48 * 2] = '\0';
    return result;
}
