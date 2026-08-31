// ---------------------------------------------------------------------------
// File: artgs.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_JIT_ARGS_HH__
#define __DBASE2MANY_JIT_ARGS_HH__

# include "stddef.h"
# include "windows.h"

extern "C" {

DLL_API int32_t      JIT_CDECL _jit_args_init(void);
DLL_API void         JIT_CDECL _jit_args_shutdown(void);

DLL_API int32_t      JIT_CDECL _jit_param_count(void);
DLL_API const char * JIT_CDECL _jit_param_str_cstr(int32_t index);

DLL_API const char * JIT_CDECL _jit_command_line_cstr(void);
DLL_API LPCSTR       JIT_CDECL _jit_GetCommandLineA(VOID);

};

#endif
