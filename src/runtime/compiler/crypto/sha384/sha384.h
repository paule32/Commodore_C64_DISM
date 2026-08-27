// ---------------------------------------------------------------------------
// File: sha384.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_SHA384_H__
#define __DBASE2MANY_SHA384_H__

# pragma once
# include "stddef.h"

typedef struct SHA384_CTX {
    uint64_t state[8];
    uint64_t bit_count_high;
    uint64_t bit_count_low;
    uint8_t  buffer[128];
}   SHA384_CTX;

extern "C" {
DLL_API VOID sha384_init  (SHA384_CTX *ctx);
DLL_API VOID sha384_update(SHA384_CTX *ctx, const void *data, size_t len);
DLL_API VOID sha384_final (SHA384_CTX *ctx, uint8_t digest[48]);

DLL_API char* _jit_sha384(char *str, int len);
};

#endif
