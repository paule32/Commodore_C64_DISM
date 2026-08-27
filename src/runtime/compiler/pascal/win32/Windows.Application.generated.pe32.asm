; Von Pascal erzeugtes Windows-PE32-Unit-Modul
; Unit: Windows.Application
bits 32
global __unit_Windows_Application
import _calloc, "msvcrt.dll", "calloc"
extern __pas_System_Strings_IntToStr
extern __pas_System_Strings_StrToInt
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
extern __pas_method_exception_create
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
__unit_Windows_Application:
    ret

; function GlobalWindowProc
global __pas_Windows_Application_GlobalWindowProc
__pas_Windows_Application_GlobalWindowProc:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    push eax
    mov ecx, __pas_param_global_globalwindowproc_winhwnd_0
    pop eax
    mov dword ptr [ecx], eax
    mov eax, dword ptr [ebp+12]
    push eax
    mov ecx, __pas_param_global_globalwindowproc_umsg_1
    pop eax
    mov dword ptr [ecx], eax
    mov eax, dword ptr [ebp+16]
    push eax
    mov ecx, __pas_param_global_globalwindowproc_wparam_2
    pop eax
    mov dword ptr [ecx], eax
    mov eax, dword ptr [ebp+20]
    push eax
    mov ecx, __pas_param_global_globalwindowproc_lparam_3
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    mov ecx, __pas_local_global_globalwindowproc_appform_4
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    mov ecx, __pas_local_global_globalwindowproc_createstruct_5
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    mov ecx, __pas_local_global_globalwindowproc_buttonwindow_6
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    mov ecx, __pas_result_global_globalwindowproc_result_7
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_global_globalwindowproc_umsg_1
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 129
    mov edx, eax
    pop eax
    cmp eax, edx
    sete al
    movzx eax, al
    test eax, eax
    jz __pas_unit_Windows_Application_if_else_1
    mov ecx, __pas_param_global_globalwindowproc_lparam_3
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_local_global_globalwindowproc_createstruct_5
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_local_global_globalwindowproc_createstruct_5
    mov ecx, dword ptr [ecx]
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_local_global_globalwindowproc_appform_4
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_local_global_globalwindowproc_appform_4
    mov eax, dword ptr [ecx]
    test eax, eax
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_unit_Windows_Application_if_else_3
    mov ecx, __pas_param_global_globalwindowproc_winhwnd_0
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_local_global_globalwindowproc_appform_4
    mov ecx, dword ptr [ecx]
    add ecx, 9
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_local_global_globalwindowproc_appform_4
    mov eax, dword ptr [ecx]
    push eax
    mov eax, -21
    push eax
    mov ecx, __pas_param_global_globalwindowproc_winhwnd_0
    mov eax, dword ptr [ecx]
    push eax
    call _SetWindowLongA@12
    jmp __pas_unit_Windows_Application_if_end_4
__pas_unit_Windows_Application_if_else_3:
__pas_unit_Windows_Application_if_end_4:
    jmp __pas_unit_Windows_Application_if_end_2
__pas_unit_Windows_Application_if_else_1:
    mov eax, -21
    push eax
    mov ecx, __pas_param_global_globalwindowproc_winhwnd_0
    mov eax, dword ptr [ecx]
    push eax
    call _GetWindowLongA@8
    push eax
    mov ecx, __pas_local_global_globalwindowproc_appform_4
    pop eax
    mov dword ptr [ecx], eax
__pas_unit_Windows_Application_if_end_2:
    mov ecx, __pas_local_global_globalwindowproc_appform_4
    mov eax, dword ptr [ecx]
    test eax, eax
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_unit_Windows_Application_if_else_5
    mov ecx, __pas_param_global_globalwindowproc_winhwnd_0
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_twindow_dispatchmessage_winhwnd_12
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_global_globalwindowproc_umsg_1
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_twindow_dispatchmessage_msg_13
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_global_globalwindowproc_wparam_2
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_twindow_dispatchmessage_wparam_14
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_global_globalwindowproc_lparam_3
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_twindow_dispatchmessage_lparam_15
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_local_global_globalwindowproc_appform_4
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_twindow_dispatchmessage
    push eax
    mov ecx, __pas_result_global_globalwindowproc_result_7
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_global_globalwindowproc_umsg_1
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 130
    mov edx, eax
    pop eax
    cmp eax, edx
    sete al
    movzx eax, al
    test eax, eax
    jz __pas_unit_Windows_Application_if_else_7
    mov eax, 0
    push eax
    mov eax, -21
    push eax
    mov ecx, __pas_param_global_globalwindowproc_winhwnd_0
    mov eax, dword ptr [ecx]
    push eax
    call _SetWindowLongA@12
    mov eax, 0
    push eax
    mov ecx, __pas_local_global_globalwindowproc_appform_4
    mov ecx, dword ptr [ecx]
    add ecx, 9
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_local_global_globalwindowproc_appform_4
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_tobject_free
    mov ecx, __pas_result_global_globalwindowproc_result_7
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret 16
    jmp __pas_unit_Windows_Application_if_end_8
__pas_unit_Windows_Application_if_else_7:
__pas_unit_Windows_Application_if_end_8:
    mov ecx, __pas_param_global_globalwindowproc_umsg_1
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 2
    mov edx, eax
    pop eax
    cmp eax, edx
    sete al
    movzx eax, al
    test eax, eax
    jz __pas_unit_Windows_Application_if_else_9
    mov eax, 0
    push eax
    call _PostQuitMessage@4
    mov eax, 0
    push eax
    mov ecx, __pas_result_global_globalwindowproc_result_7
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_global_globalwindowproc_result_7
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret 16
    jmp __pas_unit_Windows_Application_if_end_10
__pas_unit_Windows_Application_if_else_9:
__pas_unit_Windows_Application_if_end_10:
    mov ecx, __pas_result_global_globalwindowproc_result_7
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret 16
    jmp __pas_unit_Windows_Application_if_end_6
__pas_unit_Windows_Application_if_else_5:
__pas_unit_Windows_Application_if_end_6:
    mov ecx, __pas_param_global_globalwindowproc_umsg_1
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 2
    mov edx, eax
    pop eax
    cmp eax, edx
    sete al
    movzx eax, al
    test eax, eax
    jz __pas_unit_Windows_Application_if_else_11
    mov eax, 0
    push eax
    call _PostQuitMessage@4
    mov eax, 0
    push eax
    mov ecx, __pas_result_global_globalwindowproc_result_7
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_global_globalwindowproc_result_7
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret 16
    jmp __pas_unit_Windows_Application_if_end_12
__pas_unit_Windows_Application_if_else_11:
__pas_unit_Windows_Application_if_end_12:
    mov ecx, __pas_param_global_globalwindowproc_lparam_3
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_global_globalwindowproc_wparam_2
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_global_globalwindowproc_umsg_1
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_global_globalwindowproc_winhwnd_0
    mov eax, dword ptr [ecx]
    push eax
    call _DefWindowProcA@16
    push eax
    mov ecx, __pas_result_global_globalwindowproc_result_7
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_global_globalwindowproc_result_7
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret 16

; procedure RunMessageLoop
global __pas_Windows_Application_RunMessageLoop
__pas_Windows_Application_RunMessageLoop:
    push ebp
    mov ebp, esp
    mov ecx, __pas_local_global_runmessageloop_msg_8
    mov dword ptr [ecx], 0
    mov dword ptr [ecx+4], 0
    mov dword ptr [ecx+8], 0
    mov dword ptr [ecx+12], 0
    mov dword ptr [ecx+16], 0
    mov dword ptr [ecx+20], 0
    mov dword ptr [ecx+24], 0
    xor eax, eax
    push eax
    mov ecx, __pas_local_global_runmessageloop_status_9
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 0
    push eax
    mov eax, 0
    push eax
    mov eax, 0
    push eax
    mov ecx, __pas_local_global_runmessageloop_msg_8
    push ecx
    call _GetMessageA@16
    push eax
    mov ecx, __pas_local_global_runmessageloop_status_9
    pop eax
    mov dword ptr [ecx], eax
__pas_unit_Windows_Application_while_condition_13:
    mov ecx, __pas_local_global_runmessageloop_status_9
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    mov edx, eax
    pop eax
    cmp eax, edx
    setg al
    movzx eax, al
    test eax, eax
    jz __pas_unit_Windows_Application_while_end_14
    mov ecx, __pas_local_global_runmessageloop_msg_8
    push ecx
    call _TranslateMessage@4
    mov ecx, __pas_local_global_runmessageloop_msg_8
    push ecx
    call _DispatchMessageA@4
    mov eax, 0
    push eax
    mov eax, 0
    push eax
    mov eax, 0
    push eax
    mov ecx, __pas_local_global_runmessageloop_msg_8
    push ecx
    call _GetMessageA@16
    push eax
    mov ecx, __pas_local_global_runmessageloop_status_9
    pop eax
    mov dword ptr [ecx], eax
    jmp __pas_unit_Windows_Application_while_condition_13
__pas_unit_Windows_Application_while_end_14:
    mov esp, ebp
    pop ebp
    ret

; constructor TWindow.Create
global __pas_method_twindow_create
__pas_method_twindow_create:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_local_twindow_create_registerresult_10
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_local_twindow_create_winclass_11
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
    mov eax, __pas_unit_Windows_Application_string_0
    call __pas_unit_Windows_Application_print_string
    call __pas_unit_Windows_Application_print_newline
    mov eax, __pas_unit_Windows_Application_string_1
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
    mov ecx, __pas_local_twindow_create_winclass_11
    pop eax
    mov dword ptr [ecx], eax
    mov eax, __pas_Windows_Application_GlobalWindowProc
    push eax
    mov ecx, __pas_local_twindow_create_winclass_11
    add ecx, 4
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 0
    push eax
    mov ecx, __pas_local_twindow_create_winclass_11
    add ecx, 8
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 0
    push eax
    mov ecx, __pas_local_twindow_create_winclass_11
    add ecx, 12
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, esi
    add ecx, 5
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_local_twindow_create_winclass_11
    add ecx, 16
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 32512
    push eax
    mov eax, 0
    push eax
    call _LoadIconA@8
    push eax
    mov ecx, __pas_local_twindow_create_winclass_11
    add ecx, 20
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 32512
    push eax
    mov eax, 0
    push eax
    call _LoadCursorA@8
    push eax
    mov ecx, __pas_local_twindow_create_winclass_11
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
    mov ecx, __pas_local_twindow_create_winclass_11
    add ecx, 28
    pop eax
    mov dword ptr [ecx], eax
    xor eax, eax
    push eax
    mov ecx, __pas_local_twindow_create_winclass_11
    add ecx, 32
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_local_twindow_create_winclass_11
    add ecx, 36
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_local_twindow_create_winclass_11
    push ecx
    call _RegisterClassA@4
    push eax
    mov ecx, __pas_local_twindow_create_registerresult_10
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_local_twindow_create_registerresult_10
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    mov edx, eax
    pop eax
    cmp eax, edx
    sete al
    movzx eax, al
    test eax, eax
    jz __pas_unit_Windows_Application_if_else_15
    mov eax, 0
    push eax
    mov eax, 16
    mov edx, eax
    pop eax
    add eax, edx
    push eax
    mov eax, __pas_unit_Windows_Application_string_2
    push eax
    mov eax, __pas_unit_Windows_Application_string_3
    push eax
    mov eax, 0
    push eax
    call _MessageBoxA@16
    mov eax, 3
    push eax
    call _ExitProcess@4
    jmp __pas_unit_Windows_Application_if_end_16
__pas_unit_Windows_Application_if_else_15:
__pas_unit_Windows_Application_if_end_16:
    mov eax, __pas_unit_Windows_Application_string_4
    call __pas_unit_Windows_Application_print_string
    call __pas_unit_Windows_Application_print_newline
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
    mov eax, __pas_unit_Windows_Application_string_5
    call __pas_unit_Windows_Application_print_string
    call __pas_unit_Windows_Application_print_newline
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
    jz __pas_unit_Windows_Application_if_else_17
    mov eax, __pas_unit_Windows_Application_string_6
    call __pas_unit_Windows_Application_print_string
    call __pas_unit_Windows_Application_print_newline
    mov eax, 0
    push eax
    mov eax, 16
    mov edx, eax
    pop eax
    add eax, edx
    push eax
    mov eax, __pas_unit_Windows_Application_string_2
    push eax
    mov eax, __pas_unit_Windows_Application_string_7
    push eax
    mov eax, 0
    push eax
    call _MessageBoxA@16
    mov eax, 2
    push eax
    call _ExitProcess@4
    jmp __pas_unit_Windows_Application_if_end_18
__pas_unit_Windows_Application_if_else_17:
__pas_unit_Windows_Application_if_end_18:
    mov eax, __pas_unit_Windows_Application_string_8
    call __pas_unit_Windows_Application_print_string
    call __pas_unit_Windows_Application_print_newline
    mov esp, ebp
    pop ebp
    ret

; destructor TWindow.Destroy
global __pas_method_twindow_destroy
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
global __pas_method_twindow_gethandle
__pas_method_twindow_gethandle:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_twindow_gethandle_result_17
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, esi
    add ecx, 9
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_result_twindow_gethandle_result_17
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_twindow_gethandle_result_17
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function TWindow.DispatchMessage
global __pas_method_twindow_dispatchmessage
__pas_method_twindow_dispatchmessage:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_twindow_dispatchmessage_result_16
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_twindow_dispatchmessage_lparam_15
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_twindow_dispatchmessage_wparam_14
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_twindow_dispatchmessage_msg_13
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_twindow_dispatchmessage_winhwnd_12
    mov eax, dword ptr [ecx]
    push eax
    call _DefWindowProcA@16
    push eax
    mov ecx, __pas_result_twindow_dispatchmessage_result_16
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_twindow_dispatchmessage_result_16
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; constructor TForm.Create
global __pas_method_tform_create
__pas_method_tform_create:
    push ebp
    mov ebp, esp
    push esi
    call __pas_method_twindow_create
    pop esi
    mov eax, __pas_unit_Windows_Application_string_9
    call __pas_unit_Windows_Application_print_string
    call __pas_unit_Windows_Application_print_newline
    mov eax, __pas_unit_Windows_Application_string_10
    push eax
    mov ecx, esi
    add ecx, 33
    pop eax
    mov dword ptr [ecx], eax
    mov esp, ebp
    pop ebp
    ret

; destructor TForm.Destroy
global __pas_method_tform_destroy
__pas_method_tform_destroy:
    push ebp
    mov ebp, esp
    push esi
    call __pas_method_twindow_destroy
    pop esi
    mov esp, ebp
    pop ebp
    ret

; function TApplication.getHandle
global __pas_method_tapplication_gethandle
__pas_method_tapplication_gethandle:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tapplication_gethandle_result_18
    pop eax
    mov dword ptr [ecx], eax
    push esi
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_twindow_gethandle
    pop esi
    push eax
    mov ecx, __pas_result_tapplication_gethandle_result_18
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tapplication_gethandle_result_18
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; constructor TApplication.Create
global __pas_method_tapplication_create
__pas_method_tapplication_create:
    push ebp
    mov ebp, esp
    push esi
    call __pas_method_tobject_create
    pop esi
    mov eax, __pas_unit_Windows_Application_string_11
    call __pas_unit_Windows_Application_print_string
    call __pas_unit_Windows_Application_print_newline
    push 37
    push 1
    call _calloc
    add esp, 8
    push eax
    mov ecx, __pas_ctor_result__ctor_tform_18_19_19
    pop eax
    mov dword ptr [ecx], eax
    push esi
    mov ecx, __pas_ctor_result__ctor_tform_18_19_19
    mov eax, dword ptr [ecx]
    mov esi, eax
    call __pas_method_tform_create
    pop esi
    mov ecx, __pas_ctor_result__ctor_tform_18_19_19
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 1
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 10
    push eax
    push esi
    call __pas_method_tapplication_gethandle
    pop esi
    push eax
    call _ShowWindow@8
    push esi
    call __pas_method_tapplication_gethandle
    pop esi
    push eax
    call _UpdateWindow@4
    call __pas_Windows_Application_RunMessageLoop
    mov esp, ebp
    pop ebp
    ret

; destructor TApplication.Destroy
global __pas_method_tapplication_destroy
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

__pas_unit_Windows_Application_write_cstring:
    push eax
    push eax
    call lstrlenA
    mov edx, eax
    pop eax
    push 0
    push __pas_unit_Windows_Application_written
    push edx
    push eax
    push dword ptr [__pas_unit_Windows_Application_stdout_handle]
    call WriteFile
    ret

__pas_unit_Windows_Application_print_string:
    call __pas_unit_Windows_Application_write_cstring
    ret

__pas_unit_Windows_Application_print_newline:
    mov eax, __pas_unit_Windows_Application_newline
    call __pas_unit_Windows_Application_write_cstring
    ret

align 4
__pas_unit_Windows_Application_fmt_s: db 37, 115, 0
__pas_unit_Windows_Application_fmt_d: db 37, 100, 0
__pas_unit_Windows_Application_fmt_c: db 37, 99, 0
__pas_unit_Windows_Application_newline: db 13, 10, 0
__pas_unit_Windows_Application_clear_sequence: db 27, 91, 50, 74, 27, 91, 72, 0
__pas_unit_Windows_Application_range_message: db 82, 97, 110, 103, 101, 32, 101, 114, 114, 111, 114, 13, 10, 0

; Pascal-Variablen
__pas_param_global_globalwindowproc_winhwnd_0: dd 0 ; intern: integer
__pas_param_global_globalwindowproc_umsg_1: dd 0 ; intern: integer
__pas_param_global_globalwindowproc_wparam_2: dd 0 ; intern: integer
__pas_param_global_globalwindowproc_lparam_3: dd 0 ; intern: integer
__pas_local_global_globalwindowproc_appform_4: dd 0 ; intern: TForm
__pas_local_global_globalwindowproc_createstruct_5: dd 0 ; intern: PCREATESTRUCTA
__pas_local_global_globalwindowproc_buttonwindow_6: dd 0 ; intern: integer
__pas_result_global_globalwindowproc_result_7: dd 0 ; intern: integer
__pas_local_global_runmessageloop_msg_8: db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ; intern: TMsg
__pas_local_global_runmessageloop_status_9: dd 0 ; intern: integer
__pas_local_twindow_create_registerresult_10: dd 0 ; intern: integer
__pas_local_twindow_create_winclass_11: db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ; intern: TWndClassA
__pas_param_twindow_dispatchmessage_winhwnd_12: dd 0 ; intern: integer
__pas_param_twindow_dispatchmessage_msg_13: dd 0 ; intern: integer
__pas_param_twindow_dispatchmessage_wparam_14: dd 0 ; intern: integer
__pas_param_twindow_dispatchmessage_lparam_15: dd 0 ; intern: integer
__pas_result_twindow_dispatchmessage_result_16: dd 0 ; intern: integer
__pas_result_twindow_gethandle_result_17: dd 0 ; intern: integer
__pas_result_tapplication_gethandle_result_18: dd 0 ; intern: integer
__pas_ctor_result__ctor_tform_18_19_19: dd 0 ; intern: TForm

; Nullterminierte Windows-Latin-1-Zeichenketten
__pas_unit_Windows_Application_string_0: db 84, 87, 105, 110, 100, 111, 119, 58, 32, 67, 114, 101, 97, 116, 101, 0
__pas_unit_Windows_Application_string_1: db 87, 105, 110, 51, 50, 71, 117, 105, 46, 87, 105, 110, 100, 111, 119, 0
__pas_unit_Windows_Application_string_2: db 87, 105, 110, 51, 50, 45, 70, 101, 104, 108, 101, 114, 0
__pas_unit_Windows_Application_string_3: db 68, 105, 101, 32, 70, 101, 110, 115, 116, 101, 114, 107, 108, 97, 115, 115, 101, 32, 107, 111, 110, 110, 116, 101, 32, 110, 105, 99, 104, 116, 32, 114, 101, 103, 105, 115, 116, 114, 105, 101, 114, 116, 32, 119, 101, 114, 100, 101, 110, 46, 0
__pas_unit_Windows_Application_string_4: db 82, 101, 103, 105, 115, 116, 101, 114, 32, 111, 107, 0
__pas_unit_Windows_Application_string_5: db 87, 105, 110, 67, 114, 101, 97, 116, 101, 32, 111, 107, 0
__pas_unit_Windows_Application_string_6: db 72, 97, 110, 100, 108, 101, 32, 101, 114, 114, 111, 114, 0
__pas_unit_Windows_Application_string_7: db 68, 97, 115, 32, 72, 97, 117, 112, 116, 102, 101, 110, 115, 116, 101, 114, 32, 107, 111, 110, 110, 116, 101, 32, 110, 105, 99, 104, 116, 32, 101, 114, 122, 101, 117, 103, 116, 32, 119, 101, 114, 100, 101, 110, 46, 0
__pas_unit_Windows_Application_string_8: db 84, 87, 105, 110, 100, 111, 119, 58, 32, 119, 105, 110, 32, 104, 97, 110, 100, 108, 101, 32, 111, 107, 0
__pas_unit_Windows_Application_string_9: db 84, 70, 111, 114, 109, 58, 32, 67, 114, 101, 97, 116, 101, 0
__pas_unit_Windows_Application_string_10: db 84, 70, 111, 114, 109, 0
__pas_unit_Windows_Application_string_11: db 84, 65, 112, 112, 58, 32, 67, 114, 101, 97, 116, 101, 0
