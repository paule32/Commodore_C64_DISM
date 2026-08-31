; Von Pascal erzeugtes Windows-PE32-Unit-Modul
; Unit: System.Strings
bits 32
global __unit_System_Strings
import _jit_dynstring_from_cstr, "libd64_qt5.dll", "jit_dynstring_from_cstr"
extern __IntToStr
extern __StrToInt
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
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    push eax
    mov ecx, __pas_param_global_inttostr_avalue_0
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    mov ecx, __pas_result_global_inttostr_result_1
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_global_inttostr_avalue_0
    mov eax, dword ptr [ecx]
    push eax
    call __IntToStr
    add esp, 4
    push eax
    call _jit_dynstring_from_cstr
    add esp, 4
    push eax
    mov ecx, __pas_result_global_inttostr_result_1
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_global_inttostr_result_1
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function StrToInt
global __pas_System_Strings_StrToInt
__pas_System_Strings_StrToInt:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    push eax
    mov ecx, __pas_param_global_strtoint_s_2
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    mov ecx, __pas_result_global_strtoint_result_3
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_global_strtoint_s_2
    mov eax, dword ptr [ecx]
    push eax
    call __StrToInt
    add esp, 4
    push eax
    mov ecx, __pas_result_global_strtoint_result_3
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_global_strtoint_result_3
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

align 4
__pas_unit_System_Strings_fmt_s: db 37, 115, 0
__pas_unit_System_Strings_fmt_d: db 37, 100, 0
__pas_unit_System_Strings_fmt_c: db 37, 99, 0
__pas_unit_System_Strings_newline: db 13, 10, 0
__pas_unit_System_Strings_clear_sequence: db 27, 91, 50, 74, 27, 91, 72, 0
__pas_unit_System_Strings_range_message: db 82, 97, 110, 103, 101, 32, 101, 114, 114, 111, 114, 13, 10, 0

; Pascal-Variablen
__pas_param_global_inttostr_avalue_0: dd 0 ; intern: integer
__pas_result_global_inttostr_result_1: dd 0 ; intern: string
__pas_param_global_strtoint_s_2: dd 0 ; intern: string
__pas_result_global_strtoint_result_3: dd 0 ; intern: integer
