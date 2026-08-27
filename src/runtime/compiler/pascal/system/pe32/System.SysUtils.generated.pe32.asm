; Von Pascal erzeugtes Windows-PE32-Unit-Modul
; Unit: System.SysUtils
bits 32
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
    push ebp
    mov ebp, esp
    push esi
    call __pas_method_tobject_create
    pop esi
    mov ecx, __pas_param_exception_create_amessage_0
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 1
    pop eax
    mov dword ptr [ecx], eax
    mov esp, ebp
    pop ebp
    ret

align 4
__pas_unit_System_SysUtils_fmt_s: db 37, 115, 0
__pas_unit_System_SysUtils_fmt_d: db 37, 100, 0
__pas_unit_System_SysUtils_fmt_c: db 37, 99, 0
__pas_unit_System_SysUtils_newline: db 13, 10, 0
__pas_unit_System_SysUtils_clear_sequence: db 27, 91, 50, 74, 27, 91, 72, 0
__pas_unit_System_SysUtils_range_message: db 82, 97, 110, 103, 101, 32, 101, 114, 114, 111, 114, 13, 10, 0

; Pascal-Variablen
__pas_param_exception_create_amessage_0: dd 0 ; intern: string
