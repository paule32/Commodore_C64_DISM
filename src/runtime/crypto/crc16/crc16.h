// ---------------------------------------------------------------------------
// File: CRC16.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_CRC16_H__
#define __DBASE2MANY_CRC16_H__

# pragma once
# include "stddef.h"

typedef struct CRC16_CTX {
    uint16_t crc;
}   CRC16_CTX;

extern "C" {
DLL_API VOID crc16_init  (CRC16_CTX *ctx);
DLL_API VOID crc16_update(CRC16_CTX *ctx, const void *data, size_t len);

uint16_t crc16_final(CRC16_CTX *ctx);
uint16_t crc16_calc(const void *data, size_t len);

DLL_API char* _jit_crc16(char *str, int len);
};

#endif
