// ---------------------------------------------------------------------------
// File: sha512.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_SHA512_H__
#define __DBASE2MANY_SHA512_H__

# pragma once
# include "stddef.h"

typedef struct SHA512_CTX {
    uint64_t state[8];
    uint64_t bit_count_high;
    uint64_t bit_count_low;
    uint8_t  buffer[128];
}   SHA512_CTX;

extern "C" {
DLL_API VOID sha512_init  (SHA512_CTX *ctx);
DLL_API VOID sha512_update(SHA512_CTX *ctx, const void *data, size_t len);
DLL_API VOID sha512_final (SHA512_CTX *ctx, uint8_t digest[64]);

DLL_API char* _jit_sha512(char *str, int len);
};

#endif
