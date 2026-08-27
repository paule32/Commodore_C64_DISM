// ---------------------------------------------------------------------------
// File: exception.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_EXCEPTION_H__
#define __DBASE2MANY_EXCEPTION_H__

# pragma once
# include "stddef.h"
# include "string.h"

namespace std {
class runtime_error;
class JitRuntimeError;

class runtime_error {
public:
    runtime_error();
    runtime_error(const std::string& message);
};

class JitRuntimeError: public std::runtime_error {
public:
     explicit JitRuntimeError();
     explicit JitRuntimeError(const std::string& message);
};

}

extern "C" {

typedef enum {
    JIT_OK = 0,

    JIT_RUNTIME_ERROR,
    JIT_OUT_OF_MEMORY,
    JIT_NIL_POINTER,
    JIT_ARRAY_BOUNDS,
    JIT_STRING_RANGE,
    JIT_DIVIDE_BY_ZERO,
    JIT_INVALIDE
    
}   JitExceptionCode;

typedef struct {
    uint32_t ebx;
    uint32_t esi;
    uint32_t edi;

    uint32_t ebp;
    uint32_t esp;

    uint32_t eip;
    
}   JitJumpBuffer;

typedef struct JitExceptionFrame {
    JitJumpBuffer    *  env;
    JitExceptionCode    code;
    char                message[256];
    struct              JitExceptionFrame *prev;
    
}   JitExceptionFrame;

extern JitExceptionFrame *gExceptionFrame;

// Stackverwaltung
DLL_API VOID _jit_exception_push(JitExceptionFrame *frame);
DLL_API VOID _jit_exception_pop (void);

// Exception werfen
DLL_API VOID _jit_raise(JitExceptionCode code, const char *message);

DLL_API VOID _jit_error_runtime      (const char *msg);
DLL_API VOID _jit_error_out_of_memory(const char *msg);
DLL_API VOID _jit_error_nil_pointer  (void);
DLL_API VOID _jit_error_array_bounds (void);
DLL_API VOID _jit_error_string_range (void);

};

#endif
