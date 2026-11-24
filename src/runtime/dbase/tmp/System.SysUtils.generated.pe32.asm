%include "System.SysUtils.generated.pe32.extern.inc"
bits 32


section .text


__dbase_exception_cleanup_all:
    push ebp
    mov ebp, esp
    push ebx
__dbase_exception_cleanup_next:
    mov ebx, dword ptr [__dbase_exception_objects_head]
    test ebx, ebx
    jz __dbase_exception_cleanup_done
    mov eax, dword ptr [ebx+4]
    mov dword ptr [__dbase_exception_objects_head], eax
    mov eax, dword ptr [ebx]
    test eax, eax
    jz __dbase_exception_cleanup_node
    push eax
    call __dbase_exc_object_free
    add esp, 4
__dbase_exception_cleanup_node:
    push ebx
    call __dbase_exc_free
    add esp, 4
    jmp __dbase_exception_cleanup_next
__dbase_exception_cleanup_done:
    pop ebx
    mov esp, ebp
    pop ebp
    ret
; Stage 602: dBASE source methods / JitVmt C ABI
__dbase_cls_tobject___ini__:
    ret
    ; O3: unreferenzierte TObject Standardmethode
    ; O3: unreferenzierte TObject Standardmethode
__dbase_cls_tobject_free:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov eax, dword ptr [ebp+8]
    pop edx
    cmp eax, edx
    setne al
    movzx eax, al
    test eax, eax
    jz __dbase_cls_tobject_free_else_1
    mov eax, dword ptr [ebp+8]
    push eax
    call __dbase_ffi_jit_object_free
    add esp, 4
__dbase_cls_tobject_free_else_1:
    ; O1: entfallene Instruktion
__dbase_cls_tobject_free_source_end:
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_tobject_freeinstance:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov eax, dword ptr [ebp+8]
    pop edx
    cmp eax, edx
    setne al
    movzx eax, al
    test eax, eax
    jz __dbase_cls_tobject_freeinstance_else_1
    mov eax, dword ptr [ebp+8]
    push eax
    call __dbase_ffi_jit_object_instance_free
    add esp, 4
__dbase_cls_tobject_freeinstance_else_1:
    ; O1: entfallene Instruktion
__dbase_cls_tobject_freeinstance_source_end:
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_tobject_classtype:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    push eax
    call __dbase_ffi_jit_object_class_type
    add esp, 4
    ; O1: entfallene Instruktion
__dbase_cls_tobject_classtype_source_end:
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_tobject_classparent:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    push eax
    call __dbase_ffi_jit_object_class_type
    add esp, 4
    push eax
    call __dbase_ffi_jit_class_parent
    add esp, 4
    ; O1: entfallene Instruktion
__dbase_cls_tobject_classparent_source_end:
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_tobject_classnameaddress:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    push eax
    call __dbase_ffi_jit_object_class_type
    add esp, 4
    push eax
    call __dbase_ffi_jit_class_name
    add esp, 4
    ; O1: entfallene Instruktion
__dbase_cls_tobject_classnameaddress_source_end:
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_tobject_classname:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    push eax
    call __dbase_cls_tobject_classnameaddress
    add esp, 4
    ; O1: entfallene Instruktion
__dbase_cls_tobject_classname_source_end:
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_tobject_instancesize:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    push eax
    call __dbase_ffi_jit_object_class_type
    add esp, 4
    push eax
    call __dbase_ffi_jit_class_instance_size
    add esp, 4
    ; O1: entfallene Instruktion
__dbase_cls_tobject_instancesize_source_end:
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_tobject_inheritsfrom:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov eax, dword ptr [ebp+12]
    push eax
    mov eax, dword ptr [ebp+8]
    push eax
    call __dbase_ffi_jit_inherits_from_object
    add esp, 8
    pop edx
    cmp eax, edx
    setne al
    movzx eax, al
    ; O1: entfallene Instruktion
__dbase_cls_tobject_inheritsfrom_source_end:
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_exception___ini__:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    push eax
    call __dbase_cls_tobject___ini__
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov eax, dword ptr [eax+4]
    push eax
    mov eax, __dbase_cls_exception___ini___string_0
    push eax
    mov edx, dword ptr [esp+4]
    mov ecx, dword ptr [esp]
    push __dbase_cls_empty
    push ecx
    push edx
    call __dbase_cls_concat3
    add esp, 12
    push eax
    pop eax
    add esp, 8
    push eax
    mov eax, dword ptr [ebp+12]
    push eax
    mov edx, dword ptr [esp+4]
    mov ecx, dword ptr [esp]
    push __dbase_cls_empty
    push ecx
    push edx
    call __dbase_cls_concat3
    add esp, 12
    push eax
    push dword ptr [esp+8]
    call __dbase_cls_api_LocalFree
    pop eax
    add esp, 8
    push eax
    pop eax
    push eax
    mov eax, dword ptr [ebp+8]
    mov edx, eax
    pop eax
    cmp dword ptr [edx+8], 0
    je __dbase_cls_exception___ini___skip_free_1
    push eax
    push edx
    push dword ptr [edx+4]
    call __dbase_cls_api_LocalFree
    pop edx
    pop eax
__dbase_cls_exception___ini___skip_free_1:
    mov dword ptr [edx+4], eax
    mov dword ptr [edx+8], 1
    mov eax, dword ptr [ebp+8]
    mov eax, dword ptr [eax+4]
    ; O1: entfallene Instruktion
__dbase_cls_exception___ini___source_end:
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_exception_fields_init:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    mov edx, __dbase_cls_exception_default_message
    mov dword ptr [eax+4], edx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_exception_fields_done:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    cmp dword ptr [eax+8], 0
    je __dbase_cls_exception_fields_done_message_skip
    push dword ptr [eax+4]
    call __dbase_cls_api_LocalFree
__dbase_cls_exception_fields_done_message_skip:
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_exception_get_message:
    mov eax, dword ptr [esp+4]
    mov eax, dword ptr [eax+4]
    ret
__dbase_cls_exception_set_message:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_cls_empty
    push __dbase_cls_empty
    push dword ptr [ebp+12]
    call __dbase_cls_concat3
    add esp, 12
    mov ebx, eax
    mov eax, dword ptr [ebp+8]
    cmp dword ptr [eax+8], 0
    je __dbase_cls_exception_set_message_store
    push dword ptr [eax+4]
    call __dbase_cls_api_LocalFree
__dbase_cls_exception_set_message_store:
    mov eax, dword ptr [ebp+8]
    mov dword ptr [eax+4], ebx
    mov dword ptr [eax+8], 1
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_exception_get_code:
    mov eax, dword ptr [esp+4]
    mov eax, dword ptr [eax+12]
    ret
__dbase_cls_exception_set_code:
    mov eax, dword ptr [esp+4]
    mov edx, dword ptr [esp+8]
    mov dword ptr [eax+12], edx
    ret
global __dbase_cls_exception_create
__dbase_cls_exception_create:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_vmt_exception
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_exception_create_done
    push dword ptr [ebp+8]
    push ebx
    call __dbase_cls_exception___ini__
    add esp, 8
__dbase_cls_exception_create_done:
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_dbexception_fields_init:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_init
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_dbexception_fields_done:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_done
    add esp, 4
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_dbexception_create
__dbase_cls_dbexception_create:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_vmt_dbexception
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_dbexception_create_done
    push dword ptr [ebp+8]
    push ebx
    call __dbase_cls_exception___ini__
    add esp, 8
__dbase_cls_dbexception_create_done:
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_eabort_fields_init:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_init
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_eabort_fields_done:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_done
    add esp, 4
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_eabort_create
__dbase_cls_eabort_create:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_vmt_eabort
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_eabort_create_done
    push dword ptr [ebp+8]
    push ebx
    call __dbase_cls_exception___ini__
    add esp, 8
__dbase_cls_eabort_create_done:
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_econverterror_fields_init:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_init
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_econverterror_fields_done:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_done
    add esp, 4
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_econverterror_create
__dbase_cls_econverterror_create:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_vmt_econverterror
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_econverterror_create_done
    push dword ptr [ebp+8]
    push ebx
    call __dbase_cls_exception___ini__
    add esp, 8
__dbase_cls_econverterror_create_done:
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_eoutofmemory_fields_init:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_init
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_eoutofmemory_fields_done:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_done
    add esp, 4
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_eoutofmemory_create
__dbase_cls_eoutofmemory_create:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_vmt_eoutofmemory
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_eoutofmemory_create_done
    push dword ptr [ebp+8]
    push ebx
    call __dbase_cls_exception___ini__
    add esp, 8
__dbase_cls_eoutofmemory_create_done:
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_einouterror_fields_init:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_init
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_einouterror_fields_done:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_done
    add esp, 4
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_einouterror_create
__dbase_cls_einouterror_create:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_vmt_einouterror
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_einouterror_create_done
    push dword ptr [ebp+8]
    push ebx
    call __dbase_cls_exception___ini__
    add esp, 8
__dbase_cls_einouterror_create_done:
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_einvalidcast_fields_init:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_init
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_einvalidcast_fields_done:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_done
    add esp, 4
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_einvalidcast_create
__dbase_cls_einvalidcast_create:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_vmt_einvalidcast
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_einvalidcast_create_done
    push dword ptr [ebp+8]
    push ebx
    call __dbase_cls_exception___ini__
    add esp, 8
__dbase_cls_einvalidcast_create_done:
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_einvalidpointer_fields_init:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_init
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_einvalidpointer_fields_done:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_done
    add esp, 4
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_einvalidpointer_create
__dbase_cls_einvalidpointer_create:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_vmt_einvalidpointer
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_einvalidpointer_create_done
    push dword ptr [ebp+8]
    push ebx
    call __dbase_cls_exception___ini__
    add esp, 8
__dbase_cls_einvalidpointer_create_done:
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_einterror_fields_init:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_init
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_einterror_fields_done:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_done
    add esp, 4
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_einterror_create
__dbase_cls_einterror_create:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_vmt_einterror
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_einterror_create_done
    push dword ptr [ebp+8]
    push ebx
    call __dbase_cls_exception___ini__
    add esp, 8
__dbase_cls_einterror_create_done:
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_edivbyzero_fields_init:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_einterror_fields_init
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_edivbyzero_fields_done:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_einterror_fields_done
    add esp, 4
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_edivbyzero_create
__dbase_cls_edivbyzero_create:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_vmt_edivbyzero
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_edivbyzero_create_done
    push dword ptr [ebp+8]
    push ebx
    call __dbase_cls_exception___ini__
    add esp, 8
__dbase_cls_edivbyzero_create_done:
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_erangeerror_fields_init:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_einterror_fields_init
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_erangeerror_fields_done:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_einterror_fields_done
    add esp, 4
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_erangeerror_create
__dbase_cls_erangeerror_create:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_vmt_erangeerror
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_erangeerror_create_done
    push dword ptr [ebp+8]
    push ebx
    call __dbase_cls_exception___ini__
    add esp, 8
__dbase_cls_erangeerror_create_done:
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_eintoverflow_fields_init:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_einterror_fields_init
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_eintoverflow_fields_done:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_einterror_fields_done
    add esp, 4
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_eintoverflow_create
__dbase_cls_eintoverflow_create:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_vmt_eintoverflow
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_eintoverflow_create_done
    push dword ptr [ebp+8]
    push ebx
    call __dbase_cls_exception___ini__
    add esp, 8
__dbase_cls_eintoverflow_create_done:
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_ematherror_fields_init:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_init
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_ematherror_fields_done:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_done
    add esp, 4
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_ematherror_create
__dbase_cls_ematherror_create:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_vmt_ematherror
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_ematherror_create_done
    push dword ptr [ebp+8]
    push ebx
    call __dbase_cls_exception___ini__
    add esp, 8
__dbase_cls_ematherror_create_done:
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_win32exception___ini__:
    push ebp
    mov ebp, esp
    mov eax, __dbase_cls_win32exception___ini___string_0
    push eax
    mov eax, __dbase_cls_win32exception___ini___string_2
    push eax
    mov edx, dword ptr [esp+4]
    mov ecx, dword ptr [esp]
    push __dbase_cls_empty
    push ecx
    push edx
    call __dbase_cls_concat3
    add esp, 12
    push eax
    pop eax
    add esp, 8
    push eax
    mov eax, __dbase_cls_win32exception___ini___string_4
    push eax
    mov edx, dword ptr [esp+4]
    mov ecx, dword ptr [esp]
    push __dbase_cls_empty
    push ecx
    push edx
    call __dbase_cls_concat3
    add esp, 12
    push eax
    push dword ptr [esp+8]
    call __dbase_cls_api_LocalFree
    pop eax
    add esp, 8
    push eax
    mov eax, dword ptr [ebp+8]
    mov eax, dword ptr [eax+12]
    push eax
    call __dbase_cls_u32toa
    add esp, 4
    push eax
    mov edx, dword ptr [esp+4]
    mov ecx, dword ptr [esp]
    push __dbase_cls_empty
    push ecx
    push edx
    call __dbase_cls_concat3
    add esp, 12
    push eax
    push dword ptr [esp+8]
    call __dbase_cls_api_LocalFree
    push dword ptr [esp+4]
    call __dbase_cls_api_LocalFree
    pop eax
    add esp, 8
    push eax
    mov eax, __dbase_cls_win32exception___ini___string_6
    push eax
    mov edx, dword ptr [esp+4]
    mov ecx, dword ptr [esp]
    push __dbase_cls_empty
    push ecx
    push edx
    call __dbase_cls_concat3
    add esp, 12
    push eax
    push dword ptr [esp+8]
    call __dbase_cls_api_LocalFree
    pop eax
    add esp, 8
    push eax
    mov eax, __dbase_cls_win32exception___ini___string_8
    push eax
    mov edx, dword ptr [esp+4]
    mov ecx, dword ptr [esp]
    push __dbase_cls_empty
    push ecx
    push edx
    call __dbase_cls_concat3
    add esp, 12
    push eax
    push dword ptr [esp+8]
    call __dbase_cls_api_LocalFree
    pop eax
    add esp, 8
    push eax
    mov eax, dword ptr [ebp+12]
    push eax
    mov edx, dword ptr [esp+4]
    mov ecx, dword ptr [esp]
    push __dbase_cls_empty
    push ecx
    push edx
    call __dbase_cls_concat3
    add esp, 12
    push eax
    push dword ptr [esp+8]
    call __dbase_cls_api_LocalFree
    pop eax
    add esp, 8
    push eax
    pop eax
    push eax
    mov eax, dword ptr [ebp+8]
    mov edx, eax
    pop eax
    cmp dword ptr [edx+8], 0
    je __dbase_cls_win32exception___ini___skip_free_1
    push eax
    push edx
    push dword ptr [edx+4]
    call __dbase_cls_api_LocalFree
    pop edx
    pop eax
__dbase_cls_win32exception___ini___skip_free_1:
    mov dword ptr [edx+4], eax
    mov dword ptr [edx+8], 1
    mov eax, dword ptr [ebp+8]
    mov eax, dword ptr [eax+4]
    ; O1: entfallene Instruktion
__dbase_cls_win32exception___ini___source_end:
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_win32exception_fields_init:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_init
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_win32exception_fields_done:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_done
    add esp, 4
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_win32exception_create
__dbase_cls_win32exception_create:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_vmt_win32exception
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_win32exception_create_done
    push dword ptr [ebp+8]
    push ebx
    call __dbase_cls_win32exception___ini__
    add esp, 8
__dbase_cls_win32exception_create_done:
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_win32exception_create_with_code:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_vmt_win32exception
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_win32exception_create_with_code_done
    mov edx, dword ptr [ebp+12]
    mov dword ptr [ebx+12], edx
    push dword ptr [ebp+8]
    push ebx
    call __dbase_cls_win32exception___ini__
    add esp, 8
__dbase_cls_win32exception_create_with_code_done:
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_win32fileexception_fields_init:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_win32exception_fields_init
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_win32fileexception_fields_done:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_win32exception_fields_done
    add esp, 4
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_win32fileexception_create
__dbase_cls_win32fileexception_create:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_vmt_win32fileexception
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_win32fileexception_create_done
    push dword ptr [ebp+8]
    push ebx
    call __dbase_cls_win32exception___ini__
    add esp, 8
__dbase_cls_win32fileexception_create_done:
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_win32fileexception_create_with_code:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_vmt_win32fileexception
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_win32fileexception_create_with_code_done
    mov edx, dword ptr [ebp+12]
    mov dword ptr [ebx+12], edx
    push dword ptr [ebp+8]
    push ebx
    call __dbase_cls_win32exception___ini__
    add esp, 8
__dbase_cls_win32fileexception_create_with_code_done:
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_concat3:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov esi, dword ptr [ebp+8]
    mov edi, dword ptr [ebp+12]
    mov edx, dword ptr [ebp+16]
    test esi, esi
    jnz __dbase_cls_concat3_first
    mov esi, __dbase_cls_empty
__dbase_cls_concat3_first:
    test edi, edi
    jnz __dbase_cls_concat3_second
    mov edi, __dbase_cls_empty
__dbase_cls_concat3_second:
    test edx, edx
    jnz __dbase_cls_concat3_third
    mov edx, __dbase_cls_empty
__dbase_cls_concat3_third:
    push edx
    push esi
    call __dbase_cls_api_lstrlenA
    mov ebx, eax
    push edi
    call __dbase_cls_api_lstrlenA
    add ebx, eax
    push dword ptr [esp]
    call __dbase_cls_api_lstrlenA
    add ebx, eax
    add ebx, 1
    push ebx
    push 64
    call __dbase_cls_api_LocalAlloc
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_concat3_done
    push esi
    push ebx
    call __dbase_cls_api_lstrcpyA
    push edi
    push ebx
    call __dbase_cls_api_lstrcatA
    push dword ptr [esp]
    push ebx
    call __dbase_cls_api_lstrcatA
__dbase_cls_concat3_done:
    add esp, 4
    mov eax, ebx
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_u32toa:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    push 16
    push 64
    call __dbase_cls_api_LocalAlloc
    mov edi, eax
    test eax, eax
    jz __dbase_cls_u32toa32_done
    lea esi, [edi+15]
    mov byte ptr [esi], 0
    mov eax, dword ptr [ebp+8]
    mov ebx, 10
__dbase_cls_u32toa32_digits:
    xor edx, edx
    div ebx
    add edx, 48
    dec esi
    mov byte ptr [esi], dl
    test eax, eax
    jne __dbase_cls_u32toa32_digits
    mov edx, edi
__dbase_cls_u32toa32_copy:
    movzx ebx, byte ptr [esi]
    mov byte ptr [edx], bl
    inc esi
    inc edx
    test ebx, ebx
    jne __dbase_cls_u32toa32_copy
    mov eax, edi
__dbase_cls_u32toa32_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_tobject_create
__dbase_cls_tobject_create:
    push __dbase_vmt_tobject
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    ret


; Stage 679: O3 runtime ABI import guard
__dbase_o3_abi_guard:
    call __dbase_o3_default_vmt_abi
    ret

section .data
; Stage 600: JitVmt headers: parent, name, instance_size, init, finalize, destroy
__dbase_cls_exception___ini___string_0:
    db 58, 32, 0
__dbase_cls_exception_default_message:
    db 69, 114, 114, 111, 114, 46, 0
__dbase_cls_win32exception___ini___string_0:
    db 87, 105, 110, 100, 111, 119, 115, 32, 70, 101, 104, 108, 101, 114, 0
__dbase_cls_win32exception___ini___string_2:
    db 10, 0
__dbase_cls_win32exception___ini___string_4:
    db 67, 111, 100, 101, 58, 32, 0
__dbase_cls_win32exception___ini___string_6:
    db 10, 0
__dbase_cls_win32exception___ini___string_8:
    db 84, 101, 120, 116, 58, 32, 0
__dbase_cls_empty:
    db 0
; Stage 679: TObject builtin virtual methods; DLL fallback safe
; Stage 670: shared VMT method tables
    ; O3: TObject Standardtabelle liegt in libd64_qt5.dll
    ; O3: TObject Standardtabelle liegt in libd64_qt5.dll
    ; O3: TObject Standardtabelle liegt in libd64_qt5.dll
    ; O3: TObject Standardtabelle liegt in libd64_qt5.dll
    ; O3: TObject Standardtabelle liegt in libd64_qt5.dll
    ; O3: TObject Standardtabelle liegt in libd64_qt5.dll
    ; O3: TObject Standardtabelle liegt in libd64_qt5.dll
    ; O3: TObject Standardtabelle liegt in libd64_qt5.dll
    ; O3: TObject Standardtabelle liegt in libd64_qt5.dll
    ; O3: TObject Standardtabelle liegt in libd64_qt5.dll
global __dbase_vmt_tobject
__dbase_vmt_tobject:
    dd 0
    dd __dbase_vmt_tobject_name
    dd 0x80000004
    dd __dbase_cls_tobject___ini__
    dd 0
    dd 0
__dbase_vmt_tobject_name:
    db 84, 79, 98, 106, 101, 99, 116, 0
global __dbase_vmt_exception
__dbase_vmt_exception:
    dd __dbase_vmt_tobject
    dd __dbase_vmt_exception_name
    dd 0x80000014
    dd __dbase_cls_exception_fields_init
    dd __dbase_cls_exception_fields_done
    dd 0
__dbase_vmt_exception_name:
    db 69, 120, 99, 101, 112, 116, 105, 111, 110, 0
global __dbase_vmt_dbexception
__dbase_vmt_dbexception:
    dd __dbase_vmt_exception
    dd __dbase_vmt_dbexception_name
    dd 0x80000014
    dd __dbase_cls_dbexception_fields_init
    dd __dbase_cls_dbexception_fields_done
    dd 0
__dbase_vmt_dbexception_name:
    db 68, 98, 69, 120, 99, 101, 112, 116, 105, 111, 110, 0
global __dbase_vmt_eabort
__dbase_vmt_eabort:
    dd __dbase_vmt_exception
    dd __dbase_vmt_eabort_name
    dd 0x80000014
    dd __dbase_cls_eabort_fields_init
    dd __dbase_cls_eabort_fields_done
    dd 0
__dbase_vmt_eabort_name:
    db 69, 65, 98, 111, 114, 116, 0
global __dbase_vmt_econverterror
__dbase_vmt_econverterror:
    dd __dbase_vmt_exception
    dd __dbase_vmt_econverterror_name
    dd 0x80000014
    dd __dbase_cls_econverterror_fields_init
    dd __dbase_cls_econverterror_fields_done
    dd 0
__dbase_vmt_econverterror_name:
    db 69, 67, 111, 110, 118, 101, 114, 116, 69, 114, 114, 111, 114, 0
global __dbase_vmt_eoutofmemory
__dbase_vmt_eoutofmemory:
    dd __dbase_vmt_exception
    dd __dbase_vmt_eoutofmemory_name
    dd 0x80000014
    dd __dbase_cls_eoutofmemory_fields_init
    dd __dbase_cls_eoutofmemory_fields_done
    dd 0
__dbase_vmt_eoutofmemory_name:
    db 69, 79, 117, 116, 79, 102, 77, 101, 109, 111, 114, 121, 0
global __dbase_vmt_einouterror
__dbase_vmt_einouterror:
    dd __dbase_vmt_exception
    dd __dbase_vmt_einouterror_name
    dd 0x80000014
    dd __dbase_cls_einouterror_fields_init
    dd __dbase_cls_einouterror_fields_done
    dd 0
__dbase_vmt_einouterror_name:
    db 69, 73, 110, 79, 117, 116, 69, 114, 114, 111, 114, 0
global __dbase_vmt_einvalidcast
__dbase_vmt_einvalidcast:
    dd __dbase_vmt_exception
    dd __dbase_vmt_einvalidcast_name
    dd 0x80000014
    dd __dbase_cls_einvalidcast_fields_init
    dd __dbase_cls_einvalidcast_fields_done
    dd 0
__dbase_vmt_einvalidcast_name:
    db 69, 73, 110, 118, 97, 108, 105, 100, 67, 97, 115, 116, 0
global __dbase_vmt_einvalidpointer
__dbase_vmt_einvalidpointer:
    dd __dbase_vmt_exception
    dd __dbase_vmt_einvalidpointer_name
    dd 0x80000014
    dd __dbase_cls_einvalidpointer_fields_init
    dd __dbase_cls_einvalidpointer_fields_done
    dd 0
__dbase_vmt_einvalidpointer_name:
    db 69, 73, 110, 118, 97, 108, 105, 100, 80, 111, 105, 110, 116, 101, 114, 0
global __dbase_vmt_einterror
__dbase_vmt_einterror:
    dd __dbase_vmt_exception
    dd __dbase_vmt_einterror_name
    dd 0x80000014
    dd __dbase_cls_einterror_fields_init
    dd __dbase_cls_einterror_fields_done
    dd 0
__dbase_vmt_einterror_name:
    db 69, 73, 110, 116, 69, 114, 114, 111, 114, 0
global __dbase_vmt_edivbyzero
__dbase_vmt_edivbyzero:
    dd __dbase_vmt_einterror
    dd __dbase_vmt_edivbyzero_name
    dd 0x80000014
    dd __dbase_cls_edivbyzero_fields_init
    dd __dbase_cls_edivbyzero_fields_done
    dd 0
__dbase_vmt_edivbyzero_name:
    db 69, 68, 105, 118, 66, 121, 90, 101, 114, 111, 0
global __dbase_vmt_erangeerror
__dbase_vmt_erangeerror:
    dd __dbase_vmt_einterror
    dd __dbase_vmt_erangeerror_name
    dd 0x80000014
    dd __dbase_cls_erangeerror_fields_init
    dd __dbase_cls_erangeerror_fields_done
    dd 0
__dbase_vmt_erangeerror_name:
    db 69, 82, 97, 110, 103, 101, 69, 114, 114, 111, 114, 0
global __dbase_vmt_eintoverflow
__dbase_vmt_eintoverflow:
    dd __dbase_vmt_einterror
    dd __dbase_vmt_eintoverflow_name
    dd 0x80000014
    dd __dbase_cls_eintoverflow_fields_init
    dd __dbase_cls_eintoverflow_fields_done
    dd 0
__dbase_vmt_eintoverflow_name:
    db 69, 73, 110, 116, 79, 118, 101, 114, 102, 108, 111, 119, 0
global __dbase_vmt_ematherror
__dbase_vmt_ematherror:
    dd __dbase_vmt_exception
    dd __dbase_vmt_ematherror_name
    dd 0x80000014
    dd __dbase_cls_ematherror_fields_init
    dd __dbase_cls_ematherror_fields_done
    dd 0
__dbase_vmt_ematherror_name:
    db 69, 77, 97, 116, 104, 69, 114, 114, 111, 114, 0
global __dbase_vmt_win32exception
__dbase_vmt_win32exception:
    dd __dbase_vmt_exception
    dd __dbase_vmt_win32exception_name
    dd 0x80000014
    dd __dbase_cls_win32exception_fields_init
    dd __dbase_cls_win32exception_fields_done
    dd 0
__dbase_vmt_win32exception_name:
    db 87, 105, 110, 51, 50, 69, 120, 99, 101, 112, 116, 105, 111, 110, 0
global __dbase_vmt_win32fileexception
__dbase_vmt_win32fileexception:
    dd __dbase_vmt_win32exception
    dd __dbase_vmt_win32fileexception_name
    dd 0x80000014
    dd __dbase_cls_win32fileexception_fields_init
    dd __dbase_cls_win32fileexception_fields_done
    dd 0
__dbase_vmt_win32fileexception_name:
    db 87, 105, 110, 51, 50, 70, 105, 108, 101, 69, 120, 99, 101, 112, 116, 105, 111, 110, 0

__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_text_1:
    db 85, 110, 98, 101, 104, 97, 110, 100, 101, 108, 116, 101, 32, 69, 120, 99, 101, 112, 116, 105, 111, 110, 58, 32
__dbase_text_2:
    db 58, 32
__dbase_text_3:
    db 13, 10
__dbase_output_format_screen:
    dd 1
__dbase_output_debug_override:
    dd -1
__dbase_workstation_lazy_console_marker:
    db 68, 54, 52, 68, 66, 65, 83, 69, 95, 76, 65, 90, 89, 95, 67, 79, 78, 83, 79, 76, 69, 95, 86, 49, 0

section .bss

__dbase_ffi_return:
    resq 1
__dbase_temp_number:
    resd 1
__dbase_temp_number_hi:
    resd 1
__dbase_int_cw:
    resw 1
__dbase_int_cw_trunc:
    resw 1
__dbase_call_number:
    resq 1
__dbase_format_buffer:
    resd 1
__dbase_exit_code:
    resd 1
__dbase_output_debug_visible:
    resd 1
__dbase_console_number_len:
    resd 1
__dbase_exception_id:
    resd 1
__dbase_exception_code:
    resd 1
__dbase_exception_message_type:
    resd 1
__dbase_exception_message_num:
    resq 1
__dbase_exception_message_ptr:
    resd 1
__dbase_exception_message_len:
    resd 1
__dbase_exception_class_type:
    resd 1
__dbase_exception_class_num:
    resq 1
__dbase_exception_class_ptr:
    resd 1
__dbase_exception_class_len:
    resd 1
__dbase_exception_object_type:
    resd 1
__dbase_exception_object_num:
    resq 1
__dbase_exception_object_ptr:
    resd 1
__dbase_exception_object_len:
    resd 1
__dbase_exception_cstr_type:
    resd 1
__dbase_exception_cstr_num:
    resq 1
__dbase_exception_cstr_ptr:
    resd 1
__dbase_exception_cstr_len:
    resd 1
__dbase_exception_objects_head:
    resd 1
