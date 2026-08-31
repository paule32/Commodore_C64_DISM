// ---------------------------------------------------------------------------
// File: string.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "iostream.h"
# include "stddef.h"
# include "string.h"
# include "memory.h"

namespace std {
string::string() {}
string::string(const char* s)
{
    len_  = (unsigned int)_jit_strlen(s);
    data_ = (char*)       _jit_malloc(len_ + 1);
    
    _jit_memcpy(data_, s, len_ + 1);
}

string::~string() { _jit_free(data_); }

const    char* string::c_str () const { return data_ ? data_ : ""; }
unsigned int   string::length() const { return len_; }
}   // namespace: std

DLL_API
char* _jit_strncpy(
    char *dest,
    const char *src,
    unsigned int count)
{
    unsigned int i = 0;
    
    while (i < count && src[i] != '\0') {
        dest[i] = src[i];
        i++;
    }
    
    while (i < count) {
        dest[i] = '\0';
        i++;
    }
    return dest;
}

DLL_API size_t strlen(const char* str) {
    return _jit_strlen(str);
}
