// ---------------------------------------------------------------------------
// File: jitObject.cc
// Note: Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "iostream.h"
# include "stddef.h"
# include "memory.h"
# include "jitObject.h"
# include "windows.h"

# ifdef __cplusplus
extern "C" {
# endif

typedef struct JitObjectHeader {
    JitVmt *vmt;
    
}   JitObjectHeader;

// Stage 534: allocation registry (no heap allocations inside the guard).
// Guarding the lifetime *before* accessing the object VMT avoids dereferencing
// stale pointers in the common double-Free path. Addresses may be reused by
// malloc; a later allocation then creates a new live generation at that slot.
// This is bounded diagnostic tracking, not a general-purpose heap verifier.
#define D64_OBJECT_REGISTRY_CAPACITY 8192
struct D64TrackedObject {
    const void *address;
    unsigned state;  // 0=empty, 1=live, 2=destroying, 3=freed, 4=finalizing
    unsigned generation;
};
static D64TrackedObject g_tracked[D64_OBJECT_REGISTRY_CAPACITY];
static volatile int g_registry_lock = 0;
static unsigned g_generation = 0;

static void d64_lock_objects()
{
    while (__sync_lock_test_and_set(&g_registry_lock, 1)) {
        __asm__ volatile("pause");
    }
}
static void d64_unlock_objects() { __sync_lock_release(&g_registry_lock); }

// Returns: 1=accepted, 0=unknown, -1=already freeing/freed or full.
// action=0 register, 1 begin destroying, 2 begin freeing, 3 validate.
static int d64_object_transition(const void *ptr, unsigned action)
{
    if (!ptr) return 0;
    d64_lock_objects();
    unsigned index = (unsigned)(((uintptr_t)ptr >> 4) % D64_OBJECT_REGISTRY_CAPACITY);
    unsigned empty_slot = D64_OBJECT_REGISTRY_CAPACITY;
    unsigned freed_slot = D64_OBJECT_REGISTRY_CAPACITY;
    for (unsigned count=0; count<D64_OBJECT_REGISTRY_CAPACITY; ++count) {
        unsigned i = (index + count) % D64_OBJECT_REGISTRY_CAPACITY;
        D64TrackedObject *slot = &g_tracked[i];
        if (!slot->address) { empty_slot = i; break; }
        if (slot->address == ptr) {
            int result = 0;
            if (action == 0) {
                if (slot->state == 3) {
                    slot->state = 1;
                    slot->generation = ++g_generation;
                    result = 1;
                } else result = -1;
            } else if (action == 1) {
                if (slot->state == 1) { slot->state = 2; result = 1; }
                else result = -1;
            } else if (action == 2) {
                if (slot->state == 1 || slot->state == 2) {
                    slot->state = 4; // delay final free until finalizer returns
                    result = 1;
                } else result = -1;
            } else if (action == 4) {
                if (slot->state == 4) { slot->state = 3; result = 1; }
                else result = -1;
            } else result = (slot->state == 1 || slot->state == 2 || slot->state == 4) ? 1 : -1;
            d64_unlock_objects();
            return result;
        }
        if (slot->state == 3 && freed_slot == D64_OBJECT_REGISTRY_CAPACITY)
            freed_slot = i;
    }
    int result = 0;
    if (action == 0) {
        unsigned i = empty_slot != D64_OBJECT_REGISTRY_CAPACITY ? empty_slot : freed_slot;
        if (i != D64_OBJECT_REGISTRY_CAPACITY) {
            g_tracked[i].address = ptr;
            g_tracked[i].state = 1;
            g_tracked[i].generation = ++g_generation;
            result = 1;
        } else result = -1;
    }
    d64_unlock_objects();
    return result;
}

#ifdef D64_OBJECT_LIFETIME_TRACE
static void d64_trace_object(const char *event, const void *instance)
{
    // Opt-in: compile the runtime with -DD64_OBJECT_LIFETIME_TRACE.
    // Print outside the registry lock to avoid allocator recursion.
    typedef DWORD (JIT_STDCALL *D64IdFn)(void);
    HMODULE kernel = LoadLibraryA("kernel32.dll");
    D64IdFn pid_fn = kernel ? (D64IdFn)GetProcAddress(kernel, "GetCurrentProcessId") : nullptr;
    D64IdFn tid_fn = kernel ? (D64IdFn)GetProcAddress(kernel, "GetCurrentThreadId") : nullptr;
    unsigned pid = pid_fn ? pid_fn() : 0;
    unsigned tid = tid_fn ? tid_fn() : 0;
    _jit_printf("[jit-object] %s pid=%u tid=%u ptr=%p\n", event, pid, tid, instance);
}
#else
static void d64_trace_object(const char*, const void*) { }
#endif

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

    if (d64_object_transition(object_header, 0) != 1) {
        _jit_free(object_header);
        jit_set_error(JIT_OBJECT_ERROR_REGISTRY_FULL, "Object allocation registry exhausted");
        return nullptr;
    }
    object_header->vmt = vmt;
    d64_trace_object("alloc", object_header);

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

    // Mark the allocation as freed while its address is still valid.
    // A concurrent or repeated Free now fails before the VMT dereference.
    if (d64_object_transition(instance, 2) != 1) {
        jit_set_error(JIT_OBJECT_ERROR_DOUBLE_FREE,
                      "Object already freed, is being freed, or was never allocated here");
        d64_trace_object("invalid-free", instance);
        return;
    }
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
    d64_trace_object("free", instance);
    d64_object_transition(instance, 4); // state=freed before releasing heap
    _jit_free(instance);
}

void JIT_CDECL
jit_object_free(void *instance)
{
    JitVmt *vmt;

    jit_object_error_clear();

    if (!instance)
        return;

    if (d64_object_transition(instance, 1) != 1) {
        jit_set_error(JIT_OBJECT_ERROR_DOUBLE_FREE,
                      "Repeated or concurrent jit_object_free detected");
        d64_trace_object("double-free", instance);
        return;
    }
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

    if (d64_object_transition(instance, 3) != 1) {
        jit_set_error(JIT_OBJECT_ERROR_UNTRACKED_OBJECT,
                      "Object VMT requested for invalid or freed pointer");
        return nullptr;
    }
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
