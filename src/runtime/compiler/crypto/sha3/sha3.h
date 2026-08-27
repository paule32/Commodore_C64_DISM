// ---------------------------------------------------------------------------
// File: sha3.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_SHA3_H__
#define __DBASE2MANY_SHA3_H__

# pragma once
# include "stddef.h"

typedef struct SHA3_CTX {
    uint64_t state[25];
    uint8_t  buffer[200];
    size_t   rate;
    size_t   pos;
    size_t   digest_len;
}   SHA3_CTX;

extern "C" {
DLL_API VOID sha3_init  (SHA3_CTX *ctx, size_t rate, size_t digest_len);
DLL_API VOID sha3_update(SHA3_CTX *ctx, const void *data, size_t len);
DLL_API VOID sha3_final (SHA3_CTX *ctx, uint8_t *digest);

DLL_API char* _jit_sha3(char *str, int len);
};

#endif
