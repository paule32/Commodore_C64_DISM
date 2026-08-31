; Von Pascal erzeugtes Windows-PE32+-AMD64-Unit-Modul
; Unit: System.SysUtils
; Architektur: AMD64 / x86-64 / COFF64
bits 64
global __unit_System_SysUtils
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
__unit_System_SysUtils:
    ret

; constructor Exception.Create
global __pas_method_exception_create
__pas_method_exception_create:
    push rbp
    mov rbp, rsp
    push rsi
    sub rsp, 8
    mov rsi, rcx
    mov rax, rdx
    push rax
    mov r11, __pas_param_exception_create_amessage_0
    pop rax
    mov qword ptr [r11], rax
    mov r11, rsi
    mov rax, r11
    mov qword ptr [__pas_calltmp_0], rax
    sub rsp, 32
    mov rcx, qword ptr [__pas_calltmp_0]
    call __pas_method_tobject_create
    add rsp, 32
    mov r11, __pas_param_exception_create_amessage_0
    mov rax, qword ptr [r11]
    push rax
    mov r11, rsi
    add r11, 1
    pop rax
    mov qword ptr [r11], rax
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

; Pascal-Variablen
__pas_param_exception_create_amessage_0: dq 0 ; intern: string
