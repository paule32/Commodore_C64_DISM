// ---------------------------------------------------------------------------
// File: jitObject.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "iostream.h"
# include "stddef.h"
# include "memory.h"
# include "jitObject.h"

# ifdef __cplusplus
extern "C" {
# endif

typedef struct JitObjectHeader {
    JitVmt *vmt;
    
}   JitObjectHeader;

static int                g_last_error         = JIT_OBJECT_ERROR_NONE;
static const char *       g_last_error_message = "";
static JitObjectErrorHook g_error_hook         = nullptr;

static void
jit_set_error(
    int error_code,
    const char *message)
{
    g_last_error = error_code;
    g_last_error_message = message ? message : "";

    if (g_error_hook)
        g_error_hook(g_last_error, g_last_error_message);
}

static int
jit_valid_vmt(JitVmt *vmt)
{
    if (!vmt)
    {
        jit_set_error(
            JIT_OBJECT_ERROR_INVALID_VMT,
            "VMT pointer is null"
        );
        return 0;
    }

    if (vmt->instance_size < sizeof(JitObjectHeader))
    {
        jit_set_error(
            JIT_OBJECT_ERROR_INVALID_VMT,
            "VMT instance_size is smaller than the object header"
        );
        return 0;
    }

    return 1;
}

void JIT_CDECL
jit_object_error_set_hook(JitObjectErrorHook hook)
{
    g_error_hook = hook;
}

int JIT_CDECL
jit_object_error_last(void)
{
    return g_last_error;
}

const char *JIT_CDECL
jit_object_error_last_message(void)
{
    return g_last_error_message;
}

void JIT_CDECL
jit_object_error_clear(void)
{
    g_last_error = JIT_OBJECT_ERROR_NONE;
    g_last_error_message = "";
}

void *JIT_CDECL
jit_object_instance_new(JitVmt *vmt)
{
    JitObjectHeader *object_header;

    jit_object_error_clear();

    if (!jit_valid_vmt(vmt))
        return nullptr;

    object_header = (JitObjectHeader *)_jit_calloc(
        1,
        (size_t)vmt->instance_size
    );

    if (!object_header)
    {
        jit_set_error(
            JIT_OBJECT_ERROR_OUT_OF_MEMORY,
            "Could not allocate object instance"
        );
        return nullptr;
    }

    object_header->vmt = vmt;

    if (vmt->initialize_instance)
        vmt->initialize_instance(object_header);

    return object_header;
}

void JIT_CDECL
jit_object_instance_free(void *instance)
{
    JitObjectHeader *object_header;
    JitVmt *vmt;

    jit_object_error_clear();

    if (!instance)
        return;

    object_header = (JitObjectHeader *)instance;
    vmt = object_header->vmt;

    if (!jit_valid_vmt(vmt))
    {
        jit_set_error(
            JIT_OBJECT_ERROR_INVALID_OBJECT,
            "Object contains an invalid VMT pointer"
        );
        return;
    }

    if (vmt->finalize_instance)
        vmt->finalize_instance(instance);

    object_header->vmt = nullptr;
    _jit_free(instance);
}

void JIT_CDECL
jit_object_free(void *instance)
{
    JitVmt *vmt;

    jit_object_error_clear();

    if (!instance)
        return;

    vmt = jit_object_class_type(instance);

    if (!vmt)
        return;

    /*
     * Convention:
     * destroy executes the virtual destructor chain, but does not free
     * the memory. Memory is released exactly once below.
     */
    if (vmt->destroy)
        vmt->destroy(instance);

    jit_object_instance_free(instance);
}

JitVmt *JIT_CDECL
jit_object_class_type(void *instance)
{
    JitObjectHeader *object_header;

    jit_object_error_clear();

    if (!instance)
        return nullptr;

    object_header = (JitObjectHeader *)instance;

    if (!jit_valid_vmt(object_header->vmt))
    {
        jit_set_error(
            JIT_OBJECT_ERROR_INVALID_OBJECT,
            "Object contains an invalid VMT pointer"
        );
        return nullptr;
    }

    return object_header->vmt;
}

JitVmt *JIT_CDECL
jit_class_parent(JitVmt *vmt)
{
    jit_object_error_clear();

    if (!jit_valid_vmt(vmt))
        return nullptr;

    return vmt->parent;
}

const char *JIT_CDECL
jit_class_name(JitVmt *vmt)
{
    if (!vmt) {
        _jit_printf("vmt is nil\n");
        return "";
    }

    if (vmt->class_name != nullptr) {
        return vmt->class_name;
    }   else {
        return "<unknown>";
    }
}

uint32_t JIT_CDECL
jit_class_instance_size(JitVmt *vmt)
{
    jit_object_error_clear();

    if (!jit_valid_vmt(vmt))
        return 0;

    return vmt->instance_size;
}

int JIT_CDECL
jit_inherits_from_class(
    JitVmt *current_class,
    JitVmt *expected_class)
{
    jit_object_error_clear();

    if (!current_class || !expected_class)
        return 0;

    while (current_class)
    {
        if (current_class == expected_class)
            return 1;

        current_class = current_class->parent;
    }

    return 0;
}

int JIT_CDECL
jit_inherits_from_object(
    void   *instance,
    JitVmt *expected_class)
{
    JitVmt *current_class;

    jit_object_error_clear();

    if (!instance || !expected_class)
        return 0;

    current_class = jit_object_class_type(instance);

    if (!current_class)
        return 0;

    return jit_inherits_from_class(
        current_class,
        expected_class
    );
}

void *JIT_CDECL
jit_get_virtual_vmt(
    JitVmt  *vmt,
    uint32_t slot_index)
{
    void **slot_table;
    void *method;

    jit_object_error_clear();

    if (!jit_valid_vmt(vmt))
        return nullptr;

    slot_table = (void **)(((unsigned char *)vmt) + sizeof(JitVmt));
    method = slot_table[slot_index];

    if (!method)
    {
        jit_set_error(
            JIT_OBJECT_ERROR_INVALID_VIRTUAL_SLOT,
            "Virtual method slot is null"
        );
        return nullptr;
    }

    return method;
}

void *JIT_CDECL
jit_get_virtual_object(
    void     *instance,
    uint32_t  slot_index)
{
    JitVmt *vmt;

    jit_object_error_clear();

    vmt = jit_object_class_type(instance);

    if (!vmt)
        return nullptr;

    return jit_get_virtual_vmt(
        vmt,
        slot_index
    );
}

# ifdef __cplusplus
};
# endif
