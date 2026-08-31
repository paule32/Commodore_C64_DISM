// ---------------------------------------------------------------------------
// File: crc64.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_CRC64_H__
#define __DBASE2MANY_CRC64_H__

# pragma once
# include "stddef.h"

typedef struct CRC64_CTX
{
    uint64_t crc;
}   CRC64_CTX;

extern "C" {
DLL_API VOID crc64_init  (CRC64_CTX *ctx);
DLL_API VOID crc64_update(CRC64_CTX *ctx, const void *data, size_t len);

uint64_t crc64_final(CRC64_CTX *ctx);
uint64_t crc64_calc(const void *data, size_t len);

DLL_API char* _jit_crc64(char *str, int len);
};

#endif
