// ---------------------------------------------------------------------------
// File: crc32c.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_CRC32C_H__
#define __DBASE2MANY_CRC32C_H__

# pragma once
# include "stddef.h"

typedef struct CRC32C_CTX
{
    uint32_t crc;
}   CRC32C_CTX;

extern "C" {
DLL_API VOID crc32c_init  (CRC32C_CTX *ctx);
DLL_API VOID crc32c_update(CRC32C_CTX *ctx, const void *data, size_t len);

uint32_t crc32c_final(CRC32C_CTX *ctx);
uint32_t crc32c_calc(const void *data, size_t len);

DLL_API char* _jit_crc32c(char *str, int len);
};

#endif
