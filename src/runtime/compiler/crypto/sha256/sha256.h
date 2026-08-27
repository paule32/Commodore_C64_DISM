// ---------------------------------------------------------------------------
// File: sha256.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_SHA256_H__
#define __DBASE2MANY_SHA256_H__

# pragma once
# include "stddef.h"

typedef struct SHA256_CTX {
    uint32_t state[8];
    uint64_t bit_count;
    uint8_t  buffer[64];
}   SHA256_CTX;

extern "C" {
DLL_API VOID sha256_init  (SHA256_CTX *ctx);
DLL_API VOID sha256_update(SHA256_CTX *ctx, const void *data, size_t len);
DLL_API VOID sha256_final (SHA256_CTX *ctx, uint8_t digest[32]);

DLL_API char* _jit_sha256(char *str, int len);
};

#endif
