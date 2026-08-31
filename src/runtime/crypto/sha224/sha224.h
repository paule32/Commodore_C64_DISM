// ---------------------------------------------------------------------------
// File: sha224.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_SHA224_H__
#define __DBASE2MANY_SHA224_H__

# pragma once
# include "stddef.h"

typedef struct SHA224_CTX {
    uint32_t state[8];
    uint64_t bit_count;
    uint8_t  buffer[64];
}   SHA224_CTX;

extern "C" {
DLL_API VOID sha224_init  (SHA224_CTX *ctx);
DLL_API VOID sha224_update(SHA224_CTX *ctx, const void *data, size_t len);
DLL_API VOID sha224_final (SHA224_CTX *ctx, uint8_t digest[28]);

DLL_API char* _jit_sha224(char *str, int len);
};

#endif
