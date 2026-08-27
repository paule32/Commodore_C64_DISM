// ---------------------------------------------------------------------------
// File: iostream.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_IOSTREAM_HH__
#define __DBASE2MANY_IOSTREAM_HH__

# pragma once
# include "stddef.h"

extern "C" {
typedef char* va_list;

# define va_start(ap, last) (ap = (va_list)(&last + 1))
# define va_arg(  ap, type) (*(type *)((ap += sizeof(type)) - sizeof(type)))
# define va_end(  ap)       ((void)(ap = (va_list)0))

typedef int (JIT_CDECL *printf_fn  )(const char *format, ...);
typedef int (JIT_CDECL *vprintf_fn )(const char *format, ...);

DLL_API int  JIT_CDECL _jit_printf  (const char *format, ...);
DLL_API int  JIT_CDECL _jit_vprintf (const char *format, va_list arg);

typedef int (JIT_CDECL *snprintf_fn )(char *buffer, size_t size, const char *fmt, ...);
typedef int (JIT_CDECL *vsnprintf_fn)(char *buffer, size_t size, const char *fmt, va_list ap);

DLL_API int  JIT_CDECL _jit_snprintf (char *buffer, size_t size, const char *fmt, ...);
DLL_API int  JIT_CDECL _jit_vsnprintf(char *buffer, size_t size, const char *fmt, va_list ap);

DLL_API VOID _jit_print_cstr(const char *text);
DLL_API VOID _jit_print_text(const char* s);
DLL_API VOID _jit_print_char(int c);
DLL_API VOID _jit_print_int(int v);
DLL_API VOID _jit_print_double(double v);
DLL_API VOID _jit_print_newline();

DLL_API int   JIT_CDECL _jit_read_char();
DLL_API char* JIT_CDECL _jit_read_string();
DLL_API int   JIT_CDECL _jit_read_int();

DLL_API void  JIT_CDECL _jit_debug_break();
};

namespace std {
class ostream;

typedef ostream& (*ostream_manipulator)(ostream&);

class ostream {
public:
    ostream();

    ostream& operator<<(int value);
    ostream& operator<<(uint32_t value);
    ostream& operator<<(double value);
    ostream& operator<<(char value);
    ostream& operator<<(const char* text);

    ostream& operator<<(ostream_manipulator fn);
};

extern ostream cout;

ostream& endl(ostream& os);
}   // namespace: std

#endif
