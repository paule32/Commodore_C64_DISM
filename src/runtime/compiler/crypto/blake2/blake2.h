// ---------------------------------------------------------------------------
// File: blake2.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_BLAKE2_H__
#define __DBASE2MANY_BLAKE2_H__

# pragma once
# include "stddef.h"

#define BLAKE2S_OUTBYTES 32
#define BLAKE2S_BLOCKBYTES 64

typedef struct BLAKE2S_CTX {
    uint32_t h[8];
    uint32_t t[2];
    uint32_t f[2];
    uint8_t  buf[BLAKE2S_BLOCKBYTES];
    size_t   buflen;
    size_t   outlen;
}   BLAKE2S_CTX;

extern "C" {
DLL_API VOID blake2s_init  (BLAKE2S_CTX *ctx, size_t outlen);
DLL_API VOID blake2s_update(BLAKE2S_CTX *ctx, const void *data, size_t len);
DLL_API VOID blake2s_final (BLAKE2S_CTX *ctx, uint8_t *out);

void blake2s_calc(const void *data, size_t len, uint8_t out[32]);

DLL_API char* _jit_blake2(char *str, int len);
};

#endif
