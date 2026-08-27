// ---------------------------------------------------------------------------
// File: dll_inflate.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DLL_INFLATE_H__
#define __DLL_INFLATE_H__

# pragma once
# include "stddef.h"

#ifdef __cplusplus
extern "C" {
#endif

enum {
    DB_INFLATE_OK               = 0,
    DB_INFLATE_BAD_ARGUMENT     = -1,
    DB_INFLATE_BAD_ZLIB_HEADER  = -2,
    DB_INFLATE_NEED_DICTIONARY  = -3,
    DB_INFLATE_TRUNCATED        = -4,
    DB_INFLATE_BAD_BLOCK_TYPE   = -5,
    DB_INFLATE_BAD_HUFFMAN      = -6,
    DB_INFLATE_BAD_DISTANCE     = -7,
    DB_INFLATE_OUTPUT_OVERFLOW  = -8,
    DB_INFLATE_BAD_ADLER32      = -9
};

extern "C" int db_inflate_raw(
    const unsigned char *source,
    unsigned int source_size,
    unsigned char *destination,
    unsigned int destination_capacity,
    unsigned int *destination_size
);

extern "C" unsigned int db_crc32(
    const void *data,
    unsigned int size
);

/*
int db_inflate_raw(
    const uint8_t * source,
    size_t          source_size,
    uint8_t       * destination,
    size_t          destination_capacity,
    size_t        * destination_size
);

uint32_t db_crc32(
    const void * data,
    size_t       size
);
*/

#ifdef __cplusplus
}
#endif

#endif
