%include "System.Controls.generated.pe32.extern.inc"
bits 32


section .text


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
global __dbase_cls_tobject_create
__dbase_cls_tobject_create:
    push __dbase_vmt_tobject
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    ret
global __dbase_cls_tpersistent_create
__dbase_cls_tpersistent_create:
    push __dbase_vmt_tpersistent
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    ret
global __dbase_cls_tcomponent_create
__dbase_cls_tcomponent_create:
    push __dbase_vmt_tcomponent
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    ret
global __dbase_cls_tcontrol_create
__dbase_cls_tcontrol_create:
    push __dbase_vmt_tcontrol
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    ret
global __dbase_cls_twincontrol_create
__dbase_cls_twincontrol_create:
    push __dbase_vmt_twincontrol
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    ret


; Stage 679: O3 runtime ABI import guard
__dbase_o3_abi_guard:
    call __dbase_o3_default_vmt_abi
    ret

section .data
; Stage 600: JitVmt headers: parent, name, instance_size, init, finalize, destroy
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
global __dbase_vmt_tpersistent
__dbase_vmt_tpersistent:
    dd __dbase_vmt_tobject
    dd __dbase_vmt_tpersistent_name
    dd 0x80000004
    dd __dbase_cls_tobject___ini__
    dd 0
    dd 0
__dbase_vmt_tpersistent_name:
    db 84, 80, 101, 114, 115, 105, 115, 116, 101, 110, 116, 0
global __dbase_vmt_tcomponent
__dbase_vmt_tcomponent:
    dd __dbase_vmt_tpersistent
    dd __dbase_vmt_tcomponent_name
    dd 0x80000004
    dd __dbase_cls_tobject___ini__
    dd 0
    dd 0
__dbase_vmt_tcomponent_name:
    db 84, 67, 111, 109, 112, 111, 110, 101, 110, 116, 0
global __dbase_vmt_tcontrol
__dbase_vmt_tcontrol:
    dd __dbase_vmt_tcomponent
    dd __dbase_vmt_tcontrol_name
    dd 0x80000004
    dd __dbase_cls_tobject___ini__
    dd 0
    dd 0
__dbase_vmt_tcontrol_name:
    db 84, 67, 111, 110, 116, 114, 111, 108, 0
global __dbase_vmt_twincontrol
__dbase_vmt_twincontrol:
    dd __dbase_vmt_tcontrol
    dd __dbase_vmt_twincontrol_name
    dd 0x80000004
    dd __dbase_cls_tobject___ini__
    dd 0
    dd 0
__dbase_vmt_twincontrol_name:
    db 84, 87, 105, 110, 67, 111, 110, 116, 114, 111, 108, 0

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
