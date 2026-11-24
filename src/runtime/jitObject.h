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
// +20  destroy (legacy) / shared method table pointer (compact)
// +24  first virtual method slot (legacy only)
//
// Stage 670 compact VMT: instance_size bit 31 marks the shared-table ABI.
// Stage 679 O3: a null compact-table pointer selects the nine built-in
// TObject method pointers contained in libd64_qt5.dll.
// In that case the word at +20 is a pointer to a shared table containing
// destroy at index 0 and virtual methods at indices 1..8.  All older VMTs
// without the flag continue to use the original inline virtual method slots.
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
    JIT_OBJECT_ERROR_INVALID_VIRTUAL_SLOT,
    JIT_OBJECT_ERROR_DOUBLE_FREE,
    JIT_OBJECT_ERROR_UNTRACKED_OBJECT,
    JIT_OBJECT_ERROR_REGISTRY_FULL
};

enum {
    JIT_VMT_PARENT_OFFSET       = 0,
    JIT_VMT_CLASS_NAME_OFFSET   = 4,
    JIT_VMT_INSTANCE_SIZE       = 8,
    JIT_VMT_INITIALIZE_OFFSET   = 12,
    JIT_VMT_FINALIZE_OFFSET     = 16,
    JIT_VMT_DESTROY_OFFSET      = 20,
    JIT_VMT_METHOD_BASE_OFFSET  = 24,
    JIT_VMT_SHARED_METHOD_FLAG = 0x80000000u,
    JIT_VMT_INSTANCE_SIZE_MASK = 0x7fffffffu,
    JIT_VMT_BASE_METHOD_COUNT = 8
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
// ABI exports used by native dBASE code (existing Stage-600 names).
DLL_API void * JIT_CDECL jit_object_instance_new(JitVmt *vmt);
DLL_API void   JIT_CDECL jit_object_instance_free(void *instance);

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
// Runtime capability probe: O3 default TObject method-table sentinel.
DLL_API uint32_t JIT_CDECL jit_default_tobject_vmt_abi(void);

// ---------------------------------------------------------------------------
// Virtual method lookup
// ---------------------------------------------------------------------------
DLL_API void * JIT_CDECL jit_get_virtual_vmt   (JitVmt  *vmt,      uint32_t slot_index);
DLL_API void * JIT_CDECL jit_get_virtual_object(void    *instance, uint32_t slot_index);

# ifdef __cplusplus
};
# endif

# endif
