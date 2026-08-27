// ---------------------------------------------------------------------------
// File: string.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_STRING_HH__
#define __DBASE2MANY_STRING_HH__

# pragma once
# include "stddef.h"

namespace std {
class string {
private:
    char* data_;
    unsigned int len_;
public:
     string();
     string(const char* s);
    ~string();

    const    char* c_str() const;
    unsigned int  length() const;
};
}

extern "C" {
// ---------------------------------------------------------------------------
// dynamic string - SetLength ...
// ---------------------------------------------------------------------------
constexpr DWORD DYNSTRING_MAGIC = 0x44535452;  // 'DSTR'

struct DynStringHeader {
    uint32_t magic;
    uint32_t reserved;
    uint32_t length;
    ///char   * data;
};

DLL_API void * jit_dynstring_setlength(void * data, uint32_t length);
DLL_API int    jit_dynstring_length(const char * data);
DLL_API char * jit_dynstring_concat(const char* left, const char* right);
DLL_API char * jit_dynstring_from_cstr(const char* text);

DLL_API char * _jit_strdup(const char *s);
DLL_API size_t _jit_strlen(const char* str);
DLL_API size_t      strlen(const char* str);

DLL_API char * _jit_strncpy(char *dest, const char *src, unsigned int count);

DLL_API LPSTR JIT_STDCALL lstrcpynA(LPSTR, LPCSTR, int);

};

#endif
