// ---------------------------------------------------------------------------
// \file error.cc
// \note Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "iostream.h"
# include "stddef.h"
# include "memory.h"
# include "string.h"
# include "exception.h"

using namespace std;

DLL_API VOID _jit_error_divide_by_zero() {
    _jit_raise(
        JIT_RUNTIME_ERROR,
        "division through zero"
    );
}

DLL_API void
_jit_error_array_bounds(
    const char* array_name,
    int index,
    int min_value,
    int max_value) {
    
    _jit_raise(
        JIT_RUNTIME_ERROR,
        "Array bounds error: "
    );
}

DLL_API void
_jit_error_string_range() {
    _jit_raise(
        JIT_RUNTIME_ERROR,
        "String range check error"
    );
}

DLL_API void
_jit_error_nil_pointer(const char* name)
{
    _jit_raise(
        JIT_RUNTIME_ERROR,
        "Nil pointer error: "
        //(name ? name : "<unknown>")
    );
}

DLL_API void
_jit_error_out_of_memory(const char* what)
{
    std::cout << what << std::endl;
    _jit_raise(
        JIT_RUNTIME_ERROR,
        "Out of memory: "
    );
}

DLL_API void
_jit_set_exception(
    JitContext* ctx,
    const char* message
)
{
    if (!ctx)
        return;

    ctx->exception_active  = 1;
    ctx->exception_message = message;
}

DLL_API void
_jit_error_runtime(const char* message)
{
    _jit_raise(
        JIT_RUNTIME_ERROR,
        message ? message : "Runtime error"
    );
}
