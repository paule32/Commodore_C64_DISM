// ---------------------------------------------------------------------------
// \file dbase2many.hpp
// \note Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_HPP__
#define __DBASE2MANY_HPP__

#pragma once

// ---------------------------------------------------------------------------
// Windows proto types ...
// ---------------------------------------------------------------------------
# include <windows.h>
# include <winnetwk.h>

// ---------------------------------------------------------------------------
// standard C header stuff ...
// ---------------------------------------------------------------------------
# include <stdio.h>
# include <string.h>
# include <stdlib.h>

// ---------------------------------------------------------------------------
// standard C++ header stuff ...
// ---------------------------------------------------------------------------
# include <cstdio>
# include <cstdint>
# include <cstddef>
# include <cstdlib>
# include <cstring>

# include <iostream>
# include <fstream>
# include <sstream>

# include <stdexcept>
# include <string>
# include <array>
# include <vector>
# include <algorithm>

// ---------------------------------------------------------------------------
// custom C++ header stuff ...
// ---------------------------------------------------------------------------
# ifdef ASMJIT
# include <asmjit/x86.h>
# endif
# include "mapping.hpp"

// ---------------------------------------------------------------------------
// dll export/import members for use DLL ...
// ---------------------------------------------------------------------------
# ifdef DLL_EXPORT
# define DLL_API __declspec(dllexport)
# else
# define DLL_API __declspec(dllimport)
# endif

# define CALL __cdecl

// ---------------------------------------------------------------------------
// all members in this section are marked as C members - no mangled ...
// ---------------------------------------------------------------------------
# ifdef __cplusplus
extern "C"
{
# endif

DLL_API void  _jit_print_text(const char* s);
DLL_API void  _jit_print_int(int v);
DLL_API void  _jit_print_char(int c);
DLL_API void  _jit_print_double(double v);
DLL_API void  _jit_print_newline();

DLL_API void* _jit_setlength_memory(void* old_ptr,uint64_t new_size);

DLL_API void* _jit_new_memory(uint32_t size);
DLL_API void  _jit_dispose_memory(void* p);

DLL_API char* _jit_dynstring_copy(char* src, int start, int count);
DLL_API int   _jit_dynstring_pos(char* needle, char* haystack);

DLL_API void  _jit_nil_pointer_error(const char* name);
DLL_API void  _jit_out_of_memory_error(const char* what);

DLL_API void  _jit_string_range_error();
DLL_API void  _jit_array_bounds_error(
    const char* array_name,
    int index,
    int min_value,
    int max_value);

DLL_API bool  write_formatted_asm_file(
    const char* asm_text,
    const char* file_name);

DLL_API bool  replace_all_str_c(
    const char* asm_text,
    const char* file_name);
    
// ---------------------------------------------------------------------------
// exception handling for our jit framework
// ---------------------------------------------------------------------------
class JitRuntimeError: public std::runtime_error {
public:
    explicit JitRuntimeError(const std::string& msg);
};

// ---------------------------------------------------------------------------
// asmjit context for various structures ...
// ---------------------------------------------------------------------------
struct JitContext {
    int         *  int_vars;

    double      *  double_vars;
    char        ** string_vars;
    uint8_t     *  record_vars;
    uint8_t     *  arrays_vars;
    uint64_t    *  pointr_vars;

    int            print_int_tmp;
    double         print_double_tmp;

    int            exception_active;
    const char  *  exception_message;
};

typedef void (*JitFunc)(JitContext* ctx);

// ---------------------------------------------------------------------------
// SEH ...
// ---------------------------------------------------------------------------
DLL_API void
_jit_set_exception(
    JitContext* ctx,
    const char* message
);

DLL_API void
_jit_runtime_error(
    const char* message
);

// ---------------------------------------------------------------------------
// dynamic array - SetLength ...
// ---------------------------------------------------------------------------
struct DynArrayHeader {
    uint64_t length;
    uint64_t element_size;
};

DLL_API void *
_jit_dynarray_setlength(
    void *   data,
    uint64_t length,
    uint64_t element_size);

// ---------------------------------------------------------------------------
// dynamic string - SetLength ...
// ---------------------------------------------------------------------------
# define DYNSTRING_MAGIC 0x44535452u  // 'DSTR'

struct DynStringHeader {
    uint32_t magic;
    uint32_t reserved;
    uint64_t length;
};

DLL_API void *   _jit_dynstring_setlength(void * data, uint64_t length);
DLL_API int      _jit_dynstring_length(const char * data);
DLL_API char *   _jit_dynstring_concat(const char* left, const char* right);
DLL_API char *   _jit_dynstring_from_cstr(const char* text);

DLL_API int32_t  _jit_read_int();
DLL_API char *   _jit_read_string();

DLL_API void     _jit_symbols_add(SymbolMappings& symbols);

DLL_API void     _jit_debug_break();
DLL_API uint64_t _double_to_bits(double value);    

// ---------------------------------------------------------------------------
// Windows API typedef's ...
// ---------------------------------------------------------------------------
#ifndef WIN32
typedef int32_t    INT;  // 32-bit signed integer: -2147483648 .. 2147483647
typedef uint32_t  UINT;  // unsigned INT: 0 .. 4294967295
typedef void      VOID;  // any type
typedef uint16_t  WORD;  // A 16-bit unsigned integer: 0 .. 65535
#endif  // WIN32

// ---------------------------------------------------------------------------
// Windows API kernel32.dll
// ---------------------------------------------------------------------------
DLL_API VOID _jit_ExitProcess(UINT uExitCode);

// ---------------------------------------------------------------------------
// end of C section
// ---------------------------------------------------------------------------
# ifdef __cplusplus
};
# endif
    
// ---------------------------------------------------------------------------
// misc. C++ helper members ..
// ---------------------------------------------------------------------------
DLL_API void
replace_all(
          std::string& s,
    const std::string& from,
    const std::string& to);

DLL_API std::string& replace_all_ptr(std::string& asm_text);
DLL_API std::string& replace_all_fun(std::string& asm_text);
DLL_API void         replace_all_str(std::string& asm_text , std::ofstream& asm_out);

#endif  // __DBASE2MANY_HPP__
