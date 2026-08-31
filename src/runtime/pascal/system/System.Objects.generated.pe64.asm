; Von Pascal erzeugtes Windows-PE32+-AMD64-Unit-Modul
; Unit: System.Objects
; Architektur: AMD64 / x86-64 / COFF64
bits 64
global __unit_System_Objects
import jit_object_instance_new, "libruntime_mini.dll", "jit_object_instance_new"
import jit_object_instance_free, "libruntime_mini.dll", "jit_object_instance_free"
import jit_object_free, "libruntime_mini.dll", "jit_object_free"
import jit_object_class_type, "libruntime_mini.dll", "jit_object_class_type"
import jit_class_parent, "libruntime_mini.dll", "jit_class_parent"
import jit_class_name, "libruntime_mini.dll", "jit_class_name"
import jit_class_instance_size, "libruntime_mini.dll", "jit_class_instance_size"
import jit_inherits_from_class, "libruntime_mini.dll", "jit_inherits_from_class"
import jit_inherits_from_object, "libruntime_mini.dll", "jit_inherits_from_object"
import jit_dynstring_from_cstr, "libruntime_mini.dll", "jit_dynstring_from_cstr"
__unit_System_Objects:
    ret

; constructor TObject.Create
global __pas_method_tobject_create
__pas_method_tobject_create:
    push rbp
    mov rbp, rsp
    push rsi
    sub rsp, 8
    mov rsi, rcx
    add rsp, 8
    pop rsi
    pop rbp
    ret

; destructor TObject.Destroy
global __pas_method_tobject_destroy
__pas_method_tobject_destroy:
    push rbp
    mov rbp, rsp
    push rsi
    sub rsp, 8
    mov rsi, rcx
    add rsp, 8
    pop rsi
    pop rbp
    ret

; procedure TObject.Free
global __pas_method_tobject_free
__pas_method_tobject_free:
    push rbp
    mov rbp, rsp
    push rsi
    sub rsp, 8
    mov rsi, rcx
    mov r11, rsi
    mov rax, r11
    push rax
    xor rax, rax
    mov rdx, rax
    pop rax
    cmp rax, rdx
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_if_else_1
    mov r11, rsi
    mov rax, r11
    mov qword ptr [__pas_calltmp_0], rax
    sub rsp, 32
    mov rcx, qword ptr [__pas_calltmp_0]
    call jit_object_free
    add rsp, 32
    jmp __pas_if_end_2
__pas_if_else_1:
__pas_if_end_2:
    add rsp, 8
    pop rsi
    pop rbp
    ret

; procedure TObject.FreeInstance
global __pas_method_tobject_freeinstance
__pas_method_tobject_freeinstance:
    push rbp
    mov rbp, rsp
    push rsi
    sub rsp, 8
    mov rsi, rcx
    mov r11, rsi
    mov rax, r11
    push rax
    xor rax, rax
    mov rdx, rax
    pop rax
    cmp rax, rdx
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_if_else_3
    mov r11, rsi
    mov rax, r11
    mov qword ptr [__pas_calltmp_1], rax
    sub rsp, 32
    mov rcx, qword ptr [__pas_calltmp_1]
    call jit_object_instance_free
    add rsp, 32
    jmp __pas_if_end_4
__pas_if_else_3:
__pas_if_end_4:
    add rsp, 8
    pop rsi
    pop rbp
    ret

; function TObject.ClassType
global __pas_method_tobject_classtype
__pas_method_tobject_classtype:
    push rbp
    mov rbp, rsp
    push rsi
    sub rsp, 8
    mov rsi, rcx
    xor rax, rax
    push rax
    mov r11, __pas_result_tobject_classtype_result_0
    pop rax
    mov qword ptr [r11], rax
    mov r11, rsi
    mov rax, r11
    mov qword ptr [__pas_calltmp_2], rax
    sub rsp, 32
    mov rcx, qword ptr [__pas_calltmp_2]
    call jit_object_class_type
    add rsp, 32
    push rax
    mov r11, __pas_result_tobject_classtype_result_0
    pop rax
    mov qword ptr [r11], rax
    mov r11, __pas_result_tobject_classtype_result_0
    mov rax, qword ptr [r11]
    add rsp, 8
    pop rsi
    pop rbp
    ret

; function TObject.ClassParent
global __pas_method_tobject_classparent
__pas_method_tobject_classparent:
    push rbp
    mov rbp, rsp
    push rsi
    sub rsp, 8
    mov rsi, rcx
    xor rax, rax
    push rax
    mov r11, __pas_result_tobject_classparent_result_1
    pop rax
    mov qword ptr [r11], rax
    mov r11, rsi
    mov rax, r11
    mov qword ptr [__pas_calltmp_3], rax
    sub rsp, 32
    mov rcx, qword ptr [__pas_calltmp_3]
    call jit_object_class_type
    add rsp, 32
    mov qword ptr [__pas_calltmp_4], rax
    sub rsp, 32
    mov rcx, qword ptr [__pas_calltmp_4]
    call jit_class_parent
    add rsp, 32
    push rax
    mov r11, __pas_result_tobject_classparent_result_1
    pop rax
    mov qword ptr [r11], rax
    mov r11, __pas_result_tobject_classparent_result_1
    mov rax, qword ptr [r11]
    add rsp, 8
    pop rsi
    pop rbp
    ret

; function TObject.ClassNameAddress
global __pas_method_tobject_classnameaddress
__pas_method_tobject_classnameaddress:
    push rbp
    mov rbp, rsp
    push rsi
    sub rsp, 8
    mov rsi, rcx
    xor rax, rax
    push rax
    mov r11, __pas_result_tobject_classnameaddress_result_2
    pop rax
    mov qword ptr [r11], rax
    mov r11, rsi
    mov rax, r11
    mov qword ptr [__pas_calltmp_5], rax
    sub rsp, 32
    mov rcx, qword ptr [__pas_calltmp_5]
    call jit_object_class_type
    add rsp, 32
    mov qword ptr [__pas_calltmp_6], rax
    sub rsp, 32
    mov rcx, qword ptr [__pas_calltmp_6]
    call jit_class_name
    add rsp, 32
    push rax
    mov r11, __pas_result_tobject_classnameaddress_result_2
    pop rax
    mov qword ptr [r11], rax
    mov r11, __pas_result_tobject_classnameaddress_result_2
    mov rax, qword ptr [r11]
    add rsp, 8
    pop rsi
    pop rbp
    ret

; function TObject.ClassName
global __pas_method_tobject_classname
__pas_method_tobject_classname:
    push rbp
    mov rbp, rsp
    push rsi
    sub rsp, 8
    mov rsi, rcx
    xor rax, rax
    push rax
    mov r11, __pas_result_tobject_classname_result_3
    pop rax
    mov qword ptr [r11], rax
    mov r11, rsi
    mov rax, r11
    mov qword ptr [__pas_calltmp_7], rax
    sub rsp, 32
    mov rcx, qword ptr [__pas_calltmp_7]
    call __pas_method_tobject_classnameaddress
    add rsp, 32
    mov qword ptr [__pas_calltmp_8], rax
    sub rsp, 32
    mov rcx, qword ptr [__pas_calltmp_8]
    call jit_dynstring_from_cstr
    add rsp, 32
    push rax
    mov r11, __pas_result_tobject_classname_result_3
    pop rax
    mov qword ptr [r11], rax
    mov r11, __pas_result_tobject_classname_result_3
    mov rax, qword ptr [r11]
    add rsp, 8
    pop rsi
    pop rbp
    ret

; function TObject.InstanceSize
global __pas_method_tobject_instancesize
__pas_method_tobject_instancesize:
    push rbp
    mov rbp, rsp
    push rsi
    sub rsp, 8
    mov rsi, rcx
    xor rax, rax
    push rax
    mov r11, __pas_result_tobject_instancesize_result_4
    pop rax
    mov dword ptr [r11], eax
    mov r11, rsi
    mov rax, r11
    mov qword ptr [__pas_calltmp_9], rax
    sub rsp, 32
    mov rcx, qword ptr [__pas_calltmp_9]
    call jit_object_class_type
    add rsp, 32
    mov qword ptr [__pas_calltmp_10], rax
    sub rsp, 32
    mov rcx, qword ptr [__pas_calltmp_10]
    call jit_class_instance_size
    add rsp, 32
    push rax
    mov r11, __pas_result_tobject_instancesize_result_4
    pop rax
    mov dword ptr [r11], eax
    mov r11, __pas_result_tobject_instancesize_result_4
    mov eax, dword ptr [r11]
    add rsp, 8
    pop rsi
    pop rbp
    ret

; function TObject.InheritsFrom
global __pas_method_tobject_inheritsfrom
__pas_method_tobject_inheritsfrom:
    push rbp
    mov rbp, rsp
    push rsi
    sub rsp, 8
    mov rsi, rcx
    mov rax, rdx
    push rax
    mov r11, __pas_param_tobject_inheritsfrom_aclass_5
    pop rax
    mov qword ptr [r11], rax
    xor rax, rax
    push rax
    mov r11, __pas_result_tobject_inheritsfrom_result_6
    pop rax
    mov byte ptr [r11], al
    mov r11, rsi
    mov rax, r11
    mov qword ptr [__pas_calltmp_11], rax
    mov r11, __pas_param_tobject_inheritsfrom_aclass_5
    mov rax, qword ptr [r11]
    mov qword ptr [__pas_calltmp_12], rax
    sub rsp, 32
    mov rcx, qword ptr [__pas_calltmp_11]
    mov rdx, qword ptr [__pas_calltmp_12]
    call jit_inherits_from_object
    add rsp, 32
    push rax
    mov eax, 0
    mov rdx, rax
    pop rax
    cmp eax, edx
    setne al
    movzx eax, al
    push rax
    mov r11, __pas_result_tobject_inheritsfrom_result_6
    pop rax
    mov byte ptr [r11], al
    mov r11, __pas_result_tobject_inheritsfrom_result_6
    movzx eax, byte ptr [r11]
    add rsp, 8
    pop rsi
    pop rbp
    ret

align 8
__pas_fmt_s: db 37, 115, 0
__pas_fmt_d: db 37, 100, 0
__pas_fmt_c: db 37, 99, 0
__pas_newline: db 13, 10, 0
__pas_clear_sequence: db 27, 91, 50, 74, 27, 91, 72, 0
__pas_range_message: db 82, 97, 110, 103, 101, 32, 101, 114, 114, 111, 114, 13, 10, 0

; PE64 Win64-call temporaries
__pas_calltmp_0: dq 0
__pas_calltmp_1: dq 0
__pas_calltmp_2: dq 0
__pas_calltmp_3: dq 0
__pas_calltmp_4: dq 0
__pas_calltmp_5: dq 0
__pas_calltmp_6: dq 0
__pas_calltmp_7: dq 0
__pas_calltmp_8: dq 0
__pas_calltmp_9: dq 0
__pas_calltmp_10: dq 0
__pas_calltmp_11: dq 0
__pas_calltmp_12: dq 0

; Pascal-Variablen
__pas_result_tobject_classtype_result_0: dq 0 ; intern: pointer
__pas_result_tobject_classparent_result_1: dq 0 ; intern: pointer
__pas_result_tobject_classnameaddress_result_2: dq 0 ; intern: pointer
__pas_result_tobject_classname_result_3: dq 0 ; intern: string
__pas_result_tobject_instancesize_result_4: dd 0 ; intern: integer
__pas_param_tobject_inheritsfrom_aclass_5: dq 0 ; intern: pointer
__pas_result_tobject_inheritsfrom_result_6: db 0 ; intern: boolean
