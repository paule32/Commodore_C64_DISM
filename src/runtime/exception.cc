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

// Stage 534: resolve Kernel32 TLS functions without adding an import library.
// TLS is per OS thread; the index is a process-wide resource owned by this DLL.
typedef DWORD (JIT_STDCALL *D64TlsAllocFn)(void);
typedef BOOL (JIT_STDCALL *D64TlsFreeFn)(DWORD);
typedef LPVOID (JIT_STDCALL *D64TlsGetValueFn)(DWORD);
typedef BOOL (JIT_STDCALL *D64TlsSetValueFn)(DWORD, LPVOID);
static D64TlsAllocFn     g_tls_alloc = nullptr;
static D64TlsFreeFn      g_tls_free  = nullptr;
static D64TlsGetValueFn g_tls_get   = nullptr;
static D64TlsSetValueFn g_tls_set   = nullptr;
static DWORD g_tls_index = 0xFFFFFFFFU;
static volatile int g_tls_state = 0; // 0=uninit, 1=busy, 2=ready, 3=failed

static bool d64_exception_tls_ready()
{
    int state = __sync_val_compare_and_swap(&g_tls_state, 2, 2);
    if (state == 2) return true;
    if (__sync_bool_compare_and_swap(&g_tls_state, 0, 1)) {
        HMODULE kernel = LoadLibraryA("kernel32.dll");
        if (kernel) {
            g_tls_alloc = (D64TlsAllocFn)GetProcAddress(kernel, "TlsAlloc");
            g_tls_free  = (D64TlsFreeFn)GetProcAddress(kernel, "TlsFree");
            g_tls_get   = (D64TlsGetValueFn)GetProcAddress(kernel, "TlsGetValue");
            g_tls_set   = (D64TlsSetValueFn)GetProcAddress(kernel, "TlsSetValue");
        }
        bool ok = g_tls_alloc && g_tls_free && g_tls_get && g_tls_set;
        if (ok) {
            g_tls_index = g_tls_alloc();
            ok = g_tls_index != 0xFFFFFFFFU;
        }
        __sync_synchronize();
        g_tls_state = ok ? 2 : 3;
        return ok;
    }
    while (__sync_val_compare_and_swap(&g_tls_state, 1, 1) == 1) {
        __asm__ volatile("pause");
    }
    return __sync_val_compare_and_swap(&g_tls_state, 2, 2) == 2;
}

static JitExceptionFrame *d64_current_exception()
{
    if (!d64_exception_tls_ready()) ExitProcess(1);
    return (JitExceptionFrame*)g_tls_get(g_tls_index);
}

static void d64_set_current_exception(JitExceptionFrame *frame)
{
    if (!d64_exception_tls_ready() || !g_tls_set(g_tls_index, frame))
        ExitProcess(1);
}

extern "C" VOID _jit_exception_tls_cleanup(void)
{
    // Called at DLL_PROCESS_DETACH, once no more threads use this module.
    if (__sync_val_compare_and_swap(&g_tls_state, 2, 2) == 2) {
        g_tls_free(g_tls_index);
        g_tls_index = 0xFFFFFFFFU;
        g_tls_state = 3;
    }
}

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
_jit_exception_push(JitExceptionFrame *frame)
{
    if (!frame || !frame->env) return;
    frame->prev = d64_current_exception();
    frame->code = JIT_OK;
    frame->message[0] = 0;
    d64_set_current_exception(frame);
}

DLL_API VOID
_jit_exception_pop(void)
{
    JitExceptionFrame *frame = d64_current_exception();
    if (frame)
        d64_set_current_exception(frame->prev);
}

DLL_API VOID
_jit_raise(JitExceptionCode code, const char *message)
{
    JitExceptionFrame *frame = d64_current_exception();
    if (!frame) {
        std::cout << "Unhandled Runtime Exception" << std::endl;
        if (message) std::cout << message << std::endl;
        ExitProcess(1);
    }

    frame->code = code;
    unsigned i = 0;
    if (message) {
        while (message[i] && i < sizeof(frame->message)-1) {
            frame->message[i] = message[i];
            ++i;
        }
    }
    frame->message[i] = 0;
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
