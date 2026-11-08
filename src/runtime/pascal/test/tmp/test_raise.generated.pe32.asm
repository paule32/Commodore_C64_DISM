; Von Pascal erzeugter IA-32-Assembler
; Ziel: Windows PE32 / integrierter COFF32-Linker
; Grafikbackend: Direct2D
; Programm: test_raise
bits 32
global _start
entry _start
%include "test_raise.generated.pe32.asm.imports.inc"
%line 88
_start:
    call __pas_console_init
    mov eax, __pas_string_0
    call __pas_print_string
    call __pas_print_newline
    push __pas_vmt_tfoo
    call _jit_object_instance_new
    add esp, 4
    mov ecx, __pas_ctor_result__ctor_tfoo_0_7_7
    mov dword ptr [ecx], eax
    mov eax, 42
    mov ecx, __pas_param_tfoo_create_avalue_6
    mov dword ptr [ecx], eax
    mov ecx, __pas_ctor_result__ctor_tfoo_0_7_7
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_tfoo_create
    mov ecx, __pas_ctor_result__ctor_tfoo_0_7_7
    mov eax, dword ptr [ecx]
    mov ecx, __pas_var_foo_0
    mov dword ptr [ecx], eax
    sub esp, 292
    lea eax, [esp+24]
    lea edx, [esp]
    mov dword ptr [eax], edx
    push eax
    call _jit_exception_push
    add esp, 4
    mov dword ptr [esp+0], ebx
    mov dword ptr [esp+4], esi
    mov dword ptr [esp+8], edi
    mov dword ptr [esp+12], ebp
    mov dword ptr [esp+16], esp
    mov dword ptr [esp+20], __pas_try_handler_1
    mov ecx, __pas_var_foo_0
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_tfoo_show
    call _jit_exception_pop
    add esp, 292
    mov ecx, __pas_var_foo_0
    mov eax, dword ptr [ecx]
    mov esi, eax
    push esi
    call __pas_method_tobject_free
    add esp, 4
    jmp __pas_try_end_2
__pas_try_handler_1:
    call _jit_exception_pop
    mov ecx, __pas_var_foo_0
    mov eax, dword ptr [ecx]
    mov esi, eax
    push esi
    call __pas_method_tobject_free
    add esp, 4
    mov eax, dword ptr [esp+28]
    lea edx, [esp+32]
    push edx
    push eax
    call _jit_raise
    add esp, 8
__pas_try_end_2:
    call __d64_cls_tapplication_new_create
    mov ecx, __pas_var_application_1
    mov dword ptr [ecx], eax
    mov ecx, __pas_var_application_1
    mov eax, dword ptr [ecx]
    mov esi, eax
    push esi
    call __pas_method_tobject_free
    add esp, 4
    call _d64_console_read_string
    push eax
    call _jit_free
    add esp, 4
    mov eax, 0
    push eax
    call __pas_console_restore
    call _ExitProcess@4
    call __pas_console_restore
    push 0
    call ExitProcess

; function IntToStr
__pas_global_inttostr:
    push ebp
    mov ebp, esp
    sub esp, 4
    call __pas_cookie_initialize
    mov edx, dword ptr [__pas_cookie_secret]
    xor edx, ebp
    mov dword ptr [ebp-4], edx
    push ebx
    push esi
    push edi
    sub esp, 4
    xor eax, eax
    push eax
    lea ecx, [ebp-20]
    pop eax
    mov dword ptr [ecx], eax
    lea ecx, [ebp+8]
    mov eax, dword ptr [ecx]
    push eax
    call __IntToStr
    add esp, 4
    push eax
    call _jit_dynstring_from_cstr
    add esp, 4
    push eax
    lea ecx, [ebp-20]
    pop eax
    mov dword ptr [ecx], eax
    lea ecx, [ebp-20]
    mov eax, dword ptr [ecx]
    mov edx, dword ptr [ebp-4]
    xor edx, ebp
    cmp edx, dword ptr [__pas_cookie_secret]
    jne __pas_cookie_failure
    mov ebx, dword ptr [ebp-8]
    mov esi, dword ptr [ebp-12]
    mov edi, dword ptr [ebp-16]
    mov esp, ebp
    pop ebp
    ret

; function StrToInt
__pas_global_strtoint:
    push ebp
    mov ebp, esp
    sub esp, 4
    call __pas_cookie_initialize
    mov edx, dword ptr [__pas_cookie_secret]
    xor edx, ebp
    mov dword ptr [ebp-4], edx
    push ebx
    push esi
    push edi
    sub esp, 4
    xor eax, eax
    push eax
    lea ecx, [ebp-20]
    pop eax
    mov dword ptr [ecx], eax
    lea ecx, [ebp+8]
    mov eax, dword ptr [ecx]
    push eax
    call __StrToInt
    add esp, 4
    push eax
    lea ecx, [ebp-20]
    pop eax
    mov dword ptr [ecx], eax
    lea ecx, [ebp-20]
    mov eax, dword ptr [ecx]
    mov edx, dword ptr [ebp-4]
    xor edx, ebp
    cmp edx, dword ptr [__pas_cookie_secret]
    jne __pas_cookie_failure
    mov ebx, dword ptr [ebp-8]
    mov esi, dword ptr [ebp-12]
    mov edi, dword ptr [ebp-16]
    mov esp, ebp
    pop ebp
    ret

; constructor TFaz.Create
__pas_method_tfaz_create:
    push ebp
    mov ebp, esp
    sub esp, 4
    call __pas_cookie_initialize
    mov edx, dword ptr [__pas_cookie_secret]
    xor edx, ebp
    mov dword ptr [ebp-4], edx
    push ebx
    push esi
    push edi
    push esi
    push esi
    call __pas_method_tobject_create
    add esp, 4
    pop esi
    mov edx, dword ptr [ebp-4]
    xor edx, ebp
    cmp edx, dword ptr [__pas_cookie_secret]
    jne __pas_cookie_failure
    mov ebx, dword ptr [ebp-8]
    mov esi, dword ptr [ebp-12]
    mov edi, dword ptr [ebp-16]
    mov esp, ebp
    pop ebp
    ret

; destructor TFaz.Destroy
__pas_method_tfaz_destroy:
    push ebp
    mov ebp, esp
    sub esp, 4
    call __pas_cookie_initialize
    mov edx, dword ptr [__pas_cookie_secret]
    xor edx, ebp
    mov dword ptr [ebp-4], edx
    push ebx
    push esi
    push edi
    push esi
    push esi
    call __pas_method_tobject_destroy
    add esp, 4
    pop esi
    mov edx, dword ptr [ebp-4]
    xor edx, ebp
    cmp edx, dword ptr [__pas_cookie_secret]
    jne __pas_cookie_failure
    mov ebx, dword ptr [ebp-8]
    mov esi, dword ptr [ebp-12]
    mov edi, dword ptr [ebp-16]
    mov esp, ebp
    pop ebp
    ret

; procedure TFaz.Show
__pas_method_tfaz_show:
    push ebp
    mov ebp, esp
    sub esp, 4
    call __pas_cookie_initialize
    mov edx, dword ptr [__pas_cookie_secret]
    xor edx, ebp
    mov dword ptr [ebp-4], edx
    push ebx
    push esi
    push edi
    mov eax, __pas_string_1
    call __pas_print_string
    push esi
    push esi
    call __pas_method_tobject_classname
    add esp, 4
    pop esi
    call __pas_print_string
    call __pas_print_newline
    mov eax, __pas_string_2
    call __pas_print_string
    mov eax, __pas_string_3
    call __pas_print_string
    call __pas_print_newline
    mov eax, __pas_string_4
    call __pas_print_string
    push esi
    push esi
    call __pas_method_tobject_instancesize
    add esp, 4
    pop esi
    push eax
    call __pas_global_inttostr
    add esp, 4
    call __pas_print_string
    call __pas_print_newline
    mov edx, dword ptr [ebp-4]
    xor edx, ebp
    cmp edx, dword ptr [__pas_cookie_secret]
    jne __pas_cookie_failure
    mov ebx, dword ptr [ebp-8]
    mov esi, dword ptr [ebp-12]
    mov edi, dword ptr [ebp-16]
    mov esp, ebp
    pop ebp
    ret

; constructor TFoo.Create
__pas_method_tfoo_create:
    push ebp
    mov ebp, esp
    sub esp, 4
    call __pas_cookie_initialize
    mov edx, dword ptr [__pas_cookie_secret]
    xor edx, ebp
    mov dword ptr [ebp-4], edx
    push ebx
    push esi
    push edi
    push esi
    call __pas_method_tfaz_create
    pop esi
    mov ecx, __pas_param_tfoo_create_avalue_6
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 4
    pop eax
    mov dword ptr [ecx], eax
    mov eax, __pas_string_5
    push eax
    mov ecx, esi
    add ecx, 8
    pop eax
    mov dword ptr [ecx], eax
    fld qword ptr [__pas_double_0]
    mov ecx, esi
    add ecx, 12
    fstp qword ptr [ecx]
    mov eax, __pas_string_6
    push eax
    mov ecx, esi
    add ecx, 20
    pop eax
    mov dword ptr [ecx], eax
    mov edx, dword ptr [ebp-4]
    xor edx, ebp
    cmp edx, dword ptr [__pas_cookie_secret]
    jne __pas_cookie_failure
    mov ebx, dword ptr [ebp-8]
    mov esi, dword ptr [ebp-12]
    mov edi, dword ptr [ebp-16]
    mov esp, ebp
    pop ebp
    ret

; destructor TFoo.Destroy
__pas_method_tfoo_destroy:
    push ebp
    mov ebp, esp
    sub esp, 4
    call __pas_cookie_initialize
    mov edx, dword ptr [__pas_cookie_secret]
    xor edx, ebp
    mov dword ptr [ebp-4], edx
    push ebx
    push esi
    push edi
    push esi
    call __pas_method_tfaz_destroy
    pop esi
    mov edx, dword ptr [ebp-4]
    xor edx, ebp
    cmp edx, dword ptr [__pas_cookie_secret]
    jne __pas_cookie_failure
    mov ebx, dword ptr [ebp-8]
    mov esi, dword ptr [ebp-12]
    mov edi, dword ptr [ebp-16]
    mov esp, ebp
    pop ebp
    ret

; procedure TFoo.Show
__pas_method_tfoo_show:
    push ebp
    mov ebp, esp
    sub esp, 4
    call __pas_cookie_initialize
    mov edx, dword ptr [__pas_cookie_secret]
    xor edx, ebp
    mov dword ptr [ebp-4], edx
    push ebx
    push esi
    push edi
    mov eax, __pas_string_1
    call __pas_print_string
    push esi
    push esi
    call __pas_method_tobject_classname
    add esp, 4
    pop esi
    call __pas_print_string
    call __pas_print_newline
    mov eax, __pas_string_2
    call __pas_print_string
    mov eax, __pas_string_7
    call __pas_print_string
    call __pas_print_newline
    mov eax, __pas_string_4
    call __pas_print_string
    push esi
    push esi
    call __pas_method_tobject_instancesize
    add esp, 4
    pop esi
    push eax
    call __pas_global_inttostr
    add esp, 4
    call __pas_print_string
    call __pas_print_newline
    push esi
    call __pas_method_tfaz_show
    pop esi
    mov edx, dword ptr [ebp-4]
    xor edx, ebp
    cmp edx, dword ptr [__pas_cookie_secret]
    jne __pas_cookie_failure
    mov ebx, dword ptr [ebp-8]
    mov esi, dword ptr [ebp-12]
    mov edi, dword ptr [ebp-16]
    mov esp, ebp
    pop ebp
    ret

; Stage 240: cdecl JitDestroyProc -> Exception.Destroy
__pas_vmt_destroy_exception:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    push esi
    call __pas_method_tobject_destroy
    add esp, 4
    pop esi
    mov esp, ebp
    pop ebp
    ret

; Stage 240: cdecl JitDestroyProc -> TApplication.Destroy
__pas_vmt_destroy_tapplication:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    push esi
    call __pas_method_tapplication_destroy
    add esp, 4
    pop esi
    mov esp, ebp
    pop ebp
    ret

; Stage 240: cdecl JitDestroyProc -> TFaz.Destroy
__pas_vmt_destroy_tfaz:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_tfaz_destroy
    pop esi
    mov esp, ebp
    pop ebp
    ret

; Stage 240: cdecl JitDestroyProc -> TFoo.Destroy
__pas_vmt_destroy_tfoo:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_tfoo_destroy
    pop esi
    mov esp, ebp
    pop ebp
    ret

; Stage 240: cdecl JitDestroyProc -> TForm.Destroy
__pas_vmt_destroy_tform:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    push esi
    call __pas_method_tform_destroy
    add esp, 4
    pop esi
    mov esp, ebp
    pop ebp
    ret

; Stage 240: cdecl JitDestroyProc -> TObject.Destroy
__pas_vmt_destroy_tobject:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    push esi
    call __pas_method_tobject_destroy
    add esp, 4
    pop esi
    mov esp, ebp
    pop ebp
    ret

; Stage 240: cdecl JitDestroyProc -> TWindow.Destroy
__pas_vmt_destroy_twindow:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    push esi
    call __pas_method_twindow_destroy
    add esp, 4
    pop esi
    mov esp, ebp
    pop ebp
    ret

; Stage 532: PE32 stack cookie (CSPRNG + atomic first writer)
__pas_cookie_initialize:
    push ebp
    mov ebp, esp
    sub esp, 4
    mov eax, dword ptr [__pas_cookie_secret]
    test eax, eax
    jne __pas_cookie_initialized
    lea eax, [ebp-4]
    push 2
    push 4
    push eax
    push 0
    call __d64_cookie_BCryptGenRandom
    test eax, eax
    js __pas_cookie_failure
    mov edx, dword ptr [ebp-4]
    or edx, 1
    push 0
    push edx
    push __pas_cookie_secret
    call __d64_cookie_InterlockedCompareExchange
__pas_cookie_initialized:
    mov esp, ebp
    pop ebp
    ret
__pas_cookie_failure:
    push 0
    push 0
    push 0
    call __d64_cookie_RaiseFailFastException
    push 3221226505
    call __d64_cookie_ExitProcess

__pas_console_init:
    call _d64_console_init
    ret

__pas_console_restore:
    call _d64_console_restore
    ret

__pas_print_string:
    push eax
    call _d64_console_write_text
    add esp, 4
    ret

__pas_print_newline:
    call _d64_console_newline
    ret

section .data
align 4
__pas_range_message: db 82, 97, 110, 103, 101, 32, 101, 114, 114, 111, 114, 13, 10, 0

; IEEE-754 Double-Literale
__pas_double_0: dd 2061584302, 1074376212

; Stage 240: Pascal class runtime metadata / JitVmt (PE32)
__pas_classname_exception: db 69, 120, 99, 101, 112, 116, 105, 111, 110, 0
__pas_classname_tapplication: db 84, 65, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 0
__pas_string_3:
__pas_classname_tfaz: db 84, 70, 97, 122, 0
__pas_string_7:
__pas_classname_tfoo: db 84, 70, 111, 111, 0
__pas_classname_tform: db 84, 70, 111, 114, 109, 0
__pas_classname_tobject: db 84, 79, 98, 106, 101, 99, 116, 0
__pas_classname_twindow: db 84, 87, 105, 110, 100, 111, 119, 0
align 4
__pas_vmt_exception:
    dd __pas_vmt_tobject
    dd __pas_classname_exception
    dd 8
    dd 0
    dd 0
    dd __pas_vmt_destroy_exception
__pas_vmt_tapplication:
    dd __pas_vmt_tobject
    dd __pas_classname_tapplication
    dd 8
    dd 0
    dd 0
    dd __pas_vmt_destroy_tapplication
__pas_vmt_tfaz:
    dd __pas_vmt_tobject
    dd __pas_classname_tfaz
    dd 4
    dd 0
    dd 0
    dd __pas_vmt_destroy_tfaz
__pas_vmt_tfoo:
    dd __pas_vmt_tfaz
    dd __pas_classname_tfoo
    dd 24
    dd 0
    dd 0
    dd __pas_vmt_destroy_tfoo
__pas_vmt_tform:
    dd __pas_vmt_twindow
    dd __pas_classname_tform
    dd 40
    dd 0
    dd 0
    dd __pas_vmt_destroy_tform
__pas_vmt_tobject:
    dd 0
    dd __pas_classname_tobject
    dd 4
    dd 0
    dd 0
    dd __pas_vmt_destroy_tobject
__pas_vmt_twindow:
    dd __pas_vmt_tobject
    dd __pas_classname_twindow
    dd 20
    dd 0
    dd 0
    dd __pas_vmt_destroy_twindow

; Nullterminierte Windows-Latin-1-Zeichenketten
__pas_string_0: db 120, 120, 120, 120, 120, 0
__pas_string_1: db 32, 32, 82, 117, 110, 116, 105, 109, 101, 32, 99, 108, 97, 115, 115, 58, 32, 0
__pas_string_2: db 32, 32, 77, 101, 116, 104, 111, 100, 32, 32, 111, 119, 110, 101, 114, 58, 32, 0
__pas_string_4: db 32, 32, 83, 105, 122, 101, 32, 32, 32, 32, 32, 32, 32, 32, 32, 58, 32, 0
__pas_string_5: db 72, 101, 108, 108, 111, 0
__pas_string_6: db 87, 111, 114, 108, 100, 32, 33, 0

section .bss
align 4
; Stage 535: nichtinitialisierte Pascal-Variablen (BSS)
__pas_var_foo_0: resb 4 ; Foo: TFoo
__pas_var_application_1: resb 4 ; Application: TApplication
__pas_param_tfoo_create_avalue_6: resb 4 ; intern: integer
__pas_ctor_result__ctor_tfoo_0_7_7: resb 4 ; intern: TFoo
__pas_cookie_secret: resd 1
__pas_double_scratch: resq 1
__pas_double_int_scratch: resd 1
__pas_double_buffer: resb 64
