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
import _GetModuleHandleA@4, "kernel32.dll", "GetModuleHandleA"
import _ExitProcess@4, "kernel32.dll", "ExitProcess"
import _GetWindowLongA@8, "user32.dll", "GetWindowLongA"
import _SetWindowLongA@12, "user32.dll", "SetWindowLongA"
import _LoadIconA@8, "user32.dll", "LoadIconA"
import _LoadCursorA@8, "user32.dll", "LoadCursorA"
import _RegisterClassA@4, "user32.dll", "RegisterClassA"
import _CreateWindowExA@48, "user32.dll", "CreateWindowExA"
import _ShowWindow@8, "user32.dll", "ShowWindow"
import _UpdateWindow@4, "user32.dll", "UpdateWindow"
import _IsWindow@4, "user32.dll", "IsWindow"
import _EnableWindow@8, "user32.dll", "EnableWindow"
import _MoveWindow@24, "user32.dll", "MoveWindow"
import _SetWindowTextA@8, "user32.dll", "SetWindowTextA"
import _DestroyWindow@4, "user32.dll", "DestroyWindow"
import _GetMessageA@16, "user32.dll", "GetMessageA"
import _TranslateMessage@4, "user32.dll", "TranslateMessage"
import _DispatchMessageA@4, "user32.dll", "DispatchMessageA"
import _DefWindowProcA@16, "user32.dll", "DefWindowProcA"
import _MessageBoxA@16, "user32.dll", "MessageBoxA"
import _PostQuitMessage@4, "user32.dll", "PostQuitMessage"
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
extern __IntToStr
extern __StrToInt
import _gcvt, "msvcrt.dll", "_gcvt"
import _jit_raise, "libd64_runtime.dll", "_jit_raise"
import _jit_exception_push, "libd64_runtime.dll", "_jit_exception_push"
import _jit_exception_pop, "libd64_runtime.dll", "_jit_exception_pop"
_start:
    call __pas_console_init
    push 21
    push 1
    call _calloc
    add esp, 8
    push eax
    mov ecx, __pas_ctor_result__ctor_tfoo_0_33_33
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 42
    push eax
    mov ecx, __pas_param_tfoo_create_avalue_32
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_ctor_result__ctor_tfoo_0_33_33
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_tfoo_create
    mov ecx, __pas_ctor_result__ctor_tfoo_0_33_33
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_var_foo_0
    pop eax
    mov dword ptr [ecx], eax
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
    mov ecx, __pas_var_foo_0
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_tfoo_show
    call _jit_exception_pop
    mov ecx, __pas_var_foo_0
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_tobject_free
    jmp __pas_try_end_4
__pas_try_handler_3:
    call _jit_exception_pop
    mov ecx, __pas_var_foo_0
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_tobject_free
    mov eax, dword ptr [__pas_exc_frame_2+4]
    push 0
    push eax
    call _jit_raise
    add esp, 8
__pas_try_end_4:
    push 5
    push 1
    call _calloc
    add esp, 8
    push eax
    mov ecx, __pas_ctor_result__ctor_tapplication_4_34_34
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_ctor_result__ctor_tapplication_4_34_34
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_tapplication_create
    mov ecx, __pas_ctor_result__ctor_tapplication_4_34_34
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_var_application_1
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_var_application_1
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_tobject_free
    mov eax, 0
    push eax
    call _ExitProcess@4
    call __pas_console_restore
    push 0
    call ExitProcess

; function IntToStr
__pas_global_inttostr:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    push eax
    mov ecx, __pas_param_global_inttostr_avalue_2
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    mov ecx, __pas_result_global_inttostr_result_3
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_global_inttostr_avalue_2
    mov eax, dword ptr [ecx]
    push eax
    call __IntToStr
    add esp, 4
    push eax
    call _jit_dynstring_from_cstr
    add esp, 4
    push eax
    mov ecx, __pas_result_global_inttostr_result_3
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_global_inttostr_result_3
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function StrToInt
__pas_global_strtoint:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    push eax
    mov ecx, __pas_param_global_strtoint_s_4
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    mov ecx, __pas_result_global_strtoint_result_5
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_global_strtoint_s_4
    mov eax, dword ptr [ecx]
    push eax
    call __StrToInt
    add esp, 4
    push eax
    mov ecx, __pas_result_global_strtoint_result_5
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_global_strtoint_result_5
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function GlobalWindowProc
__pas_global_globalwindowproc:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    push eax
    mov ecx, __pas_param_global_globalwindowproc_winhwnd_6
    pop eax
    mov dword ptr [ecx], eax
    mov eax, dword ptr [ebp+12]
    push eax
    mov ecx, __pas_param_global_globalwindowproc_umsg_7
    pop eax
    mov dword ptr [ecx], eax
    mov eax, dword ptr [ebp+16]
    push eax
    mov ecx, __pas_param_global_globalwindowproc_wparam_8
    pop eax
    mov dword ptr [ecx], eax
    mov eax, dword ptr [ebp+20]
    push eax
    mov ecx, __pas_param_global_globalwindowproc_lparam_9
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    mov ecx, __pas_local_global_globalwindowproc_appform_10
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    mov ecx, __pas_local_global_globalwindowproc_createstruct_11
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    mov ecx, __pas_local_global_globalwindowproc_buttonwindow_12
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    mov ecx, __pas_result_global_globalwindowproc_result_13
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_global_globalwindowproc_umsg_7
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 129
    mov edx, eax
    pop eax
    cmp eax, edx
    sete al
    movzx eax, al
    test eax, eax
    jz __pas_if_else_5
    mov ecx, __pas_param_global_globalwindowproc_lparam_9
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_local_global_globalwindowproc_createstruct_11
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_local_global_globalwindowproc_createstruct_11
    mov ecx, dword ptr [ecx]
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_local_global_globalwindowproc_appform_10
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_local_global_globalwindowproc_appform_10
    mov eax, dword ptr [ecx]
    test eax, eax
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_if_else_7
    mov ecx, __pas_param_global_globalwindowproc_winhwnd_6
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_local_global_globalwindowproc_appform_10
    mov ecx, dword ptr [ecx]
    add ecx, 9
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_local_global_globalwindowproc_appform_10
    mov eax, dword ptr [ecx]
    push eax
    mov eax, -21
    push eax
    mov ecx, __pas_param_global_globalwindowproc_winhwnd_6
    mov eax, dword ptr [ecx]
    push eax
    call _SetWindowLongA@12
    jmp __pas_if_end_8
__pas_if_else_7:
__pas_if_end_8:
    jmp __pas_if_end_6
__pas_if_else_5:
    mov eax, -21
    push eax
    mov ecx, __pas_param_global_globalwindowproc_winhwnd_6
    mov eax, dword ptr [ecx]
    push eax
    call _GetWindowLongA@8
    push eax
    mov ecx, __pas_local_global_globalwindowproc_appform_10
    pop eax
    mov dword ptr [ecx], eax
__pas_if_end_6:
    mov ecx, __pas_local_global_globalwindowproc_appform_10
    mov eax, dword ptr [ecx]
    test eax, eax
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_if_else_9
    mov ecx, __pas_param_global_globalwindowproc_winhwnd_6
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_twindow_dispatchmessage_winhwnd_26
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_global_globalwindowproc_umsg_7
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_twindow_dispatchmessage_msg_27
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_global_globalwindowproc_wparam_8
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_twindow_dispatchmessage_wparam_28
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_global_globalwindowproc_lparam_9
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_twindow_dispatchmessage_lparam_29
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_local_global_globalwindowproc_appform_10
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_twindow_dispatchmessage
    push eax
    mov ecx, __pas_result_global_globalwindowproc_result_13
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_global_globalwindowproc_umsg_7
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 130
    mov edx, eax
    pop eax
    cmp eax, edx
    sete al
    movzx eax, al
    test eax, eax
    jz __pas_if_else_11
    mov eax, 0
    push eax
    mov eax, -21
    push eax
    mov ecx, __pas_param_global_globalwindowproc_winhwnd_6
    mov eax, dword ptr [ecx]
    push eax
    call _SetWindowLongA@12
    mov eax, 0
    push eax
    mov ecx, __pas_local_global_globalwindowproc_appform_10
    mov ecx, dword ptr [ecx]
    add ecx, 9
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_local_global_globalwindowproc_appform_10
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_tobject_free
    mov ecx, __pas_result_global_globalwindowproc_result_13
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret 16
    jmp __pas_if_end_12
__pas_if_else_11:
__pas_if_end_12:
    mov ecx, __pas_param_global_globalwindowproc_umsg_7
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 2
    mov edx, eax
    pop eax
    cmp eax, edx
    sete al
    movzx eax, al
    test eax, eax
    jz __pas_if_else_13
    mov eax, 0
    push eax
    call _PostQuitMessage@4
    mov eax, 0
    push eax
    mov ecx, __pas_result_global_globalwindowproc_result_13
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_global_globalwindowproc_result_13
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret 16
    jmp __pas_if_end_14
__pas_if_else_13:
__pas_if_end_14:
    mov ecx, __pas_result_global_globalwindowproc_result_13
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret 16
    jmp __pas_if_end_10
__pas_if_else_9:
__pas_if_end_10:
    mov ecx, __pas_param_global_globalwindowproc_umsg_7
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 2
    mov edx, eax
    pop eax
    cmp eax, edx
    sete al
    movzx eax, al
    test eax, eax
    jz __pas_if_else_15
    mov eax, 0
    push eax
    call _PostQuitMessage@4
    mov eax, 0
    push eax
    mov ecx, __pas_result_global_globalwindowproc_result_13
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_global_globalwindowproc_result_13
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret 16
    jmp __pas_if_end_16
__pas_if_else_15:
__pas_if_end_16:
    mov ecx, __pas_param_global_globalwindowproc_lparam_9
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_global_globalwindowproc_wparam_8
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_global_globalwindowproc_umsg_7
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_global_globalwindowproc_winhwnd_6
    mov eax, dword ptr [ecx]
    push eax
    call _DefWindowProcA@16
    push eax
    mov ecx, __pas_result_global_globalwindowproc_result_13
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_global_globalwindowproc_result_13
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret 16

; procedure RunMessageLoop
__pas_global_runmessageloop:
    push ebp
    mov ebp, esp
    mov ecx, __pas_local_global_runmessageloop_msg_14
    mov dword ptr [ecx], 0
    mov dword ptr [ecx+4], 0
    mov dword ptr [ecx+8], 0
    mov dword ptr [ecx+12], 0
    mov dword ptr [ecx+16], 0
    mov dword ptr [ecx+20], 0
    mov dword ptr [ecx+24], 0
    xor eax, eax
    push eax
    mov ecx, __pas_local_global_runmessageloop_status_15
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 0
    push eax
    mov eax, 0
    push eax
    mov eax, 0
    push eax
    mov ecx, __pas_local_global_runmessageloop_msg_14
    push ecx
    call _GetMessageA@16
    push eax
    mov ecx, __pas_local_global_runmessageloop_status_15
    pop eax
    mov dword ptr [ecx], eax
__pas_while_condition_17:
    mov ecx, __pas_local_global_runmessageloop_status_15
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    mov edx, eax
    pop eax
    cmp eax, edx
    setg al
    movzx eax, al
    test eax, eax
    jz __pas_while_end_18
    mov ecx, __pas_local_global_runmessageloop_msg_14
    push ecx
    call _TranslateMessage@4
    mov ecx, __pas_local_global_runmessageloop_msg_14
    push ecx
    call _DispatchMessageA@4
    mov eax, 0
    push eax
    mov eax, 0
    push eax
    mov eax, 0
    push eax
    mov ecx, __pas_local_global_runmessageloop_msg_14
    push ecx
    call _GetMessageA@16
    push eax
    mov ecx, __pas_local_global_runmessageloop_status_15
    pop eax
    mov dword ptr [ecx], eax
    jmp __pas_while_condition_17
__pas_while_end_18:
    mov esp, ebp
    pop ebp
    ret

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
    jz __pas_if_else_19
    mov eax, esi
    push eax
    call _jit_object_free
    add esp, 4
    jmp __pas_if_end_20
__pas_if_else_19:
__pas_if_end_20:
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
    jz __pas_if_else_21
    mov eax, esi
    push eax
    call _jit_object_instance_free
    add esp, 4
    jmp __pas_if_end_22
__pas_if_else_21:
__pas_if_end_22:
    mov esp, ebp
    pop ebp
    ret

; function TObject.ClassType
__pas_method_tobject_classtype:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tobject_classtype_result_16
    pop eax
    mov dword ptr [ecx], eax
    mov eax, esi
    push eax
    call _jit_object_class_type
    add esp, 4
    push eax
    mov ecx, __pas_result_tobject_classtype_result_16
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tobject_classtype_result_16
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
    mov ecx, __pas_result_tobject_classparent_result_17
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
    mov ecx, __pas_result_tobject_classparent_result_17
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tobject_classparent_result_17
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
    mov ecx, __pas_result_tobject_classnameaddress_result_18
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
    mov ecx, __pas_result_tobject_classnameaddress_result_18
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tobject_classnameaddress_result_18
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
    mov ecx, __pas_result_tobject_classname_result_19
    pop eax
    mov dword ptr [ecx], eax
    push esi
    call __pas_method_tobject_classnameaddress
    pop esi
    push eax
    call _jit_dynstring_from_cstr
    add esp, 4
    push eax
    mov ecx, __pas_result_tobject_classname_result_19
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tobject_classname_result_19
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
    mov ecx, __pas_result_tobject_instancesize_result_20
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
    mov ecx, __pas_result_tobject_instancesize_result_20
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tobject_instancesize_result_20
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
    mov ecx, __pas_result_tobject_inheritsfrom_result_22
    pop eax
    mov byte ptr [ecx], al
    mov ecx, __pas_param_tobject_inheritsfrom_aclass_21
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
    mov ecx, __pas_result_tobject_inheritsfrom_result_22
    pop eax
    mov byte ptr [ecx], al
    mov ecx, __pas_result_tobject_inheritsfrom_result_22
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
    mov ecx, __pas_param_exception_create_amessage_23
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 1
    pop eax
    mov dword ptr [ecx], eax
    mov esp, ebp
    pop ebp
    ret

; constructor TWindow.Create
__pas_method_twindow_create:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_local_twindow_create_registerresult_24
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_local_twindow_create_winclass_25
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
    add ecx, 1
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    call _GetModuleHandleA@4
    push eax
    mov ecx, esi
    add ecx, 5
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 3
    push eax
    mov ecx, __pas_local_twindow_create_winclass_25
    pop eax
    mov dword ptr [ecx], eax
    mov eax, __pas_global_globalwindowproc
    push eax
    mov ecx, __pas_local_twindow_create_winclass_25
    add ecx, 4
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 0
    push eax
    mov ecx, __pas_local_twindow_create_winclass_25
    add ecx, 8
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 0
    push eax
    mov ecx, __pas_local_twindow_create_winclass_25
    add ecx, 12
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, esi
    add ecx, 5
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_local_twindow_create_winclass_25
    add ecx, 16
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 32512
    push eax
    mov eax, 0
    push eax
    call _LoadIconA@8
    push eax
    mov ecx, __pas_local_twindow_create_winclass_25
    add ecx, 20
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 32512
    push eax
    mov eax, 0
    push eax
    call _LoadCursorA@8
    push eax
    mov ecx, __pas_local_twindow_create_winclass_25
    add ecx, 24
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 5
    push eax
    mov eax, 1
    mov edx, eax
    pop eax
    add eax, edx
    push eax
    mov ecx, __pas_local_twindow_create_winclass_25
    add ecx, 28
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    mov ecx, __pas_local_twindow_create_winclass_25
    add ecx, 32
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_local_twindow_create_winclass_25
    add ecx, 36
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_local_twindow_create_winclass_25
    push ecx
    call _RegisterClassA@4
    push eax
    mov ecx, __pas_local_twindow_create_registerresult_24
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_local_twindow_create_registerresult_24
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    mov edx, eax
    pop eax
    cmp eax, edx
    sete al
    movzx eax, al
    test eax, eax
    jz __pas_if_else_23
    mov eax, 0
    push eax
    mov eax, 16
    mov edx, eax
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
    jmp __pas_if_end_24
__pas_if_else_23:
__pas_if_end_24:
    mov eax, __pas_string_4
    call __pas_print_string
    call __pas_print_newline
    mov eax, esi
    push eax
    mov ecx, esi
    add ecx, 5
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
    add ecx, 13
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    push eax
    call _CreateWindowExA@48
    push eax
    mov ecx, esi
    add ecx, 9
    pop eax
    mov dword ptr [ecx], eax
    mov eax, __pas_string_5
    call __pas_print_string
    call __pas_print_newline
    mov ecx, esi
    add ecx, 9
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    mov edx, eax
    pop eax
    cmp eax, edx
    sete al
    movzx eax, al
    test eax, eax
    jz __pas_if_else_25
    mov eax, __pas_string_6
    call __pas_print_string
    call __pas_print_newline
    mov eax, 0
    push eax
    mov eax, 16
    mov edx, eax
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
    jmp __pas_if_end_26
__pas_if_else_25:
__pas_if_end_26:
    mov eax, __pas_string_8
    call __pas_print_string
    call __pas_print_newline
    mov esp, ebp
    pop ebp
    ret

; destructor TWindow.Destroy
__pas_method_twindow_destroy:
    push ebp
    mov ebp, esp
    push esi
    call __pas_method_tobject_destroy
    pop esi
    mov esp, ebp
    pop ebp
    ret

; function TWindow.GetHandle
__pas_method_twindow_gethandle:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_twindow_gethandle_result_31
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, esi
    add ecx, 9
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_result_twindow_gethandle_result_31
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_twindow_gethandle_result_31
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function TWindow.DispatchMessage
__pas_method_twindow_dispatchmessage:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_twindow_dispatchmessage_result_30
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_twindow_dispatchmessage_lparam_29
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_twindow_dispatchmessage_wparam_28
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_twindow_dispatchmessage_msg_27
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_twindow_dispatchmessage_winhwnd_26
    mov eax, dword ptr [ecx]
    push eax
    call _DefWindowProcA@16
    push eax
    mov ecx, __pas_result_twindow_dispatchmessage_result_30
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_twindow_dispatchmessage_result_30
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; constructor TForm.Create
__pas_method_tform_create:
    push ebp
    mov ebp, esp
    push esi
    call __pas_method_twindow_create
    pop esi
    mov eax, __pas_string_9
    call __pas_print_string
    call __pas_print_newline
    mov eax, __pas_string_10
    push eax
    mov ecx, esi
    add ecx, 33
    pop eax
    mov dword ptr [ecx], eax
    mov esp, ebp
    pop ebp
    ret

; destructor TForm.Destroy
__pas_method_tform_destroy:
    push ebp
    mov ebp, esp
    push esi
    call __pas_method_twindow_destroy
    pop esi
    mov esp, ebp
    pop ebp
    ret

; constructor TApplication.Create
__pas_method_tapplication_create:
    push ebp
    mov ebp, esp
    push esi
    call __pas_method_tobject_create
    pop esi
    mov eax, __pas_string_11
    call __pas_print_string
    call __pas_print_newline
    push 37
    push 1
    call _calloc
    add esp, 8
    push eax
    mov ecx, __pas_ctor_result__ctor_tform_26_35_35
    pop eax
    mov dword ptr [ecx], eax
    push esi
    mov ecx, __pas_ctor_result__ctor_tform_26_35_35
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_tform_create
    pop esi
    mov ecx, __pas_ctor_result__ctor_tform_26_35_35
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 1
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 10
    push eax
    mov ecx, esi
    add ecx, 1
    mov ecx, dword ptr [ecx]
    add ecx, 9
    mov eax, dword ptr [ecx]
    push eax
    call _ShowWindow@8
    mov ecx, esi
    add ecx, 1
    mov ecx, dword ptr [ecx]
    add ecx, 9
    mov eax, dword ptr [ecx]
    push eax
    call _UpdateWindow@4
    call __pas_global_runmessageloop
    mov esp, ebp
    pop ebp
    ret

; destructor TApplication.Destroy
__pas_method_tapplication_destroy:
    push ebp
    mov ebp, esp
    push esi
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_tobject_free
    pop esi
    push esi
    call __pas_method_tobject_destroy
    pop esi
    mov esp, ebp
    pop ebp
    ret

; constructor TFaz.Create
__pas_method_tfaz_create:
    push ebp
    mov ebp, esp
    push esi
    call __pas_method_tobject_create
    pop esi
    mov eax, __pas_string_12
    call __pas_print_string
    call __pas_print_newline
    mov esp, ebp
    pop ebp
    ret

; destructor TFaz.Destroy
__pas_method_tfaz_destroy:
    push ebp
    mov ebp, esp
    mov eax, __pas_string_13
    call __pas_print_string
    mov eax, __pas_string_14
    call __pas_print_string
    call __pas_print_newline
    push esi
    call __pas_method_tobject_destroy
    pop esi
    mov esp, ebp
    pop ebp
    ret

; procedure TFaz.Show
__pas_method_tfaz_show:
    push ebp
    mov ebp, esp
    mov eax, __pas_string_15
    call __pas_print_string
    mov eax, __pas_string_14
    call __pas_print_string
    call __pas_print_newline
    mov eax, __pas_string_16
    call __pas_print_string
    push esi
    call __pas_method_tobject_classname
    pop esi
    call __pas_print_string
    call __pas_print_newline
    mov eax, __pas_string_17
    call __pas_print_string
    mov eax, __pas_string_18
    call __pas_print_string
    call __pas_print_newline
    mov eax, __pas_string_19
    call __pas_print_string
    push esi
    call __pas_method_tobject_instancesize
    pop esi
    push eax
    mov ecx, __pas_param_global_inttostr_avalue_2
    pop eax
    mov dword ptr [ecx], eax
    call __pas_global_inttostr
    call __pas_print_string
    call __pas_print_newline
    mov esp, ebp
    pop ebp
    ret

; constructor TFoo.Create
__pas_method_tfoo_create:
    push ebp
    mov ebp, esp
    push esi
    call __pas_method_tfaz_create
    pop esi
    mov ecx, __pas_param_tfoo_create_avalue_32
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 1
    pop eax
    mov dword ptr [ecx], eax
    mov eax, __pas_string_20
    push eax
    mov ecx, esi
    add ecx, 5
    pop eax
    mov dword ptr [ecx], eax
    fld qword ptr [__pas_double_0]
    mov ecx, esi
    add ecx, 9
    fstp qword ptr [ecx]
    mov eax, __pas_string_21
    push eax
    mov ecx, esi
    add ecx, 17
    pop eax
    mov dword ptr [ecx], eax
    mov esp, ebp
    pop ebp
    ret

; destructor TFoo.Destroy
__pas_method_tfoo_destroy:
    push ebp
    mov ebp, esp
    mov eax, __pas_string_22
    call __pas_print_string
    mov eax, __pas_string_14
    call __pas_print_string
    call __pas_print_newline
    push esi
    call __pas_method_tfaz_destroy
    pop esi
    mov esp, ebp
    pop ebp
    ret

; procedure TFoo.Show
__pas_method_tfoo_show:
    push ebp
    mov ebp, esp
    mov eax, __pas_string_23
    call __pas_print_string
    mov eax, __pas_string_14
    call __pas_print_string
    call __pas_print_newline
    mov eax, __pas_string_16
    call __pas_print_string
    push esi
    call __pas_method_tobject_classname
    pop esi
    call __pas_print_string
    call __pas_print_newline
    mov eax, __pas_string_17
    call __pas_print_string
    mov eax, __pas_string_24
    call __pas_print_string
    call __pas_print_newline
    mov eax, __pas_string_19
    call __pas_print_string
    push esi
    call __pas_method_tobject_instancesize
    pop esi
    push eax
    mov ecx, __pas_param_global_inttostr_avalue_2
    pop eax
    mov dword ptr [ecx], eax
    call __pas_global_inttostr
    call __pas_print_string
    call __pas_print_newline
    push esi
    call __pas_method_tfaz_show
    pop esi
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

; IEEE-754 Double-Literale
__pas_double_0: dd 2061584302, 1074376212

; Pascal-Variablen
__pas_var_foo_0: dd 0 ; Foo: TFoo
__pas_var_application_1: dd 0 ; Application: TApplication
__pas_param_global_inttostr_avalue_2: dd 0 ; intern: integer
__pas_result_global_inttostr_result_3: dd 0 ; intern: string
__pas_param_global_strtoint_s_4: dd 0 ; intern: string
__pas_result_global_strtoint_result_5: dd 0 ; intern: integer
__pas_param_global_globalwindowproc_winhwnd_6: dd 0 ; intern: integer
__pas_param_global_globalwindowproc_umsg_7: dd 0 ; intern: integer
__pas_param_global_globalwindowproc_wparam_8: dd 0 ; intern: integer
__pas_param_global_globalwindowproc_lparam_9: dd 0 ; intern: integer
__pas_local_global_globalwindowproc_appform_10: dd 0 ; intern: TForm
__pas_local_global_globalwindowproc_createstruct_11: dd 0 ; intern: PCREATESTRUCTA
__pas_local_global_globalwindowproc_buttonwindow_12: dd 0 ; intern: integer
__pas_result_global_globalwindowproc_result_13: dd 0 ; intern: integer
__pas_local_global_runmessageloop_msg_14: db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ; intern: TMsg
__pas_local_global_runmessageloop_status_15: dd 0 ; intern: integer
__pas_result_tobject_classtype_result_16: dd 0 ; intern: pointer
__pas_result_tobject_classparent_result_17: dd 0 ; intern: pointer
__pas_result_tobject_classnameaddress_result_18: dd 0 ; intern: pointer
__pas_result_tobject_classname_result_19: dd 0 ; intern: string
__pas_result_tobject_instancesize_result_20: dd 0 ; intern: integer
__pas_param_tobject_inheritsfrom_aclass_21: dd 0 ; intern: pointer
__pas_result_tobject_inheritsfrom_result_22: db 0 ; intern: boolean
__pas_param_exception_create_amessage_23: dd 0 ; intern: string
__pas_local_twindow_create_registerresult_24: dd 0 ; intern: integer
__pas_local_twindow_create_winclass_25: db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ; intern: TWndClassA
__pas_param_twindow_dispatchmessage_winhwnd_26: dd 0 ; intern: integer
__pas_param_twindow_dispatchmessage_msg_27: dd 0 ; intern: integer
__pas_param_twindow_dispatchmessage_wparam_28: dd 0 ; intern: integer
__pas_param_twindow_dispatchmessage_lparam_29: dd 0 ; intern: integer
__pas_result_twindow_dispatchmessage_result_30: dd 0 ; intern: integer
__pas_result_twindow_gethandle_result_31: dd 0 ; intern: integer
__pas_param_tfoo_create_avalue_32: dd 0 ; intern: integer
__pas_ctor_result__ctor_tfoo_0_33_33: dd 0 ; intern: TFoo
__pas_ctor_result__ctor_tapplication_4_34_34: dd 0 ; intern: TApplication
__pas_ctor_result__ctor_tform_26_35_35: dd 0 ; intern: TForm

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
__pas_string_10: db 84, 70, 111, 114, 109, 0
__pas_string_11: db 84, 65, 112, 112, 58, 32, 67, 114, 101, 97, 116, 101, 0
__pas_string_12: db 84, 70, 97, 122, 32, 67, 114, 101, 97, 116, 101, 0
__pas_string_13: db 84, 70, 97, 122, 32, 68, 101, 115, 116, 114, 111, 121, 0
__pas_string_14: db 0
__pas_string_15: db 84, 70, 97, 122, 32, 83, 104, 111, 119, 0
__pas_string_16: db 32, 32, 82, 117, 110, 116, 105, 109, 101, 32, 99, 108, 97, 115, 115, 58, 32, 0
__pas_string_17: db 32, 32, 77, 101, 116, 104, 111, 100, 32, 32, 111, 119, 110, 101, 114, 58, 32, 0
__pas_string_18: db 84, 70, 97, 122, 0
__pas_string_19: db 32, 32, 83, 105, 122, 101, 32, 32, 32, 32, 32, 32, 32, 32, 32, 58, 32, 0
__pas_string_20: db 72, 101, 108, 108, 111, 0
__pas_string_21: db 87, 111, 114, 108, 100, 32, 33, 0
__pas_string_22: db 84, 70, 111, 111, 32, 68, 101, 115, 116, 114, 111, 121, 0
__pas_string_23: db 84, 70, 111, 111, 32, 83, 104, 111, 119, 0
__pas_string_24: db 84, 70, 111, 111, 0

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
__pas_double_scratch: resq 1
__pas_double_int_scratch: resd 1
__pas_double_buffer: resb 64

; Pascal TRY/EXCEPT exception frames (PE32, BSS)
__pas_exc_env_1: resb 24
__pas_exc_frame_2: resb 268
