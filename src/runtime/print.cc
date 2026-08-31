// ---------------------------------------------------------------------------
// \file print.cc
// \note Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "iostream.h"
# include "stddef.h"
# include "memory.h"
# include "string.h"
# include "variant.h"
# include "exception.h"
# include "windows.h"

extern "C" {

DLL_API void  _jit_print_newline() { _jit_print_text("\n"); }
DLL_API char* _jit_dynstring_from_cstr(const char* text);

unsigned int utoa10(unsigned int value, char *buffer)
{
    char tmp[16];
    unsigned int len = 0;

    do {
        tmp[len++] = '0' + (value % 10);
        value /= 10;
    }   while (value);

    for (unsigned int i = 0; i < len; i++)
    buffer[i  ] = tmp[len - i - 1];
    buffer[len] = 0;

    return len;
}

unsigned int itoa10(int value, char *buffer)
{
    unsigned int pos = 0;

    if (value < 0) {
        buffer[pos++] = '-';
        value = -value;
    }

    return pos + utoa10((unsigned int)value, buffer + pos);
}

DLL_API VOID _jit_print_char(int ch)
{
    DWORD  written;
    HANDLE h = p_GetStdHandle(STD_OUTPUT_HANDLE);
    p_WriteFile(h, &ch, 1, &written, 0);
}

DLL_API VOID _jit_print_double(double value)
{
    if (value < 0.0) {
        _jit_print_text("-");
        value = -value;
    }

    int integer = (int)value;
    double frac = value - integer;
    HANDLE    h = p_GetStdHandle(STD_OUTPUT_HANDLE);

    _jit_print_int(integer);
    _jit_print_text(".");

    for (int i = 0; i < 6; i++) {
        frac     *= 10.0;
        int digit = (int)frac;
        char c    = '0' + digit;

        DWORD written;
        p_WriteFile(h, &c, 1, &written, nullptr);
        frac -= digit;
    }
}

DLL_API VOID _jit_print_int(int value)
{
    char buffer[16];
    DWORD written;

    unsigned int len = itoa10(value, buffer);
    HANDLE   h = p_GetStdHandle(STD_OUTPUT_HANDLE);

    p_WriteFile(h, buffer, len, &written, 0);
    //ExitProcess(1);
}

DLL_API char *
_jit_dynstring_copy(
    char* src,
    int start,
    int count) {
    
    if (!src)
        return _jit_dynstring_from_cstr("");

    DynStringHeader* h = (DynStringHeader*)(src - sizeof(DynStringHeader));

    if (h->magic != DYNSTRING_MAGIC)
        _jit_raise(
            JIT_RUNTIME_ERROR,
            "Invalid dynamic string"
        );

    int len = (int)h->length;

    // Pascal: Strings sind 1-basiert
    if (start < 1)
        start = 1;

    if (count <= 0 || start > len)
        return _jit_dynstring_from_cstr("");

    int zero_index = start - 1;
    int available  = len - zero_index;

    if (count > available)
        count = available;
    
    char *result = static_cast<char *>(
        _jit_malloc(
            sizeof(DynStringHeader) + count + 1
        )
    );
    
    if (!result) {
        _jit_raise(
            JIT_RUNTIME_ERROR,
            "Out of memory in dynstring_copy"
        );
    }

    DynStringHeader* rh = reinterpret_cast<DynStringHeader*>(result);
    rh->magic    = DYNSTRING_MAGIC;
    rh->reserved = 0;
    rh->length   = count;

    char* data = result + sizeof(DynStringHeader);

    _jit_memcpy(
        data,
        src + zero_index,
        count
    );
    
    data[count] = 0;

    return data;
}

DLL_API int
_jit_dynstring_pos(
    char* needle,
    char* haystack)
{
    if (!needle || !haystack)
        return 0;

    DynStringHeader* nh = (DynStringHeader*)(needle   - sizeof(DynStringHeader));
    DynStringHeader* hh = (DynStringHeader*)(haystack - sizeof(DynStringHeader));

    if (nh->magic != DYNSTRING_MAGIC)
        _jit_raise(
            JIT_RUNTIME_ERROR,
            "Invalid search string"
        );

    if (hh->magic != DYNSTRING_MAGIC)
        _jit_raise(
            JIT_RUNTIME_ERROR,
            "Invalid source string"
        );

    int nlen = (int)nh->length;
    int hlen = (int)hh->length;

    if (nlen <= 0)
        return 0;

    if (nlen > hlen)
        return 0;

    for (int i = 0; i <= hlen - nlen; i++)
    {
        if (_jit_memcmp(haystack + i, needle, nlen) == 0)
            return i + 1;   // Pascal: 1-basiert
    }

    return 0;
}

DLL_API VOID JIT_CDECL _jit_print_variant(const JitVariantArg *value)
{
    uint64_t bits;
    double double_value;

    if (value == nullptr) {
        return;
    }

    switch (value->kind) {
        case JIT_VARIANT_INTEGER: {
            _jit_print_int((int32_t)value->value_low);
            break;
        }

        case JIT_VARIANT_BOOLEAN: {
            // Später kann hier True/False statt 0/1 ausgegeben werden.
            _jit_print_int(value->value_low != 0);
            break;
        }

        case JIT_VARIANT_CHAR: {
            LPCSTR char_ptr = (LPCSTR)(uintptr_t)value->value_low;
            if (char_ptr != nullptr) {
                int ch = (unsigned char)char_ptr[0];
                _jit_print_char(ch);
            }
            break;
        }

        case JIT_VARIANT_STRING: {
            _jit_print_text((const char *)(uintptr_t)value->value_low);
            break;
        }

        case JIT_VARIANT_DOUBLE: {
            bits = ((uint64_t)value->value_high << 32) | value->value_low;
            _jit_memcpy(&double_value, &bits, sizeof(double_value));

            _jit_print_double(double_value);
            break;
        }

        case JIT_VARIANT_POINTER: {
            // Pointer zunächst hexadezimal ausgeben.
            _jit_printf("0x%08X", (unsigned)value->value_low);
            break;
        }

        case JIT_VARIANT_EMPTY:
        default: {
            break;
        }
    }
}

DLL_API VOID JIT_CDECL
_jit_print_variant_array(
    const JitVariantArg *values,
    int32_t high) {
    
    int32_t index;

    if (values == nullptr || high < 0) {
        return;
    }

    for (index = 0; index <= high; ++index) {
        _jit_print_variant(&values[index]);
    }
}

};
