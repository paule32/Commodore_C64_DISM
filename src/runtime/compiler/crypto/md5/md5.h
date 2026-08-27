// ---------------------------------------------------------------------------
// File: md5.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_MD5_H__
#define __DBASE2MANY_MD5_H__

#pragma once
#include "stddef.h"

typedef struct MD5_CTX {
    uint32_t state[4];
    uint64_t bit_count;
    uint8_t  buffer[64];
}   MD5_CTX;

extern "C" {
DLL_API VOID _jit_md5_init   (MD5_CTX *ctx);
DLL_API VOID _jit_md5_update (MD5_CTX *ctx, const void *data, size_t len);
DLL_API VOID _jit_md5_final  (MD5_CTX *ctx, uint8_t digest[16]);

DLL_API char* _jit_md5(char *str, int v);
};

#endif
