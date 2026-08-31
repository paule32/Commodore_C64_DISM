// ---------------------------------------------------------------------------
// File: exception.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "iostream.h"
# include "stddef.h"
# include "exception.h"
# include "string.h"
# include "memory.h"
# include "windows.h"

JitExceptionFrame *gExceptionFrame = nullptr;

namespace std {
runtime_error::runtime_error() {}
runtime_error::runtime_error(const std::string &message) {
    MessageBoxA(
        nullptr,
        message.c_str(),
        "Error",
        0
    );
    ExitProcess(1);
}

JitRuntimeError::JitRuntimeError(
    const std::string& msg):
    std::runtime_error(msg)
    {}

}   // naemspace: std

DLL_API VOID
_jit_exception_push( JitExceptionFrame *frame)
{
    if (!frame)
        return;

    frame->prev = gExceptionFrame;
    frame->code = JIT_OK;
    frame->message[0] = 0;

    gExceptionFrame = frame;
}

DLL_API VOID
_jit_exception_pop(void)
{
    if (gExceptionFrame)
        gExceptionFrame = gExceptionFrame->prev;
}

DLL_API VOID
_jit_raise(
    JitExceptionCode code,
    const char *message)
{
    JitExceptionFrame *frame = gExceptionFrame;
    if (frame == nullptr) {
        std::cout << std::endl;
        std::cout << "Unhandled Runtime Exception" << std::endl;

        if (message)
            std::cout << message <<
            std::endl ;

        ExitProcess(1);
    }

    frame->code = code;

    if (message) {
        std::cout << message << std::endl;
    }   else {
        frame->message[0] = 0;
    }

    _jit_longjmp(frame->env, 1);
}

/*
DLL_API VOID
_jit_error_runtime(const char *msg) {
    _jit_raise(JIT_RUNTIME_ERROR, msg);
}
*/
DLL_API VOID
_jit_error_out_of_memory(void) {
    _jit_raise(
        JIT_OUT_OF_MEMORY,
        "Out of memory");
}

DLL_API VOID
_jit_error_nil_pointer(void) {
    _jit_raise(
        JIT_NIL_POINTER,
        "Nil pointer");
}

DLL_API VOID
_jit_error_array_bounds(void) {
    _jit_raise(
        JIT_ARRAY_BOUNDS,
        "Array bounds exceeded");
}
/*
DLL_API VOID
_jit_error_string_range(void) {
    _jit_raise(
        JIT_STRING_RANGE,
        "String range exceeded");
}
*/
