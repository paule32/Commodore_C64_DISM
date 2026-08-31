// ---------------------------------------------------------------------------
// \file memory.cc
// \note Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "iostream.h"
# include "stddef.h"
# include "string.h"
# include "memory.h"
# include "windows.h"

static malloc_fn    p_malloc    = nullptr;
static calloc_fn    p_calloc    = nullptr;
static realloc_fn   p_realloc   = nullptr;
static free_fn      p_free      = nullptr;

static memcpy_fn    p_memcpy    = nullptr;
static memset_fn    p_memset    = nullptr;
static memcmp_fn    p_memcmp    = nullptr;
static memmove_fn   p_memmove   = nullptr;

static vprintf_fn   p_vprintf   = nullptr;
static printf_fn    p_printf    = nullptr;

//static snprintf_fn  p_snprintf  = nullptr;
static vsnprintf_fn p_vsnprintf = nullptr;

// ---------------------------------------------------------------------------
// msvcrt.dll imports ...
// ---------------------------------------------------------------------------
struct CRTImport {
    const char* name;
    void**      target;
};
CRTImport crt_imports[] = {
    { "malloc",    (void**)&p_malloc     },
    { "calloc",    (void**)&p_calloc     },
    { "realloc",   (void**)&p_realloc    },
    { "free",      (void**)&p_free       },

    { "memcpy",    (void**)&p_memcpy     },
    { "memset",    (void**)&p_memset     },
    { "memcmp",    (void**)&p_memcmp     },
    { "memmove",   (void**)&p_memmove    },

    { "printf",    (void**)&p_printf     },
    { "vprintf",   (void**)&p_vprintf    },
    
    //{ "snprintf",  (void**)&p_snprintf   },
    { "vsnprintf", (void**)&p_vsnprintf  },
};

// ---------------------------------------------------------------------------
// kernel32.dll imports ...
// ---------------------------------------------------------------------------
struct KERNEL32Import {
    const char* name;
    void**      target;
};
KERNEL32Import kernel32_imports[] = {
    { "ExitProcess",            (void**)&p_ExitProcess},
    { "GetDriveTypeA",          (void**)&p_GetDriveTypeA},
    { "GetVolumeInformationA",  (void**)&p_GetVolumeInformationA},
};

// ---------------------------------------------------------------------------
// user32.dll imports ...
// ---------------------------------------------------------------------------
struct USER32Import {
    const char* name;
    void**      target;
};
USER32Import user32_imports[] = {
    { "MessageBoxA",     (void**)&p_MessageBoxA  },
};

// ---------------------------------------------------------------------------
// mpr.dll imports ...
// ---------------------------------------------------------------------------
struct MPRImport {
    const char* name;
    void**      target;
};
MPRImport mpr_imports[] = {
    { "WNetGetConnectionA", (void**)&p_WNetGetConnectionA},
};

static int init_msvcrt(void)
{
    HMODULE h1, h2, h3, h4;
    bool ok = true;

    if (p_malloc && p_free) {
        return 1;
    }
    
    // msvcrt.dll
    ok = true;
    h1 = p_LoadLibraryA("msvcrt.dll");
    if (!h1) {
        p_MessageBoxA(0,
            "Error",
            "Error: msvcrt.dll could not load.",
            0);
        return 0;
    }
    
    for (int i = 0; i < sizeof(crt_imports) / sizeof(crt_imports[0]); ++i) {
        *crt_imports[i].target = (void*)p_GetProcAddress(h1, crt_imports[i].name);
        
        if (!*crt_imports[i].target) {
            std::cout << crt_imports[i].name << " ";
            ok = false;
        }
    }
    
    // kernel32t.dll
    ok = true;
    h2 = p_LoadLibraryA("kernel32.dll");
    if (!h2) {
        MessageBoxA(0,
            "Error",
            "Error: kernel32.dll could not load.",
            0);
        return 0;
    }
    
    for (int i = 0; i < sizeof(kernel32_imports) / sizeof(kernel32_imports[0]); ++i) {
        *kernel32_imports[i].target = (void*)GetProcAddress(h2, kernel32_imports[i].name);
        
        if (!*kernel32_imports[i].target) {
            std::cout << kernel32_imports[i].name << " ";
            ok = false;
        }
    }
    if (!ok) {
        std::cout << "== null" << std::endl;
        return 0;
    }
    
    // user32.dll
    ok = true;
    h3 = LoadLibraryA("user32.dll");
    if (!h3) {
        MessageBoxA(0,
            "Error",
            "Error: user32.dll could not load.",
            0);
        return 0;
    }
    
    for (int i = 0; i < sizeof(user32_imports) / sizeof(user32_imports[0]); ++i) {
        *user32_imports[i].target = (void*)GetProcAddress(h3, user32_imports[i].name);
        
        if (!*user32_imports[i].target) {
            std::cout << user32_imports[i].name << " ";
            ok = false;
        }
    }
    
    // user32.dll
    ok = true;
    h4 = p_LoadLibraryA("mpr.dll");
    if (!h4) {
        MessageBoxA(0,
            "Error",
            "Error: mpr.dll could not load.",
            0);
        return 0;
    }
    
    for (int i = 0; i < sizeof(mpr_imports) / sizeof(mpr_imports[0]); ++i) {
        *mpr_imports[i].target = (void*)GetProcAddress(h4, mpr_imports[i].name);
        
        if (!*mpr_imports[i].target) {
            std::cout << mpr_imports[i].name << " ";
            ok = false;
        }
    }
    if (!ok) {
        std::cout << "== null" << std::endl;
        return 0;
    }   return 1;
}

extern "C" DLL_API char* _jit_dynstring_from_cstr(const char* text);

static bool is_probably_dynstring(const char* data)
{
    if (!data)
        return false;

    const DynStringHeader* h = ((const DynStringHeader*)data) - 1;
    return h->length < 1024 * 1024;
}

static bool is_dynstring(const char* data)
{
    if (!data)
        return false;

    const DynStringHeader* h = ((const DynStringHeader*)data) - 1;
    return h->magic == DYNSTRING_MAGIC;
}

static uint64_t
dynstring_length_strict(
    const char* data) {
    
    if (!data)
        return 0;

    const DynStringHeader* h = ((const DynStringHeader*)data) - 1;

    if (h->magic != DYNSTRING_MAGIC) {
        _jit_raise(
            JIT_INVALIDE,
            "Invalid dynamic string"
        );
    }

    return h->length;
}

static uint64_t string_length_mixed(
    const char* data) {
    
    if (!data)
        return 0;

    if (is_dynstring(data)) {
        const DynStringHeader* h = ((const DynStringHeader*)data) - 1;
        return h->length;
    }

    return (uint64_t)_jit_strlen(data);
}
extern "C" {
    
/*
DLL_API void*
_jit_new_memory(uint32_t size)
{
    void* p = _jit_malloc(size);

    if (!p) {
        _jit_raise(
            JIT_OUT_OF_MEMORY,
            "Out of memory in New()"
        );
    }

    p_memset(p, 0, size);
    return p;
}*/

DLL_API void *
_jit_new_memory(uint32_t size)
{
    void *p = _jit_malloc(size);

    if (!p) {
        _jit_error_out_of_memory("Out of memory in New()");
        return 0;
    }

    _jit_memset(p, 0, size);
    return p;
}

DLL_API void
_jit_dispose_memory(void* p)
{
    if (!p) return;
    if (!p_free)  {
        if (!init_msvcrt())
            return;
    }

    p_free((JitJumpBuffer*)p);
}

DLL_API void *
_jit_setlength_memory(
    void *   old_ptr,
    uint64_t new_size)
{
    void* p = p_realloc(old_ptr, new_size);

    if (!p) {
        return nullptr;
    }

    return p;
}

DLL_API void *
_jit_dynarray_setlength(
    void *   data,
    uint32_t length,
    uint32_t element_size) {
    
    DynArrayHeader* old_header = nullptr;

    if (data) {
        old_header = ((DynArrayHeader*)data) - 1;
    }

    uint32_t total_size =
        sizeof(DynArrayHeader) + length * element_size;

    DynArrayHeader* new_header =
        //(DynArrayHeader*)p_realloc(old_header, total_size);
        (DynArrayHeader*)_jit_malloc(total_size);

    if (!new_header) {
        _jit_raise(
            JIT_OUT_OF_MEMORY,
            "Out of memory in SetLength(array)"
        );
    }

    new_header->length = length;
    new_header->element_size = element_size;

    return (void*)(new_header + 1);
}

DLL_API void*
_jit_dynstring_setlength(
    void*    old_data,
    uint32_t new_length)
{
    DynStringHeader* old_h = nullptr;

    if (old_data) {
        old_h = ((DynStringHeader*)old_data) - 1;

        if (old_h->magic != DYNSTRING_MAGIC)
            _jit_raise(JIT_RUNTIME_ERROR, "Invalid dynamic string");
    }

    DynStringHeader* h =
        (DynStringHeader*)_jit_malloc(sizeof(DynStringHeader) + new_length + 1);

    if (!h)
        _jit_raise(JIT_OUT_OF_MEMORY, "Out of memory.");

    h->magic    = DYNSTRING_MAGIC;
    h->reserved = 0;
    h->length   = new_length;

    char* data = (char*)(h + 1);

    uint32_t copy_len = 0;

    if (old_h) {
        copy_len = old_h->length;

        if (copy_len > new_length)
            copy_len = new_length;

        if (copy_len > 0)
            _jit_memcpy(data, old_data, copy_len);
    }

    if (new_length > copy_len)
        _jit_memset(data + copy_len, 0, new_length - copy_len);

    data[new_length] = 0;

    return data;
}

DLL_API int
_jit_dynstring_length(const char* data)
{    
    if (!data)
        return 0;

    const DynStringHeader* h = ((const DynStringHeader*)data) - 1;
    return (int)h->length;
}

static DynStringHeader* _jit_dynstring_header_from_data(void* p) {
    if (!p)
    return nullptr;
    return ((DynStringHeader*)p) - 1;
}

DLL_API char*
_jit_dynstring_concat(void* left, void* right)
{
    DynStringHeader* lhs = _jit_dynstring_header_from_data(left);
    DynStringHeader* rhs = _jit_dynstring_header_from_data(right);

    if (!lhs || lhs->magic != DYNSTRING_MAGIC)
        _jit_raise(JIT_RUNTIME_ERROR, "Invalid dynamic string 1");

    if (!rhs || rhs->magic != DYNSTRING_MAGIC)
        _jit_raise(JIT_RUNTIME_ERROR, "Invalid dynamic string 2");

    uint32_t lhs_size = lhs->length;
    uint32_t rhs_size = rhs->length;
    uint32_t total    = lhs_size + rhs_size;

    DynStringHeader* out =
        (DynStringHeader*)_jit_malloc(sizeof(DynStringHeader) + total + 1);

    if (!out)
        _jit_raise(JIT_OUT_OF_MEMORY, "Out of memory.");

    out->magic    = DYNSTRING_MAGIC;
    out->reserved = 0;
    out->length   = total;

    char* data = (char*)(out + 1);

    _jit_memcpy(data, left, lhs_size);
    _jit_memcpy(data + lhs_size, right, rhs_size);
    data[total] = 0;

    return data;
}

DLL_API char*
_jit_dynstring_from_cstr(const char* text)
{
    if (!text)
        text = "";

    uint32_t len = (uint32_t)_jit_strlen(text);

    DynStringHeader* h =
        (DynStringHeader*)_jit_malloc(sizeof(DynStringHeader) + len + 1);

    if (!h)
        _jit_raise(JIT_OUT_OF_MEMORY, "Out of memory.");

    h->magic    = DYNSTRING_MAGIC;
    h->reserved = 0;
    h->length   = len;

    char* data = (char*)(h + 1);

    _jit_memcpy(data, text, len);
    data[len] = 0;

    return data;
}

DLL_API void *
_jit_malloc(uint32_t size)
{
    if (!init_msvcrt()) {
        std::cout << "heap error" << std::endl;
        return nullptr;
    }
    return p_malloc(size);
}

DLL_API void *
_jit_calloc(uint32_t count, uint32_t size)
{
    if (!init_msvcrt()) {
        std::cout << "heap error" << std::endl;
        return nullptr;
    }
    return p_calloc(count, size);
}

DLL_API void *
_jit_realloc(void *ptr, unsigned int new_size) {
    if (!init_msvcrt()) {
        std::cout << "heap error" << std::endl;
        return nullptr;
    }
    return p_realloc(ptr, (size_t)new_size);
}

DLL_API void
_jit_free(void *ptr) {
    if (!ptr)
        return;

    if (!init_msvcrt())
        return;

    _jit_free(ptr);
}

DLL_API size_t
_jit_strlen(const char *s) {
    const char *p = s;

    if (!s) return 0;

    while (*p) ++p;
    return (size_t)(p - s);
}

DLL_API char *
_jit_strdup(const char *s) {
    char *p;
    unsigned int len;

    if (!s)
        s = "";

    if (!p_malloc || !p_memcpy) {
        if (!init_msvcrt())
            return nullptr;
    }
    
    len = (unsigned int)_jit_strlen(s);

    p = (char *)_jit_malloc(len + 1);
    if (!p)
        return nullptr;

    _jit_memcpy(p, s, len + 1);
    return p;
}

DLL_API void * _jit_memcpy (void* dest, const void *src, size_t count) { return p_memcpy (dest, src  , count); }
DLL_API void * _jit_memset (void* dest, int value, size_t count)       { return p_memset (dest, value, count); }
DLL_API void *      memset (void* dest, int value, size_t count)       { return p_memset (dest, value, count); }
DLL_API int    _jit_memcmp (void* buf1, void* buf2, size_t count)      { return p_memcmp (buf1, buf2 , count); }
DLL_API void * _jit_memmove(void* dest, const void* src, size_t count) { return p_memmove(dest, src  , count); }

DLL_API int  _jit_setjmp (JitJumpBuffer *env)            { return __jit_setjmp(env);         }
DLL_API VOID _jit_longjmp(JitJumpBuffer *env, int value) {        __jit_longjmp(env, value); }

DLL_API int  JIT_CDECL _jit_vprintf(const char *format, va_list args) {
    return p_vprintf(format, args);
}
DLL_API int  JIT_CDECL _jit_printf(const char *format, ...) {
    va_list args;
    int result;

    va_start(args, format);
    result = _jit_vprintf(format, args);
    va_end(args);

    return result;
}

DLL_API int JIT_CDECL _jit_vsnprintf(char *buffer, size_t size, const char *fmt, va_list arg) {
    return p_vsnprintf(buffer, size, fmt, arg);
}
DLL_API int JIT_CDECL _jit_snprintf (char *buffer, size_t size, const char *fmt, ...) {
    va_list ap;
    int result;

    va_start(ap, fmt);
    result = _jit_vsnprintf(
        buffer,
        size,
        fmt,
        ap);
    va_end(ap);

    return result;
}

int parse_integer(const char *s)
{
    int sign  = 1;
    int value = 0;

    if (*s == '-') {
        sign = -1;
        s++;
    }

    while (*s >= '0' && *s <= '9') {
        value = value * 10 + (*s - '0');
        s++;
    }

    return value * sign;
}

DLL_API int  JIT_CDECL _jit_read_int() {
    char* buffer = (char*)_jit_malloc(256);
    DWORD bytesRead;
    HANDLE h = p_GetStdHandle(STD_INPUT_HANDLE);
    
    p_ReadFile(h, buffer, sizeof(buffer)-1, &bytesRead, nullptr);
    while (bytesRead &&
      (buffer[  bytesRead-1] == '\r' ||
       buffer[  bytesRead-1] == '\n' )) {
       buffer[--bytesRead] = 0;
    }
    return parse_integer(buffer);
}
DLL_API char*  JIT_CDECL _jit_read_string() {
    char* buffer = (char*)_jit_malloc(1024);
    DWORD bytesRead;
    HANDLE h = p_GetStdHandle(STD_INPUT_HANDLE);
    
    p_ReadFile(h, buffer, sizeof(buffer)-1, &bytesRead, nullptr);
    while (bytesRead &&
      (buffer[  bytesRead-1] == '\r' ||
       buffer[  bytesRead-1] == '\n' )) {
       buffer[--bytesRead] = 0;
    }
    return buffer;
}
DLL_API int JIT_CDECL _jit_read_char()
{
    char   buffer[16];
    DWORD  bytesRead = 0;
    HANDLE hInput;

    if (!p_GetStdHandle || !p_ReadFile)
        return -1;

    hInput = p_GetStdHandle(STD_INPUT_HANDLE);

    if (hInput == nullptr ||
        hInput == INVALID_HANDLE_VALUE) {
        return -1;
    }

    if (!p_ReadFile(
        hInput,
        buffer,
        sizeof(buffer),
        &bytesRead,
        nullptr )) {
        return -1;
    }

    if (bytesRead == 0)
        return -1;

    return static_cast<unsigned char>(buffer[0]);
}

DLL_API void JIT_CDECL _jit_debug_break() {
    _jit_print_text("[DEBUG BREAK] press Enter...");
    _jit_read_char();
    _jit_print_text("\n");
}
};
