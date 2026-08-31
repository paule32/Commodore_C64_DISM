// ---------------------------------------------------------------------------
// File: jitObject.h
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_JITOBJECT_HH__
#define __DBASE2MANY_JITOBJECT_HH__

# pragma once

# include "stddef.h"

# ifdef __cplusplus
extern "C" {
# endif

typedef struct JitVmt JitVmt;

typedef void (JIT_CDECL *JitInitializeProc)(void *instance);
typedef void (JIT_CDECL *JitFinalizeProc)(void *instance);
typedef void (JIT_CDECL *JitDestroyProc)(void *instance);
typedef void (JIT_CDECL *JitObjectErrorHook)(int error_code, const char *message);

// ---------------------------------------------------------------------------
// PE32 layout:
//
// +0   parent
// +4   class_name
// +8   instance_size
// +12  initialize_instance
// +16  finalize_instance
// +20  destroy
// +24  first virtual method slot
//
// Additional virtual slots are stored directly behind this header.
// ---------------------------------------------------------------------------
struct JitVmt {
    JitVmt           * parent;
    const char       * class_name;
    uint32_t           instance_size;
    JitInitializeProc  initialize_instance;
    JitFinalizeProc    finalize_instance;
    JitDestroyProc     destroy;
};

enum JitObjectError {
    JIT_OBJECT_ERROR_NONE = 0,
    JIT_OBJECT_ERROR_INVALID_VMT,
    JIT_OBJECT_ERROR_INVALID_OBJECT,
    JIT_OBJECT_ERROR_OUT_OF_MEMORY,
    JIT_OBJECT_ERROR_INVALID_VIRTUAL_SLOT
};

enum {
    JIT_VMT_PARENT_OFFSET       = 0,
    JIT_VMT_CLASS_NAME_OFFSET   = 4,
    JIT_VMT_INSTANCE_SIZE       = 8,
    JIT_VMT_INITIALIZE_OFFSET   = 12,
    JIT_VMT_FINALIZE_OFFSET     = 16,
    JIT_VMT_DESTROY_OFFSET      = 20,
    JIT_VMT_METHOD_BASE_OFFSET  = 24
};

// ---------------------------------------------------------------------------
// Error handling
// ---------------------------------------------------------------------------
DLL_API void JIT_CDECL
_jit_object_set_error_hook(JitObjectErrorHook hook);

DLL_API int          JIT_CDECL jit_object_error_last        (void);
DLL_API const char * JIT_CDECL jit_object_error_last_message(void);
DLL_API void         JIT_CDECL jit_object_error_clear       (void);

// ---------------------------------------------------------------------------
// Allocation and destruction
// ---------------------------------------------------------------------------
DLL_API void * JIT_CDECL jit_object_new_instance(JitVmt *vmt);

DLL_API void   JIT_CDECL jit_object_free_instance(void *instance);
DLL_API void   JIT_CDECL jit_object_free         (void *instance);

// ---------------------------------------------------------------------------
// Object and class information
// ---------------------------------------------------------------------------
DLL_API JitVmt     * JIT_CDECL jit_object_class_type(void *instance);
DLL_API JitVmt     * JIT_CDECL jit_class_parent        (JitVmt *vmt);
DLL_API const char * JIT_CDECL jit_class_name          (JitVmt *vmt);
DLL_API uint32_t     JIT_CDECL jit_class_instance_size (JitVmt *vmt);

DLL_API int JIT_CDECL jit_inherits_from_class (JitVmt *current_class, JitVmt *expected_class);
DLL_API int JIT_CDECL jit_inherits_from_object(void   *instance,      JitVmt *expected_class);

// ---------------------------------------------------------------------------
// Virtual method lookup
// ---------------------------------------------------------------------------
DLL_API void * JIT_CDECL jit_get_virtual_vmt   (JitVmt  *vmt,      uint32_t slot_index);
DLL_API void * JIT_CDECL jit_get_virtual_object(void    *instance, uint32_t slot_index);

# ifdef __cplusplus
};
# endif

# endif
