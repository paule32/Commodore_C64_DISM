%include "System.SysUtils.generated.pe32.extern.inc"
bits 32
; dBASE Runtime CLASS DLL – no Qt GUI / no EXE startup
global __d64_dll_entry
entry __d64_dll_entry
export "__dbase_cls_tobject_vmt", __dbase_cls_tobject_vmt
export "__dbase_cls_tobject_create", __dbase_cls_tobject_create
export "__dbase_cls_exception_vmt", __dbase_cls_exception_vmt
export "__dbase_cls_exception_create", __dbase_cls_exception_create
export "__dbase_cls_exception___ini__", __dbase_cls_exception___ini__
export "__dbase_cls_exception_get_message", __dbase_cls_exception_get_message
export "__dbase_cls_exception_set_message", __dbase_cls_exception_set_message
export "__dbase_cls_tobject___ini__", __dbase_cls_tobject___ini__
export "__dbase_cls_tobject___del__", __dbase_cls_tobject___del__
export "__dbase_cls_tobject_free", __dbase_cls_tobject_free
export "__dbase_cls_tobject_freeinstance", __dbase_cls_tobject_freeinstance
export "__dbase_cls_tobject_classtype", __dbase_cls_tobject_classtype
export "__dbase_cls_tobject_classparent", __dbase_cls_tobject_classparent
export "__dbase_cls_tobject_classnameaddress", __dbase_cls_tobject_classnameaddress
export "__dbase_cls_tobject_classname", __dbase_cls_tobject_classname
export "__dbase_cls_tobject_instancesize", __dbase_cls_tobject_instancesize
export "__dbase_cls_tobject_inheritsfrom", __dbase_cls_tobject_inheritsfrom

section .text

__d64_dll_entry:
    push 1
    pop eax
    ret 12

; Stage 602: dBASE source methods / JitVmt C ABI
__dbase_cls_tobject___ini__:
    ret
__dbase_cls_tobject___del__:
    ret
__dbase_cls_tobject_free:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    test eax, eax
    jz __dbase_cls_tobject_free_else_1
    mov eax, dword ptr [ebp+8]
    push eax
    call __dbase_ffi_jit_object_free
    add esp, 4
__dbase_cls_tobject_free_else_1:
    jmp __dbase_cls_tobject_free_source_end
__dbase_cls_tobject_free_source_end:
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_tobject_freeinstance:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    test eax, eax
    jz __dbase_cls_tobject_freeinstance_else_1
    mov eax, dword ptr [ebp+8]
    push eax
    call __dbase_ffi_jit_object_instance_free
    add esp, 4
__dbase_cls_tobject_freeinstance_else_1:
    jmp __dbase_cls_tobject_freeinstance_source_end
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
    jmp __dbase_cls_tobject_classtype_source_end
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
    jmp __dbase_cls_tobject_classparent_source_end
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
    jmp __dbase_cls_tobject_classnameaddress_source_end
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
    jmp __dbase_cls_tobject_classname_source_end
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
    jmp __dbase_cls_tobject_instancesize_source_end
__dbase_cls_tobject_instancesize_source_end:
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_tobject_inheritsfrom:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+12]
    push eax
    mov eax, dword ptr [ebp+8]
    push eax
    call __dbase_ffi_jit_inherits_from_object
    add esp, 8
    test eax, eax
    setne al
    movzx eax, al
    jmp __dbase_cls_tobject_inheritsfrom_source_end
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
    mov eax, dword ptr [ebp+12]
    pop edx
    pop ecx
    push eax
    push edx
    push ecx
    call __dbase_cls_concat3
    add esp, 12
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
    jmp __dbase_cls_exception___ini___source_end
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
global __dbase_cls_tobject_create
__dbase_cls_tobject_create:
    push __dbase_vmt_tobject
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    ret
global __dbase_cls_tobject_vmt
__dbase_cls_tobject_vmt:
    mov eax, __dbase_vmt_tobject
    ret
global __dbase_cls_exception_vmt
__dbase_cls_exception_vmt:
    mov eax, __dbase_vmt_exception
    ret

section .data

; Stage 600: JitVmt headers: parent, name, instance_size, init, finalize, destroy
__dbase_cls_exception___ini___string_0:
    db 58, 32, 0
__dbase_cls_exception_default_message:
    db 69, 120, 99, 101, 112, 116, 105, 111, 110, 0
__dbase_cls_empty:
    db 0
global __dbase_vmt_tobject
__dbase_vmt_tobject:
    dd 0
    dd __dbase_vmt_tobject_name
    dd 4
    dd __dbase_cls_tobject___ini__
    dd 0
    dd __dbase_cls_tobject___del__
    dd __dbase_cls_tobject_free
    dd __dbase_cls_tobject_freeinstance
    dd __dbase_cls_tobject_classtype
    dd __dbase_cls_tobject_classparent
    dd __dbase_cls_tobject_classnameaddress
    dd __dbase_cls_tobject_classname
    dd __dbase_cls_tobject_instancesize
    dd __dbase_cls_tobject_inheritsfrom
__dbase_vmt_tobject_name:
    db 84, 79, 98, 106, 101, 99, 116, 0
global __dbase_vmt_exception
__dbase_vmt_exception:
    dd __dbase_vmt_tobject
    dd __dbase_vmt_exception_name
    dd 12
    dd __dbase_cls_exception_fields_init
    dd __dbase_cls_exception_fields_done
    dd __dbase_cls_tobject___del__
    dd __dbase_cls_tobject_free
    dd __dbase_cls_tobject_freeinstance
    dd __dbase_cls_tobject_classtype
    dd __dbase_cls_tobject_classparent
    dd __dbase_cls_tobject_classnameaddress
    dd __dbase_cls_tobject_classname
    dd __dbase_cls_tobject_instancesize
    dd __dbase_cls_tobject_inheritsfrom
__dbase_vmt_exception_name:
    db 69, 120, 99, 101, 112, 116, 105, 111, 110, 0

section .bss
