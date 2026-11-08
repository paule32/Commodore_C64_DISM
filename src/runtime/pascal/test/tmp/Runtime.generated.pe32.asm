; Von Pascal erzeugter IA-32-Assembler
; Ziel: Windows PE32 DLL / integrierter COFF32-Linker
; Library: Runtime
bits 32
dllname "Runtime.dll"
global __d64_dll_entry
entry __d64_dll_entry
%include "Runtime.generated.pe32.asm.imports.inc"
%line 56
__d64_dll_entry:
    push ebp
    mov ebp, esp
    cmp dword ptr [ebp+12], 1
    jne __pas_dll_attach_done_1
__pas_dll_attach_done_1:
    mov eax, 1
    mov esp, ebp
    pop ebp
    ret 12

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

; function GlobalWindowProc
__pas_global_globalwindowproc:
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
    sub esp, 16
    xor eax, eax
    push eax
    lea ecx, [ebp-20]
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    lea ecx, [ebp-24]
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    lea ecx, [ebp-28]
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    lea ecx, [ebp-32]
    pop eax
    mov dword ptr [ecx], eax
    lea ecx, [ebp+12]
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 129
    mov edx, 129
    pop eax
    cmp eax, edx
    jne __pas_if_else_2
    lea ecx, [ebp+20]
    mov eax, dword ptr [ecx]
    push eax
    lea ecx, [ebp-24]
    pop eax
    mov dword ptr [ecx], eax
    lea ecx, [ebp-24]
    mov ecx, dword ptr [ecx]
    mov eax, dword ptr [ecx]
    push eax
    lea ecx, [ebp-20]
    pop eax
    mov dword ptr [ecx], eax
    lea ecx, [ebp-20]
    mov eax, dword ptr [ecx]
    test eax, eax
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_if_else_4
    lea ecx, [ebp+8]
    mov eax, dword ptr [ecx]
    push eax
    lea ecx, [ebp-20]
    mov ecx, dword ptr [ecx]
    add ecx, 12
    pop eax
    mov dword ptr [ecx], eax
    lea ecx, [ebp-20]
    mov eax, dword ptr [ecx]
    push eax
    mov eax, -21
    push eax
    lea ecx, [ebp+8]
    mov eax, dword ptr [ecx]
    push eax
    call _SetWindowLongA@12
    jmp __pas_if_end_3
__pas_if_else_4:
__pas_if_end_5:
    jmp __pas_if_end_3
__pas_if_else_2:
    mov eax, -21
    push eax
    lea ecx, [ebp+8]
    mov eax, dword ptr [ecx]
    push eax
    call _GetWindowLongA@8
    push eax
    lea ecx, [ebp-20]
    pop eax
    mov dword ptr [ecx], eax
__pas_if_end_3:
    lea ecx, [ebp-20]
    mov eax, dword ptr [ecx]
    test eax, eax
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_if_else_6
    lea ecx, [ebp+8]
    mov eax, dword ptr [ecx]
    mov ecx, __pas_param_twindow_dispatchmessage_winhwnd_24
    mov dword ptr [ecx], eax
    lea ecx, [ebp+12]
    mov eax, dword ptr [ecx]
    mov ecx, __pas_param_twindow_dispatchmessage_msg_25
    mov dword ptr [ecx], eax
    lea ecx, [ebp+16]
    mov eax, dword ptr [ecx]
    mov ecx, __pas_param_twindow_dispatchmessage_wparam_26
    mov dword ptr [ecx], eax
    lea ecx, [ebp+20]
    mov eax, dword ptr [ecx]
    mov ecx, __pas_param_twindow_dispatchmessage_lparam_27
    mov dword ptr [ecx], eax
    lea ecx, [ebp-20]
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_twindow_dispatchmessage
    push eax
    lea ecx, [ebp-32]
    pop eax
    mov dword ptr [ecx], eax
    lea ecx, [ebp+12]
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 130
    mov edx, 130
    pop eax
    cmp eax, edx
    jne __pas_if_else_8
    mov eax, 0
    push eax
    mov eax, -21
    push eax
    lea ecx, [ebp+8]
    mov eax, dword ptr [ecx]
    push eax
    call _SetWindowLongA@12
    mov eax, 0
    push eax
    lea ecx, [ebp-20]
    mov ecx, dword ptr [ecx]
    add ecx, 12
    pop eax
    mov dword ptr [ecx], eax
    lea ecx, [ebp-20]
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_tobject_free
    lea ecx, [ebp-32]
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
    ret 16
__pas_if_else_8:
__pas_if_end_9:
    lea ecx, [ebp+12]
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 2
    mov edx, 2
    pop eax
    cmp eax, edx
    jne __pas_if_else_10
    mov eax, 0
    push eax
    call _PostQuitMessage@4
    mov eax, 0
    push eax
    lea ecx, [ebp-32]
    pop eax
    mov dword ptr [ecx], eax
    lea ecx, [ebp-32]
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
    ret 16
__pas_if_else_10:
__pas_if_end_11:
    lea ecx, [ebp-32]
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
    ret 16
__pas_if_else_6:
__pas_if_end_7:
    lea ecx, [ebp+12]
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 2
    mov edx, 2
    pop eax
    cmp eax, edx
    jne __pas_if_else_12
    mov eax, 0
    push eax
    call _PostQuitMessage@4
    mov eax, 0
    push eax
    lea ecx, [ebp-32]
    pop eax
    mov dword ptr [ecx], eax
    lea ecx, [ebp-32]
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
    ret 16
__pas_if_else_12:
__pas_if_end_13:
    lea ecx, [ebp+20]
    mov eax, dword ptr [ecx]
    push eax
    lea ecx, [ebp+16]
    mov eax, dword ptr [ecx]
    push eax
    lea ecx, [ebp+12]
    mov eax, dword ptr [ecx]
    push eax
    lea ecx, [ebp+8]
    mov eax, dword ptr [ecx]
    push eax
    call _DefWindowProcA@16
    push eax
    lea ecx, [ebp-32]
    pop eax
    mov dword ptr [ecx], eax
    lea ecx, [ebp-32]
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
    ret 16

; procedure RunMessageLoop
__pas_global_runmessageloop:
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
    sub esp, 32
    lea ecx, [ebp-44]
    mov dword ptr [ecx], 0
    mov dword ptr [ecx+4], 0
    mov dword ptr [ecx+8], 0
    mov dword ptr [ecx+12], 0
    mov dword ptr [ecx+16], 0
    mov dword ptr [ecx+20], 0
    mov dword ptr [ecx+24], 0
    xor eax, eax
    push eax
    lea ecx, [ebp-48]
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 0
    push eax
    mov eax, 0
    push eax
    mov eax, 0
    push eax
    lea ecx, [ebp-44]
    push ecx
    call _GetMessageA@16
    push eax
    lea ecx, [ebp-48]
    pop eax
    mov dword ptr [ecx], eax
__pas_while_condition_14:
    lea ecx, [ebp-48]
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    mov edx, 0
    pop eax
    cmp eax, edx
    jle __pas_while_end_15
    lea ecx, [ebp-44]
    push ecx
    call _TranslateMessage@4
    lea ecx, [ebp-44]
    push ecx
    call _DispatchMessageA@4
    mov eax, 0
    push eax
    mov eax, 0
    push eax
    mov eax, 0
    push eax
    lea ecx, [ebp-44]
    push ecx
    call _GetMessageA@16
    push eax
    lea ecx, [ebp-48]
    pop eax
    mov dword ptr [ecx], eax
    jmp __pas_while_condition_14
__pas_while_end_15:
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

; constructor TObject.Create
__pas_method_tobject_create:
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

; destructor TObject.Destroy
__pas_method_tobject_destroy:
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

; procedure TObject.Free
__pas_method_tobject_free:
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
    mov eax, esi
    push eax
    xor eax, eax
    mov edx, eax
    pop eax
    cmp eax, edx
    je __pas_if_else_16
    mov eax, esi
    push eax
    call _jit_object_free
    add esp, 4
    jmp __pas_if_end_17
__pas_if_else_16:
__pas_if_end_17:
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

; procedure TObject.FreeInstance
__pas_method_tobject_freeinstance:
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
    mov eax, esi
    push eax
    xor eax, eax
    mov edx, eax
    pop eax
    cmp eax, edx
    je __pas_if_else_18
    mov eax, esi
    push eax
    call _jit_object_instance_free
    add esp, 4
    jmp __pas_if_end_19
__pas_if_else_18:
__pas_if_end_19:
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

; function TObject.ClassType
__pas_method_tobject_classtype:
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
    mov eax, esi
    push eax
    call _jit_object_class_type
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

; function TObject.ClassParent
__pas_method_tobject_classparent:
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
    mov eax, esi
    push eax
    call _jit_object_class_type
    add esp, 4
    push eax
    call _jit_class_parent
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

; function TObject.ClassNameAddress
__pas_method_tobject_classnameaddress:
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
    mov eax, esi
    push eax
    call _jit_object_class_type
    add esp, 4
    push eax
    call _jit_class_name
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

; function TObject.ClassName
__pas_method_tobject_classname:
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
    push esi
    call __pas_method_tobject_classnameaddress
    pop esi
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

; function TObject.InstanceSize
__pas_method_tobject_instancesize:
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
    mov eax, esi
    push eax
    call _jit_object_class_type
    add esp, 4
    push eax
    call _jit_class_instance_size
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

; function TObject.InheritsFrom
__pas_method_tobject_inheritsfrom:
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
    mov byte ptr [ecx], al
    mov ecx, __pas_param_tobject_inheritsfrom_aclass_19
    mov eax, dword ptr [ecx]
    push eax
    mov eax, esi
    push eax
    call _jit_inherits_from_object
    add esp, 8
    push eax
    mov eax, 0
    mov edx, 0
    pop eax
    cmp eax, edx
    setne al
    movzx eax, al
    push eax
    lea ecx, [ebp-20]
    pop eax
    mov byte ptr [ecx], al
    lea ecx, [ebp-20]
    movzx eax, byte ptr [ecx]
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

; constructor Exception.Create
__pas_method_exception_create:
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
    call __pas_method_tobject_create
    pop esi
    mov ecx, __pas_param_exception_create_amessage_21
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 4
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

; constructor TWindow.Create
__pas_method_twindow_create:
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
    sub esp, 44
    xor eax, eax
    push eax
    lea ecx, [ebp-20]
    pop eax
    mov dword ptr [ecx], eax
    lea ecx, [ebp-60]
    mov dword ptr [ecx], 0
    mov dword ptr [ecx+4], 0
    mov dword ptr [ecx+8], 0
    mov dword ptr [ecx+12], 0
    mov dword ptr [ecx+16], 0
    mov dword ptr [ecx+20], 0
    mov dword ptr [ecx+24], 0
    mov dword ptr [ecx+28], 0
    mov dword ptr [ecx+32], 0
    mov dword ptr [ecx+36], 0
    push esi
    call __pas_method_tobject_create
    pop esi
    mov eax, __pas_string_0
    call __pas_print_string
    call __pas_print_newline
    mov eax, __pas_string_1
    push eax
    mov ecx, esi
    add ecx, 4
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    call _GetModuleHandleA@4
    push eax
    mov ecx, esi
    add ecx, 8
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 3
    push eax
    lea ecx, [ebp-60]
    pop eax
    mov dword ptr [ecx], eax
    mov eax, __pas_global_globalwindowproc
    push eax
    lea ecx, [ebp-60]
    add ecx, 4
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 0
    push eax
    lea ecx, [ebp-60]
    add ecx, 8
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 0
    push eax
    lea ecx, [ebp-60]
    add ecx, 12
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, esi
    add ecx, 8
    mov eax, dword ptr [ecx]
    push eax
    lea ecx, [ebp-60]
    add ecx, 16
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 32512
    push eax
    mov eax, 0
    push eax
    call _LoadIconA@8
    push eax
    lea ecx, [ebp-60]
    add ecx, 20
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 32512
    push eax
    mov eax, 0
    push eax
    call _LoadCursorA@8
    push eax
    lea ecx, [ebp-60]
    add ecx, 24
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 5
    push eax
    mov eax, 1
    mov edx, 1
    pop eax
    add eax, edx
    push eax
    lea ecx, [ebp-60]
    add ecx, 28
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    lea ecx, [ebp-60]
    add ecx, 32
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, esi
    add ecx, 4
    mov eax, dword ptr [ecx]
    push eax
    lea ecx, [ebp-60]
    add ecx, 36
    pop eax
    mov dword ptr [ecx], eax
    lea ecx, [ebp-60]
    push ecx
    call _RegisterClassA@4
    push eax
    lea ecx, [ebp-20]
    pop eax
    mov dword ptr [ecx], eax
    lea ecx, [ebp-20]
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    mov edx, 0
    pop eax
    cmp eax, edx
    jne __pas_if_else_20
    mov eax, 0
    push eax
    mov eax, 16
    mov edx, 16
    pop eax
    add eax, edx
    push eax
    mov eax, __pas_string_2
    push eax
    mov eax, __pas_string_3
    push eax
    mov eax, 0
    push eax
    call _MessageBoxA@16
    mov eax, 3
    push eax
    call _ExitProcess@4
    jmp __pas_if_end_21
__pas_if_else_20:
__pas_if_end_21:
    mov eax, __pas_string_4
    call __pas_print_string
    call __pas_print_newline
    mov eax, esi
    push eax
    mov ecx, esi
    add ecx, 8
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    push eax
    mov eax, 0
    push eax
    mov eax, 480
    push eax
    mov eax, 640
    push eax
    mov eax, 0
    push eax
    mov eax, 0
    push eax
    mov eax, 13565952
    push eax
    mov ecx, esi
    add ecx, 16
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 4
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    push eax
    call _CreateWindowExA@48
    push eax
    mov ecx, esi
    add ecx, 12
    pop eax
    mov dword ptr [ecx], eax
    mov eax, __pas_string_5
    call __pas_print_string
    call __pas_print_newline
    mov ecx, esi
    add ecx, 12
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    mov edx, 0
    pop eax
    cmp eax, edx
    jne __pas_if_else_22
    mov eax, __pas_string_6
    call __pas_print_string
    call __pas_print_newline
    mov eax, 0
    push eax
    mov eax, 16
    mov edx, 16
    pop eax
    add eax, edx
    push eax
    mov eax, __pas_string_2
    push eax
    mov eax, __pas_string_7
    push eax
    mov eax, 0
    push eax
    call _MessageBoxA@16
    mov eax, 2
    push eax
    call _ExitProcess@4
    jmp __pas_if_end_23
__pas_if_else_22:
__pas_if_end_23:
    mov eax, __pas_string_8
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

; destructor TWindow.Destroy
__pas_method_twindow_destroy:
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
    call __pas_method_tobject_destroy
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

; function TWindow.GetHandle
__pas_method_twindow_gethandle:
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
    mov ecx, esi
    add ecx, 12
    mov eax, dword ptr [ecx]
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

; function TWindow.DispatchMessage
__pas_method_twindow_dispatchmessage:
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
    mov ecx, __pas_param_twindow_dispatchmessage_lparam_27
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_twindow_dispatchmessage_wparam_26
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_twindow_dispatchmessage_msg_25
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_twindow_dispatchmessage_winhwnd_24
    mov eax, dword ptr [ecx]
    push eax
    call _DefWindowProcA@16
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

; constructor TForm.Create
__pas_method_tform_create:
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
    call __pas_method_twindow_create
    pop esi
    mov eax, __pas_string_9
    call __pas_print_string
    call __pas_print_newline
    mov eax, __pas_string_10
    push eax
    mov ecx, esi
    add ecx, 36
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

; destructor TForm.Destroy
__pas_method_tform_destroy:
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
    call __pas_method_twindow_destroy
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

; constructor TApplication.Create
__pas_method_tapplication_create:
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
    call __pas_method_tobject_create
    pop esi
    mov eax, __pas_string_11
    call __pas_print_string
    mov eax, __pas_string_12
    call __pas_print_string
    call __pas_print_newline
    push __pas_vmt_tform
    call _jit_object_instance_new
    add esp, 4
    mov ecx, __pas_ctor_result__ctor_tform_23_30_30
    mov dword ptr [ecx], eax
    push esi
    mov ecx, __pas_ctor_result__ctor_tform_23_30_30
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_tform_create
    pop esi
    mov ecx, __pas_ctor_result__ctor_tform_23_30_30
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 4
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 10
    push eax
    mov ecx, esi
    add ecx, 4
    mov ecx, dword ptr [ecx]
    add ecx, 12
    mov eax, dword ptr [ecx]
    push eax
    call _ShowWindow@8
    mov ecx, esi
    add ecx, 4
    mov ecx, dword ptr [ecx]
    add ecx, 12
    mov eax, dword ptr [ecx]
    push eax
    call _UpdateWindow@4
    call __pas_global_runmessageloop
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

; destructor TApplication.Destroy
__pas_method_tapplication_destroy:
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
    mov ecx, esi
    add ecx, 4
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_tobject_free
    pop esi
    push esi
    call __pas_method_tobject_destroy
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

global __d64_cls_tobject_new_create
__d64_cls_tobject_new_create:
    push ebp
    mov ebp, esp
    push esi
    push __pas_vmt_tobject
    call _jit_object_instance_new
    add esp, 4
    mov esi, eax
    test esi, esi
    jz __d64_cls_tobject_new_create_end
    call __pas_method_tobject_create
    mov eax, esi
__d64_cls_tobject_new_create_end:
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_exception_new_create
__d64_cls_exception_new_create:
    push ebp
    mov ebp, esp
    push esi
    push __pas_vmt_exception
    call _jit_object_instance_new
    add esp, 4
    mov esi, eax
    test esi, esi
    jz __d64_cls_exception_new_create_end
    mov eax, dword ptr [ebp+8]
    mov dword ptr [__pas_param_exception_create_amessage_21], eax
    call __pas_method_exception_create
    mov eax, esi
__d64_cls_exception_new_create_end:
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_twindow_new_create
__d64_cls_twindow_new_create:
    push ebp
    mov ebp, esp
    push esi
    push __pas_vmt_twindow
    call _jit_object_instance_new
    add esp, 4
    mov esi, eax
    test esi, esi
    jz __d64_cls_twindow_new_create_end
    call __pas_method_twindow_create
    mov eax, esi
__d64_cls_twindow_new_create_end:
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tform_new_create
__d64_cls_tform_new_create:
    push ebp
    mov ebp, esp
    push esi
    push __pas_vmt_tform
    call _jit_object_instance_new
    add esp, 4
    mov esi, eax
    test esi, esi
    jz __d64_cls_tform_new_create_end
    call __pas_method_tform_create
    mov eax, esi
__d64_cls_tform_new_create_end:
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tapplication_new_create
__d64_cls_tapplication_new_create:
    push ebp
    mov ebp, esp
    push esi
    push __pas_vmt_tapplication
    call _jit_object_instance_new
    add esp, 4
    mov esi, eax
    test esi, esi
    jz __d64_cls_tapplication_new_create_end
    call __pas_method_tapplication_create
    mov eax, esi
__d64_cls_tapplication_new_create_end:
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tobject_method_create
__d64_cls_tobject_method_create:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_tobject_create
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tobject_method_destroy
__d64_cls_tobject_method_destroy:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_tobject_destroy
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tobject_method_free
__d64_cls_tobject_method_free:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_tobject_free
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tobject_method_freeinstance
__d64_cls_tobject_method_freeinstance:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_tobject_freeinstance
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tobject_method_classtype
__d64_cls_tobject_method_classtype:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_tobject_classtype
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tobject_method_classparent
__d64_cls_tobject_method_classparent:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_tobject_classparent
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tobject_method_classnameaddress
__d64_cls_tobject_method_classnameaddress:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_tobject_classnameaddress
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tobject_method_classname
__d64_cls_tobject_method_classname:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_tobject_classname
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tobject_method_instancesize
__d64_cls_tobject_method_instancesize:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_tobject_instancesize
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tobject_method_inheritsfrom
__d64_cls_tobject_method_inheritsfrom:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    mov eax, dword ptr [ebp+12]
    mov dword ptr [__pas_param_tobject_inheritsfrom_aclass_19], eax
    call __pas_method_tobject_inheritsfrom
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_exception_method_create
__d64_cls_exception_method_create:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    mov eax, dword ptr [ebp+12]
    mov dword ptr [__pas_param_exception_create_amessage_21], eax
    call __pas_method_exception_create
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_twindow_method_create
__d64_cls_twindow_method_create:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_twindow_create
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_twindow_method_destroy
__d64_cls_twindow_method_destroy:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_twindow_destroy
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_twindow_method_gethandle
__d64_cls_twindow_method_gethandle:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_twindow_gethandle
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_twindow_method_dispatchmessage
__d64_cls_twindow_method_dispatchmessage:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    mov eax, dword ptr [ebp+12]
    mov dword ptr [__pas_param_twindow_dispatchmessage_winhwnd_24], eax
    mov eax, dword ptr [ebp+16]
    mov dword ptr [__pas_param_twindow_dispatchmessage_msg_25], eax
    mov eax, dword ptr [ebp+20]
    mov dword ptr [__pas_param_twindow_dispatchmessage_wparam_26], eax
    mov eax, dword ptr [ebp+24]
    mov dword ptr [__pas_param_twindow_dispatchmessage_lparam_27], eax
    call __pas_method_twindow_dispatchmessage
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tform_method_create
__d64_cls_tform_method_create:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_tform_create
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tform_method_destroy
__d64_cls_tform_method_destroy:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_tform_destroy
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tapplication_method_create
__d64_cls_tapplication_method_create:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_tapplication_create
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tapplication_method_destroy
__d64_cls_tapplication_method_destroy:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_tapplication_destroy
    pop esi
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_exception_get_fmessage
__d64_cls_exception_get_fmessage:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    mov edx, dword ptr [ebp+12]
    mov cl, byte ptr [eax+4]
    mov byte ptr [edx+0], cl
    mov cl, byte ptr [eax+5]
    mov byte ptr [edx+1], cl
    mov cl, byte ptr [eax+6]
    mov byte ptr [edx+2], cl
    mov cl, byte ptr [eax+7]
    mov byte ptr [edx+3], cl
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_exception_set_fmessage
__d64_cls_exception_set_fmessage:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    mov edx, dword ptr [ebp+12]
    mov cl, byte ptr [edx+0]
    mov byte ptr [eax+4], cl
    mov cl, byte ptr [edx+1]
    mov byte ptr [eax+5], cl
    mov cl, byte ptr [edx+2]
    mov byte ptr [eax+6], cl
    mov cl, byte ptr [edx+3]
    mov byte ptr [eax+7], cl
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tform_get_fwidth
__d64_cls_tform_get_fwidth:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    mov edx, dword ptr [ebp+12]
    mov cl, byte ptr [eax+20]
    mov byte ptr [edx+0], cl
    mov cl, byte ptr [eax+21]
    mov byte ptr [edx+1], cl
    mov cl, byte ptr [eax+22]
    mov byte ptr [edx+2], cl
    mov cl, byte ptr [eax+23]
    mov byte ptr [edx+3], cl
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tform_set_fwidth
__d64_cls_tform_set_fwidth:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    mov edx, dword ptr [ebp+12]
    mov cl, byte ptr [edx+0]
    mov byte ptr [eax+20], cl
    mov cl, byte ptr [edx+1]
    mov byte ptr [eax+21], cl
    mov cl, byte ptr [edx+2]
    mov byte ptr [eax+22], cl
    mov cl, byte ptr [edx+3]
    mov byte ptr [eax+23], cl
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tform_get_fheight
__d64_cls_tform_get_fheight:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    mov edx, dword ptr [ebp+12]
    mov cl, byte ptr [eax+24]
    mov byte ptr [edx+0], cl
    mov cl, byte ptr [eax+25]
    mov byte ptr [edx+1], cl
    mov cl, byte ptr [eax+26]
    mov byte ptr [edx+2], cl
    mov cl, byte ptr [eax+27]
    mov byte ptr [edx+3], cl
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tform_set_fheight
__d64_cls_tform_set_fheight:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    mov edx, dword ptr [ebp+12]
    mov cl, byte ptr [edx+0]
    mov byte ptr [eax+24], cl
    mov cl, byte ptr [edx+1]
    mov byte ptr [eax+25], cl
    mov cl, byte ptr [edx+2]
    mov byte ptr [eax+26], cl
    mov cl, byte ptr [edx+3]
    mov byte ptr [eax+27], cl
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tform_get_fleft
__d64_cls_tform_get_fleft:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    mov edx, dword ptr [ebp+12]
    mov cl, byte ptr [eax+28]
    mov byte ptr [edx+0], cl
    mov cl, byte ptr [eax+29]
    mov byte ptr [edx+1], cl
    mov cl, byte ptr [eax+30]
    mov byte ptr [edx+2], cl
    mov cl, byte ptr [eax+31]
    mov byte ptr [edx+3], cl
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tform_set_fleft
__d64_cls_tform_set_fleft:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    mov edx, dword ptr [ebp+12]
    mov cl, byte ptr [edx+0]
    mov byte ptr [eax+28], cl
    mov cl, byte ptr [edx+1]
    mov byte ptr [eax+29], cl
    mov cl, byte ptr [edx+2]
    mov byte ptr [eax+30], cl
    mov cl, byte ptr [edx+3]
    mov byte ptr [eax+31], cl
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tform_get_ftop
__d64_cls_tform_get_ftop:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    mov edx, dword ptr [ebp+12]
    mov cl, byte ptr [eax+32]
    mov byte ptr [edx+0], cl
    mov cl, byte ptr [eax+33]
    mov byte ptr [edx+1], cl
    mov cl, byte ptr [eax+34]
    mov byte ptr [edx+2], cl
    mov cl, byte ptr [eax+35]
    mov byte ptr [edx+3], cl
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tform_set_ftop
__d64_cls_tform_set_ftop:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    mov edx, dword ptr [ebp+12]
    mov cl, byte ptr [edx+0]
    mov byte ptr [eax+32], cl
    mov cl, byte ptr [edx+1]
    mov byte ptr [eax+33], cl
    mov cl, byte ptr [edx+2]
    mov byte ptr [eax+34], cl
    mov cl, byte ptr [edx+3]
    mov byte ptr [eax+35], cl
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tform_get_fcaption
__d64_cls_tform_get_fcaption:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    mov edx, dword ptr [ebp+12]
    mov cl, byte ptr [eax+36]
    mov byte ptr [edx+0], cl
    mov cl, byte ptr [eax+37]
    mov byte ptr [edx+1], cl
    mov cl, byte ptr [eax+38]
    mov byte ptr [edx+2], cl
    mov cl, byte ptr [eax+39]
    mov byte ptr [edx+3], cl
    mov esp, ebp
    pop ebp
    ret

global __d64_cls_tform_set_fcaption
__d64_cls_tform_set_fcaption:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    mov edx, dword ptr [ebp+12]
    mov cl, byte ptr [edx+0]
    mov byte ptr [eax+36], cl
    mov cl, byte ptr [edx+1]
    mov byte ptr [eax+37], cl
    mov cl, byte ptr [edx+2]
    mov byte ptr [eax+38], cl
    mov cl, byte ptr [edx+3]
    mov byte ptr [eax+39], cl
    mov esp, ebp
    pop ebp
    ret

; Stage 240: cdecl JitDestroyProc -> Exception.Destroy
__pas_vmt_destroy_exception:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    call __pas_method_tobject_destroy
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
    call __pas_method_tapplication_destroy
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
    call __pas_method_tform_destroy
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
    call __pas_method_tobject_destroy
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
    call __pas_method_twindow_destroy
    pop esi
    mov esp, ebp
    pop ebp
    ret
export "Exception_Create", __d64_cls_exception_method_create
export "Exception_get_Message", __d64_cls_exception_get_fmessage
export "Exception_new_Create", __d64_cls_exception_new_create
export "TApplication_Create", __d64_cls_tapplication_method_create
export "TApplication_Destroy", __d64_cls_tapplication_method_destroy
export "TApplication_new_Create", __d64_cls_tapplication_new_create
export "TForm_Create", __d64_cls_tform_method_create
export "TForm_Destroy", __d64_cls_tform_method_destroy
export "TForm_get_Caption", __d64_cls_tform_get_fcaption
export "TForm_get_Height", __d64_cls_tform_get_fheight
export "TForm_get_Left", __d64_cls_tform_get_fleft
export "TForm_get_Top", __d64_cls_tform_get_ftop
export "TForm_get_Width", __d64_cls_tform_get_fwidth
export "TForm_new_Create", __d64_cls_tform_new_create
export "TForm_set_Caption", __d64_cls_tform_set_fcaption
export "TForm_set_Height", __d64_cls_tform_set_fheight
export "TForm_set_Left", __d64_cls_tform_set_fleft
export "TForm_set_Top", __d64_cls_tform_set_ftop
export "TForm_set_Width", __d64_cls_tform_set_fwidth
export "TObject_ClassName", __d64_cls_tobject_method_classname
export "TObject_ClassNameAddress", __d64_cls_tobject_method_classnameaddress
export "TObject_ClassParent", __d64_cls_tobject_method_classparent
export "TObject_ClassType", __d64_cls_tobject_method_classtype
export "TObject_Create", __d64_cls_tobject_method_create
export "TObject_Destroy", __d64_cls_tobject_method_destroy
export "TObject_Free", __d64_cls_tobject_method_free
export "TObject_FreeInstance", __d64_cls_tobject_method_freeinstance
export "TObject_InheritsFrom", __d64_cls_tobject_method_inheritsfrom
export "TObject_InstanceSize", __d64_cls_tobject_method_instancesize
export "TObject_new_Create", __d64_cls_tobject_new_create
export "TWindow_Create", __d64_cls_twindow_method_create
export "TWindow_Destroy", __d64_cls_twindow_method_destroy
export "TWindow_DispatchMessage", __d64_cls_twindow_method_dispatchmessage
export "TWindow_GetHandle", __d64_cls_twindow_method_gethandle
export "TWindow_new_Create", __d64_cls_twindow_new_create
export "D64_System_Strings_IntToStr", __pas_global_inttostr
export "D64_System_Strings_StrToInt", __pas_global_strtoint

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

; Stage 240: Pascal class runtime metadata / JitVmt (PE32)
__pas_classname_exception: db 69, 120, 99, 101, 112, 116, 105, 111, 110, 0
__pas_classname_tapplication: db 84, 65, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 0
__pas_string_10:
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
__pas_string_0: db 84, 87, 105, 110, 100, 111, 119, 58, 32, 67, 114, 101, 97, 116, 101, 0
__pas_string_1: db 87, 105, 110, 51, 50, 71, 117, 105, 46, 87, 105, 110, 100, 111, 119, 0
__pas_string_2: db 87, 105, 110, 51, 50, 45, 70, 101, 104, 108, 101, 114, 0
__pas_string_3: db 68, 105, 101, 32, 70, 101, 110, 115, 116, 101, 114, 107, 108, 97, 115, 115, 101, 32, 107, 111, 110, 110, 116, 101, 32, 110, 105, 99, 104, 116, 32, 114, 101, 103, 105, 115, 116, 114, 105, 101, 114, 116, 32, 119, 101, 114, 100, 101, 110, 46, 0
__pas_string_4: db 82, 101, 103, 105, 115, 116, 101, 114, 32, 111, 107, 0
__pas_string_5: db 87, 105, 110, 67, 114, 101, 97, 116, 101, 32, 111, 107, 0
__pas_string_6: db 72, 97, 110, 100, 108, 101, 32, 101, 114, 114, 111, 114, 0
__pas_string_7: db 68, 97, 115, 32, 72, 97, 117, 112, 116, 102, 101, 110, 115, 116, 101, 114, 32, 107, 111, 110, 110, 116, 101, 32, 110, 105, 99, 104, 116, 32, 101, 114, 122, 101, 117, 103, 116, 32, 119, 101, 114, 100, 101, 110, 46, 0
__pas_string_8: db 84, 87, 105, 110, 100, 111, 119, 58, 32, 119, 105, 110, 32, 104, 97, 110, 100, 108, 101, 32, 111, 107, 0
__pas_string_9: db 84, 70, 111, 114, 109, 58, 32, 67, 114, 101, 97, 116, 101, 0
__pas_string_11: db 84, 65, 112, 112, 58, 32, 67, 114, 101, 97, 116, 101, 0
__pas_string_12: db 0

section .bss
align 4
; Stage 535: nichtinitialisierte Pascal-Variablen (BSS)
__pas_param_tobject_inheritsfrom_aclass_19: resb 4 ; intern: pointer
__pas_param_exception_create_amessage_21: resb 4 ; intern: string
__pas_param_twindow_dispatchmessage_winhwnd_24: resb 4 ; intern: integer
__pas_param_twindow_dispatchmessage_msg_25: resb 4 ; intern: integer
__pas_param_twindow_dispatchmessage_wparam_26: resb 4 ; intern: integer
__pas_param_twindow_dispatchmessage_lparam_27: resb 4 ; intern: integer
__pas_ctor_result__ctor_tform_23_30_30: resb 4 ; intern: TForm
__pas_cookie_secret: resd 1
__pas_double_scratch: resq 1
__pas_double_int_scratch: resd 1
__pas_double_buffer: resb 64
