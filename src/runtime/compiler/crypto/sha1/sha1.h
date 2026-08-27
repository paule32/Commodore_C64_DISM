// ---------------------------------------------------------------------------
// File: sha1.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_SHA1_H__
#define __DBASE2MANY_SHA1_H__

# pragma once
# include "stddef.h"

typedef struct SHA1_CTX {
    uint32_t state[5];
    uint64_t bit_count;
    uint8_t  buffer[64];
}   SHA1_CTX;

extern "C" {
DLL_API VOID sha1_init  (SHA1_CTX *ctx);
DLL_API VOID sha1_update(SHA1_CTX *ctx, const void *data, size_t len);
DLL_API VOID sha1_final (SHA1_CTX *ctx, uint8_t digest[20]);

DLL_API char* _jit_sha1(char *str, int len);
};

#endif
