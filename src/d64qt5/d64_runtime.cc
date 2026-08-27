// ---------------------------------------------------------------------------
// File:   d64_runtime.cc
// Author: (c) 2026 Jens Kallup - paule32
// All rights reserved
// ---------------------------------------------------------------------------
// Purpose:
//   Minimal PE32 runtime symbol set reconstructed from test_raise.exe imports
//   and the supplied dBase2Many runtime sources.
//
// Target: i686 / Windows PE32 / MinGW GCC
// ---------------------------------------------------------------------------
#if !defined(_WIN32)
# error "This source is intended for Windows PE32."
#endif
#if !defined(__i386__)
# error "This source implements the PE32/i386 exception ABI. Build with MinGW32."
#endif

#include <windows.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#ifndef DLL_API
# define DLL_API __declspec(dllexport)
#endif
#ifndef JIT_CDECL
# define JIT_CDECL __cdecl
#endif

// ---------------------------------------------------------------------------
// Exception ABI -- matches supplied exception.h (PE32).
// ---------------------------------------------------------------------------
enum JitExceptionCode {
    JIT_OK = 0,
    JIT_RUNTIME_ERROR,
    JIT_OUT_OF_MEMORY,
    JIT_NIL_POINTER,
    JIT_ARRAY_BOUNDS,
    JIT_STRING_RANGE,
    JIT_DIVIDE_BY_ZERO,
    JIT_INVALIDE
};

struct JitJumpBuffer {
    uint32_t ebx;
    uint32_t esi;
    uint32_t edi;
    uint32_t ebp;
    uint32_t esp;
    uint32_t eip;
};

struct JitExceptionFrame {
    JitJumpBuffer *env;
    JitExceptionCode code;
    char message[256];
    JitExceptionFrame *prev;
};

static JitExceptionFrame *gExceptionFrame = nullptr;

static void d64_write_text(const char *text)
{
    if (!text)
        return;

    HANDLE h = GetStdHandle(STD_OUTPUT_HANDLE);
    if (!h || h == INVALID_HANDLE_VALUE)
        return;

    DWORD written = 0;
    DWORD len = (DWORD)strlen(text);
    if (len)
        WriteFile(h, text, len, &written, nullptr);
}

static void d64_write_line(const char *text)
{
    if (text)
        d64_write_text(text);
    d64_write_text("\r\n");
}

extern "C" {

DLL_API void JIT_CDECL jit_exception_push(JitExceptionFrame *frame)
{
    if (!frame)
        return;

    frame->prev = gExceptionFrame;
    frame->code = JIT_OK;
    frame->message[0] = 0;
    gExceptionFrame = frame;
}

DLL_API void JIT_CDECL jit_exception_pop(void)
{
    if (gExceptionFrame)
        gExceptionFrame = gExceptionFrame->prev;
}

// ---------------------------------------------------------------------------
// PE32 setjmp/longjmp.
// Equivalent to the supplied setjmp32.asm ABI used by memory.cc.
// ---------------------------------------------------------------------------
DLL_API __attribute__((naked)) int JIT_CDECL jit_setjmp(JitJumpBuffer * /*env*/)
{
    __asm__ __volatile__(
        "movl 4(%esp), %edx\n\t"
        "movl %ebx, 0(%edx)\n\t"
        "movl %esi, 4(%edx)\n\t"
        "movl %edi, 8(%edx)\n\t"
        "movl %ebp, 12(%edx)\n\t"
        "leal 4(%esp), %eax\n\t"
        "movl %eax, 16(%edx)\n\t"
        "movl (%esp), %eax\n\t"
        "movl %eax, 20(%edx)\n\t"
        "xorl %eax, %eax\n\t"
        "ret\n\t"
    );
}

static __attribute__((naked, noreturn)) void JIT_CDECL d64_longjmp(
    JitJumpBuffer * /*env*/,
    int /*value*/)
{
    __asm__ __volatile__(
        "movl 4(%esp), %edx\n\t"
        "movl 8(%esp), %eax\n\t"
        "testl %eax, %eax\n\t"
        "jne 1f\n\t"
        "movl $1, %eax\n\t"
        "1:\n\t"
        "movl 0(%edx), %ebx\n\t"
        "movl 4(%edx), %esi\n\t"
        "movl 8(%edx), %edi\n\t"
        "movl 12(%edx), %ebp\n\t"
        "movl 16(%edx), %esp\n\t"
        "jmp *20(%edx)\n\t"
    );
}

DLL_API void JIT_CDECL jit_raise(JitExceptionCode code, const char *message)
{
    JitExceptionFrame *frame = gExceptionFrame;

    if (!frame) {
        d64_write_line("Unhandled Runtime Exception");
        if (message)
            d64_write_line(message);
        ExitProcess(1);
    }

    frame->code = code;

    // Preserve the supplied exception.cc behaviour: a provided message is
    // printed before control transfers to the EXCEPT handler.
    if (message)
        d64_write_line(message);
    else
        frame->message[0] = 0;

    d64_longjmp(frame->env, 1);
}

// ---------------------------------------------------------------------------
// Console/string allocation subset from supplied memory.cc.
// ---------------------------------------------------------------------------
DLL_API char *JIT_CDECL jit_read_string(void)
{
    const DWORD capacity = 1024;
    char *buffer = (char *)malloc(capacity);
    if (!buffer)
        return nullptr;

    HANDLE h = GetStdHandle(STD_INPUT_HANDLE);
    if (!h || h == INVALID_HANDLE_VALUE) {
        free(buffer);
        return nullptr;
    }

    DWORD bytesRead = 0;
    if (!ReadFile(h, buffer, capacity - 1, &bytesRead, nullptr)) {
        free(buffer);
        return nullptr;
    }

    if (bytesRead >= capacity)
        bytesRead = capacity - 1;
    buffer[bytesRead] = 0;

    while (bytesRead &&
          (buffer[bytesRead - 1] == '\r' || buffer[bytesRead - 1] == '\n'))
        buffer[--bytesRead] = 0;

    return buffer;
}

DLL_API void JIT_CDECL jit_free(void *ptr)
{
    // The uploaded memory.cc accidentally calls jit_free(ptr) recursively
    // inside this function.  The intended allocator pair is free(ptr).
    free(ptr);
}

// ---------------------------------------------------------------------------
// Dynamic string ABI from runtime/string.h + memory.cc.
// test_raise.exe imports the public spelling WITHOUT the leading underscore.
// ---------------------------------------------------------------------------
static const uint32_t DYNSTRING_MAGIC = 0x44535452u; // 'DSTR'

struct DynStringHeader {
    uint32_t magic;
    uint32_t reserved;
    uint32_t length;
};

DLL_API char *JIT_CDECL jit_dynstring_from_cstr(const char *text)
{
    if (!text)
        text = "";

    uint32_t len = (uint32_t)strlen(text);
    DynStringHeader *h = (DynStringHeader *)malloc(sizeof(DynStringHeader) + len + 1);
    if (!h)
        jit_raise(JIT_OUT_OF_MEMORY, "Out of memory.");

    h->magic = DYNSTRING_MAGIC;
    h->reserved = 0;
    h->length = len;

    char *data = (char *)(h + 1);
    if (len)
        memcpy(data, text, len);
    data[len] = 0;
    return data;
}

// ---------------------------------------------------------------------------
// Object/VMT ABI -- matches supplied jitObject.h / jitObject.cc.
// ---------------------------------------------------------------------------
struct JitVmt;
typedef void (JIT_CDECL *JitInitializeProc)(void *instance);
typedef void (JIT_CDECL *JitFinalizeProc)(void *instance);
typedef void (JIT_CDECL *JitDestroyProc)(void *instance);

struct JitVmt {
    JitVmt *parent;
    const char *class_name;
    uint32_t instance_size;
    JitInitializeProc initialize_instance;
    JitFinalizeProc finalize_instance;
    JitDestroyProc destroy;
};

struct JitObjectHeader {
    JitVmt *vmt;
};

static bool jit_valid_vmt(JitVmt *vmt)
{
    return vmt && vmt->instance_size >= sizeof(JitObjectHeader);
}

DLL_API JitVmt *JIT_CDECL jit_object_class_type(void *instance)
{
    if (!instance)
        return nullptr;

    JitObjectHeader *header = (JitObjectHeader *)instance;
    return jit_valid_vmt(header->vmt) ? header->vmt : nullptr;
}

DLL_API void JIT_CDECL jit_object_instance_free(void *instance)
{
    if (!instance)
        return;

    JitObjectHeader *header = (JitObjectHeader *)instance;
    JitVmt *vmt = header->vmt;
    if (!jit_valid_vmt(vmt))
        return;

    if (vmt->finalize_instance)
        vmt->finalize_instance(instance);

    header->vmt = nullptr;
    jit_free(instance);
}

DLL_API void JIT_CDECL jit_object_free(void *instance)
{
    if (!instance)
        return;

    JitVmt *vmt = jit_object_class_type(instance);
    if (!vmt)
        return;

    if (vmt->destroy)
        vmt->destroy(instance);

    jit_object_instance_free(instance);
}

DLL_API JitVmt *JIT_CDECL jit_class_parent(JitVmt *vmt)
{
    return jit_valid_vmt(vmt) ? vmt->parent : nullptr;
}

DLL_API const char *JIT_CDECL jit_class_name(JitVmt *vmt)
{
    if (!vmt)
        return "";
    return vmt->class_name ? vmt->class_name : "<unknown>";
}

DLL_API uint32_t JIT_CDECL jit_class_instance_size(JitVmt *vmt)
{
    return jit_valid_vmt(vmt) ? vmt->instance_size : 0;
}

static int JIT_CDECL jit_inherits_from_class(
    JitVmt *current_class,
    JitVmt *expected_class)
{
    if (!current_class || !expected_class)
        return 0;

    while (current_class) {
        if (current_class == expected_class)
            return 1;
        current_class = current_class->parent;
    }
    return 0;
}

DLL_API int JIT_CDECL jit_inherits_from_object(
    void *instance,
    JitVmt *expected_class)
{
    if (!instance || !expected_class)
        return 0;

    JitVmt *current_class = jit_object_class_type(instance);
    return current_class
        ? jit_inherits_from_class(current_class, expected_class)
        : 0;
}

} // extern "C"
