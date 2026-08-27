// ---------------------------------------------------------------------------
// File: sha1.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "stddef.h"
# include "memory.h"
# include "sha1.h"

#define SHA1_ROTL(x,n) (((x) << (n)) | ((x) >> (32 - (n))))

static void sha1_transform(uint32_t state[5], const uint8_t block[64])
{
    uint32_t w[80];
    uint32_t a, b, c, d, e, f, k, temp;

    for (int i = 0; i < 16; i++) {
        w[i] =
            ((uint32_t)block[i * 4 + 0] << 24) |
            ((uint32_t)block[i * 4 + 1] << 16) |
            ((uint32_t)block[i * 4 + 2] << 8)  |
            ((uint32_t)block[i * 4 + 3]);
    }

    for (int i = 16; i < 80; i++)
        w[i] = SHA1_ROTL(w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16], 1);

    a = state[0];
    b = state[1];
    c = state[2];
    d = state[3];
    e = state[4];

    for (int i = 0; i < 80; i++) {
        if (i < 20) {
            f = (b & c) | ((~b) & d);
            k = 0x5a827999;
        } else if (i < 40) {
            f = b ^ c ^ d;
            k = 0x6ed9eba1;
        } else if (i < 60) {
            f = (b & c) | (b & d) | (c & d);
            k = 0x8f1bbcdc;
        } else {
            f = b ^ c ^ d;
            k = 0xca62c1d6;
        }

        temp = SHA1_ROTL(a, 5) + f + e + k + w[i];
        e = d;
        d = c;
        c = SHA1_ROTL(b, 30);
        b = a;
        a = temp;
    }

    state[0] += a;
    state[1] += b;
    state[2] += c;
    state[3] += d;
    state[4] += e;
}

DLL_API VOID
sha1_init(SHA1_CTX *ctx)
{
    ctx->bit_count = 0;

    ctx->state[0] = 0x67452301;
    ctx->state[1] = 0xefcdab89;
    ctx->state[2] = 0x98badcfe;
    ctx->state[3] = 0x10325476;
    ctx->state[4] = 0xc3d2e1f0;
}

DLL_API VOID
sha1_update(SHA1_CTX *ctx, const void *data, size_t len)
{
    const uint8_t *input = (const uint8_t *)data;

    size_t index = (size_t)((ctx->bit_count >> 3) & 63);
    ctx->bit_count += ((uint64_t)len << 3);

    size_t part_len = 64 - index;
    size_t i = 0;

    if (len >= part_len) {
        _jit_memcpy(&ctx->buffer[index], input, part_len);
        sha1_transform(ctx->state, ctx->buffer);

        for (i = part_len; i + 63 < len; i += 64)
            sha1_transform(ctx->state, &input[i]);

        index = 0;
    }

    _jit_memcpy(&ctx->buffer[index], &input[i], len - i);
}

DLL_API VOID
sha1_final(SHA1_CTX *ctx, uint8_t digest[20])
{
    static const uint8_t padding[64] = { 0x80 };

    uint8_t bits[8];

    for (int i = 0; i < 8; i++)
        bits[7 - i] = (uint8_t)((ctx->bit_count >> (8 * i)) & 0xff);

    size_t index = (size_t)((ctx->bit_count >> 3) & 63);
    size_t pad_len = (index < 56) ? (56 - index) : (120 - index);

    sha1_update(ctx, padding, pad_len);
    sha1_update(ctx, bits, 8);

    for (int i = 0; i < 5; i++) {
        digest[i * 4 + 0] = (uint8_t)((ctx->state[i] >> 24) & 0xff);
        digest[i * 4 + 1] = (uint8_t)((ctx->state[i] >> 16) & 0xff);
        digest[i * 4 + 2] = (uint8_t)((ctx->state[i] >> 8)  & 0xff);
        digest[i * 4 + 3] = (uint8_t)( ctx->state[i]        & 0xff);
    }
}

static char *bytes_to_hex_alloc(const uint8_t *data, size_t len)
{
    static const char hex[] = "0123456789abcdef";
    char *result = (char*)_jit_malloc(len * 2 + 1);
    if (result == nullptr)
        return nullptr;

    for (size_t i = 0; i < len; i++) {
        result[i * 2 + 0] = hex[(data[i] >> 4) & 0x0F];
        result[i * 2 + 1] = hex[data[i] & 0x0F];
    }

    result[len * 2] = '\0';

    return result;
}

DLL_API char*
_jit_sha1(char *str, int len)
{
    SHA1_CTX ctx;
    uint8_t digest[20];

    sha1_init(&ctx);
    sha1_update(&ctx, str, (size_t)len);
    sha1_final(&ctx, digest);

    return bytes_to_hex_alloc(digest, sizeof(digest));
}
