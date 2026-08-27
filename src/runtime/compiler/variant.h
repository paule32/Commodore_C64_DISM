// ---------------------------------------------------------------------------
// File: variant.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_VARIANT_HH__
#define __DBASE2MANY_VARIANT_HH__

# pragma once

# include "stddef.h"

# ifdef __cplusplus
extern "C" {
# endif

typedef enum JitVariantKind
{
    JIT_VARIANT_EMPTY   = 0,
    JIT_VARIANT_INTEGER = 1,
    JIT_VARIANT_BOOLEAN = 2,
    JIT_VARIANT_CHAR    = 3,
    JIT_VARIANT_STRING  = 4,
    JIT_VARIANT_DOUBLE  = 5,
    JIT_VARIANT_POINTER = 6
    
}   JitVariantKind;

// ---------------------------------------------------------------------------
// NT32-Layout: exakt 12 Byte
//
// +0  kind
// +4  value_low
// +8  value_high
//
// Integer, Boolean, String und Pointer liegen in value_low.
// Double liegt als 64-Bit-Bitmuster in value_low/value_high.
// ---------------------------------------------------------------------------
# pragma pack(push, 1)

typedef struct JitVariantArg
{
    uint32_t kind;
    uint32_t value_low;
    uint32_t value_high;
    
}   JitVariantArg;

# pragma pack(pop)

DLL_API VOID JIT_CDECL _jit_print_variant      (const JitVariantArg *value);
DLL_API VOID JIT_CDECL _jit_print_variant_array(const JitVariantArg *values, int32_t high);

#ifdef __cplusplus
};
#endif

#endif
