; Von Pascal erzeugtes Windows-PE32+-AMD64-Unit-Modul
; Unit: System.Strings
; Architektur: AMD64 / x86-64 / COFF64
bits 64
global __unit_System_Strings
import jit_dynstring_from_cstr, "libruntime_mini.dll", "jit_dynstring_from_cstr"
extern _IntToStr
extern _StrToInt
extern __pas_method_tobject_classname
extern __pas_method_tobject_classnameaddress
extern __pas_method_tobject_classparent
extern __pas_method_tobject_classtype
extern __pas_method_tobject_create
extern __pas_method_tobject_destroy
extern __pas_method_tobject_free
extern __pas_method_tobject_freeinstance
extern __pas_method_tobject_inheritsfrom
extern __pas_method_tobject_instancesize
__unit_System_Strings:
    ret

; function IntToStr
global __pas_System_Strings_IntToStr
__pas_System_Strings_IntToStr:
    push rbp
    mov rbp, rsp
    mov rax, rcx
    push rax
    mov r11, __pas_param_global_inttostr_avalue_0
    pop rax
    mov dword ptr [r11], eax
    xor rax, rax
    push rax
    mov r11, __pas_result_global_inttostr_result_1
    pop rax
    mov qword ptr [r11], rax
    mov r11, __pas_param_global_inttostr_avalue_0
    mov eax, dword ptr [r11]
    mov qword ptr [__pas_calltmp_0], rax
    sub rsp, 32
    mov rcx, qword ptr [__pas_calltmp_0]
    call _IntToStr
    add rsp, 32
    mov qword ptr [__pas_calltmp_1], rax
    sub rsp, 32
    mov rcx, qword ptr [__pas_calltmp_1]
    call jit_dynstring_from_cstr
    add rsp, 32
    push rax
    mov r11, __pas_result_global_inttostr_result_1
    pop rax
    mov qword ptr [r11], rax
    mov r11, __pas_result_global_inttostr_result_1
    mov rax, qword ptr [r11]
    mov rsp, rbp
    pop rbp
    ret

; function StrToInt
global __pas_System_Strings_StrToInt
__pas_System_Strings_StrToInt:
    push rbp
    mov rbp, rsp
    mov rax, rcx
    push rax
    mov r11, __pas_param_global_strtoint_s_2
    pop rax
    mov qword ptr [r11], rax
    xor rax, rax
    push rax
    mov r11, __pas_result_global_strtoint_result_3
    pop rax
    mov dword ptr [r11], eax
    mov r11, __pas_param_global_strtoint_s_2
    mov rax, qword ptr [r11]
    mov qword ptr [__pas_calltmp_2], rax
    sub rsp, 32
    mov rcx, qword ptr [__pas_calltmp_2]
    call _StrToInt
    add rsp, 32
    push rax
    mov r11, __pas_result_global_strtoint_result_3
    pop rax
    mov dword ptr [r11], eax
    mov r11, __pas_result_global_strtoint_result_3
    mov eax, dword ptr [r11]
    mov rsp, rbp
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

; Pascal-Variablen
__pas_param_global_inttostr_avalue_0: dd 0 ; intern: integer
__pas_result_global_inttostr_result_1: dq 0 ; intern: string
__pas_param_global_strtoint_s_2: dq 0 ; intern: string
__pas_result_global_strtoint_result_3: dd 0 ; intern: integer
