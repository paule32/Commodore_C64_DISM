// ---------------------------------------------------------------------------
// File: crc32.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_CRC32_H__
#define __DBASE2MANY_CRC32_H__

# pragma once
# include "stddef.h"

typedef struct CRC32_CTX {
    uint32_t crc;
}   CRC32_CTX;

extern "C" {
DLL_API VOID crc32_init  (CRC32_CTX *ctx);
DLL_API VOID crc32_update(CRC32_CTX *ctx, const void *data, size_t len);

uint32_t crc32_final(CRC32_CTX *ctx);
uint32_t crc32_calc(const void *data, size_t len);

DLL_API char* _jit_crc32(char *str, int len);
};

#endif
