; Von Pascal erzeugter IA-32-Assembler
; Ziel: Windows PE32 / integrierter COFF32-Linker
; Grafikbackend: Direct2D
; Programm: test_raise
bits 32
global _start
entry _start
extern ExitProcess
extern AllocConsole
extern GetStdHandle
extern SetConsoleScreenBufferSize
extern SetConsoleWindowInfo
extern GetConsoleScreenBufferInfo
extern SetConsoleCursorPosition
extern GetConsoleMode
extern SetConsoleMode
extern WriteFile
extern lstrlenA
extern wsprintfA
import _calloc, "msvcrt.dll", "calloc"
import _jit_object_instance_new, "libd64_runtime.dll", "jit_object_instance_new"
import _jit_object_instance_free, "libd64_runtime.dll", "jit_object_instance_free"
import _jit_object_free, "libd64_runtime.dll", "jit_object_free"
import _jit_object_class_type, "libd64_runtime.dll", "jit_object_class_type"
import _jit_class_parent, "libd64_runtime.dll", "jit_class_parent"
import _jit_class_name, "libd64_runtime.dll", "jit_class_name"
import _jit_class_instance_size, "libd64_runtime.dll", "jit_class_instance_size"
import _jit_inherits_from_class, "libd64_runtime.dll", "jit_inherits_from_class"
import _jit_inherits_from_object, "libd64_runtime.dll", "jit_inherits_from_object"
import _jit_dynstring_from_cstr, "libd64_runtime.dll", "jit_dynstring_from_cstr"
import _jit_raise, "libd64_runtime.dll", "_jit_raise"
import _jit_exception_push, "libd64_runtime.dll", "_jit_exception_push"
import _jit_exception_pop, "libd64_runtime.dll", "_jit_exception_pop"
import _jit_read_string, "libd64_runtime.dll", "_jit_read_string"
import _jit_read_int, "libd64_runtime.dll", "_jit_read_int"
import _jit_free, "libd64_runtime.dll", "_jit_free"
_start:
    call __pas_console_init
    mov eax, __pas_string_0
    call __pas_print_string
    call __pas_print_newline
    mov dword ptr [__pas_exc_frame_2], __pas_exc_env_1
    push __pas_exc_frame_2
    call _jit_exception_push
    add esp, 4
    mov dword ptr [__pas_exc_env_1+0], ebx
    mov dword ptr [__pas_exc_env_1+4], esi
    mov dword ptr [__pas_exc_env_1+8], edi
    mov dword ptr [__pas_exc_env_1+12], ebp
    mov dword ptr [__pas_exc_env_1+16], esp
    mov dword ptr [__pas_exc_env_1+20], __pas_try_handler_3
    mov eax, __pas_string_1
    call __pas_print_string
    call __pas_print_newline
    mov eax, __pas_string_2
    push eax
    push 7
    call _jit_raise
    add esp, 8
    mov eax, __pas_string_3
    call __pas_print_string
    call __pas_print_newline
    call _jit_exception_pop
    jmp __pas_try_end_4
__pas_try_handler_3:
    call _jit_exception_pop
    mov eax, __pas_string_4
    call __pas_print_string
    call __pas_print_newline
__pas_try_end_4:
    mov eax, __pas_string_5
    call __pas_print_string
    call __pas_print_newline
    call _jit_read_string
    push eax
    call _jit_free
    add esp, 4
    call __pas_console_restore
    push 0
    call ExitProcess

; constructor TObject.Create
__pas_method_tobject_create:
    push ebp
    mov ebp, esp
    mov esp, ebp
    pop ebp
    ret

; destructor TObject.Destroy
__pas_method_tobject_destroy:
    push ebp
    mov ebp, esp
    mov esp, ebp
    pop ebp
    ret

; procedure TObject.Free
__pas_method_tobject_free:
    push ebp
    mov ebp, esp
    mov eax, esi
    push eax
    xor eax, eax
    mov edx, eax
    pop eax
    cmp eax, edx
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_if_else_5
    mov eax, esi
    push eax
    call _jit_object_free
    add esp, 4
    jmp __pas_if_end_6
__pas_if_else_5:
__pas_if_end_6:
    mov esp, ebp
    pop ebp
    ret

; procedure TObject.FreeInstance
__pas_method_tobject_freeinstance:
    push ebp
    mov ebp, esp
    mov eax, esi
    push eax
    xor eax, eax
    mov edx, eax
    pop eax
    cmp eax, edx
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_if_else_7
    mov eax, esi
    push eax
    call _jit_object_instance_free
    add esp, 4
    jmp __pas_if_end_8
__pas_if_else_7:
__pas_if_end_8:
    mov esp, ebp
    pop ebp
    ret

; function TObject.ClassType
__pas_method_tobject_classtype:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tobject_classtype_result_0
    pop eax
    mov dword ptr [ecx], eax
    mov eax, esi
    push eax
    call _jit_object_class_type
    add esp, 4
    push eax
    mov ecx, __pas_result_tobject_classtype_result_0
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tobject_classtype_result_0
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function TObject.ClassParent
__pas_method_tobject_classparent:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tobject_classparent_result_1
    pop eax
    mov dword ptr [ecx], eax
    mov eax, esi
    push eax
    call _jit_object_class_type
    add esp, 4
    push eax
    call _jit_class_parent
    add esp, 4
    push eax
    mov ecx, __pas_result_tobject_classparent_result_1
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tobject_classparent_result_1
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function TObject.ClassNameAddress
__pas_method_tobject_classnameaddress:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tobject_classnameaddress_result_2
    pop eax
    mov dword ptr [ecx], eax
    mov eax, esi
    push eax
    call _jit_object_class_type
    add esp, 4
    push eax
    call _jit_class_name
    add esp, 4
    push eax
    mov ecx, __pas_result_tobject_classnameaddress_result_2
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tobject_classnameaddress_result_2
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function TObject.ClassName
__pas_method_tobject_classname:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tobject_classname_result_3
    pop eax
    mov dword ptr [ecx], eax
    push esi
    call __pas_method_tobject_classnameaddress
    pop esi
    push eax
    call _jit_dynstring_from_cstr
    add esp, 4
    push eax
    mov ecx, __pas_result_tobject_classname_result_3
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tobject_classname_result_3
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function TObject.InstanceSize
__pas_method_tobject_instancesize:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tobject_instancesize_result_4
    pop eax
    mov dword ptr [ecx], eax
    mov eax, esi
    push eax
    call _jit_object_class_type
    add esp, 4
    push eax
    call _jit_class_instance_size
    add esp, 4
    push eax
    mov ecx, __pas_result_tobject_instancesize_result_4
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tobject_instancesize_result_4
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function TObject.InheritsFrom
__pas_method_tobject_inheritsfrom:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tobject_inheritsfrom_result_6
    pop eax
    mov byte ptr [ecx], al
    mov ecx, __pas_param_tobject_inheritsfrom_aclass_5
    mov eax, dword ptr [ecx]
    push eax
    mov eax, esi
    push eax
    call _jit_inherits_from_object
    add esp, 8
    push eax
    mov eax, 0
    mov edx, eax
    pop eax
    cmp eax, edx
    setne al
    movzx eax, al
    push eax
    mov ecx, __pas_result_tobject_inheritsfrom_result_6
    pop eax
    mov byte ptr [ecx], al
    mov ecx, __pas_result_tobject_inheritsfrom_result_6
    movzx eax, byte ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; constructor Exception.Create
__pas_method_exception_create:
    push ebp
    mov ebp, esp
    push esi
    call __pas_method_tobject_create
    pop esi
    mov ecx, __pas_param_exception_create_amessage_7
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 1
    pop eax
    mov dword ptr [ecx], eax
    mov esp, ebp
    pop ebp
    ret

__pas_console_init:
    call AllocConsole
    push -11
    call GetStdHandle
    mov dword ptr [__pas_stdout_handle], eax
    push __pas_console_info
    push eax
    call GetConsoleScreenBufferInfo
    mov dword ptr [__pas_console_state_valid], eax
    push __pas_console_rect
    push 1
    push eax
    call SetConsoleWindowInfo
    push 1638480
    push dword ptr [__pas_stdout_handle]
    call SetConsoleScreenBufferSize
    push __pas_console_mode
    push dword ptr [__pas_stdout_handle]
    call GetConsoleMode
    mov eax, dword ptr [__pas_console_mode]
    or eax, 4
    push eax
    push dword ptr [__pas_stdout_handle]
    call SetConsoleMode
    ret

__pas_console_restore:
    cmp dword ptr [__pas_console_state_valid], 0
    je __pas_console_restore_done
    push dword ptr [__pas_console_mode]
    push dword ptr [__pas_stdout_handle]
    call SetConsoleMode
    push __pas_console_restore_rect
    push 1
    push dword ptr [__pas_stdout_handle]
    call SetConsoleWindowInfo
    push dword ptr [__pas_console_info]
    push dword ptr [__pas_stdout_handle]
    call SetConsoleScreenBufferSize
    mov eax, __pas_console_info
    add eax, 10
    push eax
    push 1
    push dword ptr [__pas_stdout_handle]
    call SetConsoleWindowInfo
    push dword ptr [__pas_console_info+4]
    push dword ptr [__pas_stdout_handle]
    call SetConsoleCursorPosition
__pas_console_restore_done:
    ret

__pas_write_cstring:
    push eax
    push eax
    call lstrlenA
    mov edx, eax
    pop eax
    push 0
    push __pas_written
    push edx
    push eax
    push dword ptr [__pas_stdout_handle]
    call WriteFile
    ret

__pas_print_string:
    call __pas_write_cstring
    ret

__pas_print_newline:
    mov eax, __pas_newline
    call __pas_write_cstring
    ret

align 4
__pas_console_rect: dw 0, 0, 79, 24
__pas_fmt_s: db 37, 115, 0
__pas_fmt_d: db 37, 100, 0
__pas_fmt_c: db 37, 99, 0
__pas_newline: db 13, 10, 0
__pas_clear_sequence: db 27, 91, 50, 74, 27, 91, 72, 0
__pas_range_message: db 82, 97, 110, 103, 101, 32, 101, 114, 114, 111, 114, 13, 10, 0

; Pascal-Variablen
__pas_result_tobject_classtype_result_0: dd 0 ; intern: pointer
__pas_result_tobject_classparent_result_1: dd 0 ; intern: pointer
__pas_result_tobject_classnameaddress_result_2: dd 0 ; intern: pointer
__pas_result_tobject_classname_result_3: dd 0 ; intern: string
__pas_result_tobject_instancesize_result_4: dd 0 ; intern: integer
__pas_param_tobject_inheritsfrom_aclass_5: dd 0 ; intern: pointer
__pas_result_tobject_inheritsfrom_result_6: db 0 ; intern: boolean
__pas_param_exception_create_amessage_7: dd 0 ; intern: string

; Nullterminierte Windows-Latin-1-Zeichenketten
__pas_string_0: db 115, 116, 97, 114, 116, 0
__pas_string_1: db 98, 101, 102, 111, 114, 101, 32, 114, 97, 105, 115, 101, 0
__pas_string_2: db 102, 117, 122, 122, 0
__pas_string_3: db 117, 110, 114, 101, 97, 99, 104, 97, 98, 108, 101, 0
__pas_string_4: db 101, 120, 99, 101, 112, 116, 105, 111, 110, 32, 99, 97, 117, 103, 104, 116, 0
__pas_string_5: db 97, 102, 116, 101, 114, 32, 101, 120, 99, 101, 112, 116, 0

section .bss
align 4
__pas_stdout_handle: resd 1
__pas_console_restore_rect: resw 4
__pas_console_info: resb 22
__pas_console_state_valid: resd 1
__pas_console_mode: resd 1
__pas_written: resd 1
__pas_format_buffer: resb 32
__pas_char_buffer: resb 2

; Pascal TRY/EXCEPT exception frames (PE32, BSS)
__pas_exc_env_1: resb 24
__pas_exc_frame_2: resb 268
