%include "System.Objects.generated.pe32.extern.inc"
bits 32
; dBASE Runtime CLASS DLL – no Qt GUI / no EXE startup
global __d64_dll_entry
entry __d64_dll_entry
export "__dbase_cls_tobject_vmt", __dbase_cls_tobject_vmt
export "__dbase_cls_tobject_create", __dbase_cls_tobject_create
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
    jmp __dbase_cls_tobject_free_source_end
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
    jmp __dbase_cls_tobject_inheritsfrom_source_end
__dbase_cls_tobject_inheritsfrom_source_end:
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

section .data

; Stage 600: JitVmt headers: parent, name, instance_size, init, finalize, destroy
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

section .bss
