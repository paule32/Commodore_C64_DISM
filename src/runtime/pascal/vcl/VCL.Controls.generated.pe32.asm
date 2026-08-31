; Von Pascal erzeugtes Windows-PE32-Unit-Modul
; Unit: VCL.Controls
bits 32
global __unit_VCL_Controls
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
import _jit_raise, "libruntime_mini.dll", "_jit_raise"
__unit_VCL_Controls:
    ret

; function TControl.GetWindowClass
global __pas_method_tcontrol_getwindowclass
__pas_method_tcontrol_getwindowclass:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tcontrol_getwindowclass_result_2
    pop eax
    mov dword ptr [ecx], eax
    mov eax, __pas_unit_VCL_Controls_string_0
    push eax
    mov ecx, __pas_result_tcontrol_getwindowclass_result_2
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tcontrol_getwindowclass_result_2
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function TControl.GetWindowStyle
global __pas_method_tcontrol_getwindowstyle
__pas_method_tcontrol_getwindowstyle:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tcontrol_getwindowstyle_result_3
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 1073741824
    push eax
    mov eax, 67108864
    mov edx, eax
    pop eax
    or eax, edx
    push eax
    mov ecx, __pas_result_tcontrol_getwindowstyle_result_3
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tcontrol_getwindowstyle_result_3
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function TControl.GetWindowExStyle
global __pas_method_tcontrol_getwindowexstyle
__pas_method_tcontrol_getwindowexstyle:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tcontrol_getwindowexstyle_result_4
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 0
    push eax
    mov ecx, __pas_result_tcontrol_getwindowexstyle_result_4
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tcontrol_getwindowexstyle_result_4
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; procedure TControl.CreateHandle
global __pas_method_tcontrol_createhandle
__pas_method_tcontrol_createhandle:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_local_tcontrol_createhandle_style_5
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    mov edx, eax
    pop eax
    cmp eax, edx
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_unit_VCL_Controls_if_else_1
    mov esp, ebp
    pop ebp
    ret
    jmp __pas_unit_VCL_Controls_if_end_2
__pas_unit_VCL_Controls_if_else_1:
__pas_unit_VCL_Controls_if_end_2:
    push esi
    call __pas_method_tcontrol_getwindowstyle
    pop esi
    push eax
    mov ecx, __pas_local_tcontrol_createhandle_style_5
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, esi
    add ecx, 33
    movzx eax, byte ptr [ecx]
    test eax, eax
    jz __pas_unit_VCL_Controls_if_else_3
    mov ecx, __pas_local_tcontrol_createhandle_style_5
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 268435456
    mov edx, eax
    pop eax
    or eax, edx
    push eax
    mov ecx, __pas_local_tcontrol_createhandle_style_5
    pop eax
    mov dword ptr [ecx], eax
    jmp __pas_unit_VCL_Controls_if_end_4
__pas_unit_VCL_Controls_if_else_3:
__pas_unit_VCL_Controls_if_end_4:
    mov ecx, esi
    add ecx, 34
    movzx eax, byte ptr [ecx]
    cmp eax, 0
    sete al
    movzx eax, al
    test eax, eax
    jz __pas_unit_VCL_Controls_if_else_5
    mov ecx, __pas_local_tcontrol_createhandle_style_5
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 134217728
    mov edx, eax
    pop eax
    or eax, edx
    push eax
    mov ecx, __pas_local_tcontrol_createhandle_style_5
    pop eax
    mov dword ptr [ecx], eax
    jmp __pas_unit_VCL_Controls_if_end_6
__pas_unit_VCL_Controls_if_else_5:
__pas_unit_VCL_Controls_if_end_6:
    mov eax, esi
    push eax
    xor eax, eax
    push eax
    call _GetModuleHandleA@4
    push eax
    mov ecx, esi
    add ecx, 9
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 5
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 25
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 21
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 17
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 13
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_local_tcontrol_createhandle_style_5
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 29
    mov eax, dword ptr [ecx]
    push eax
    push esi
    call __pas_method_tcontrol_getwindowclass
    pop esi
    push eax
    push esi
    call __pas_method_tcontrol_getwindowexstyle
    pop esi
    push eax
    call _CreateWindowExA@48
    push eax
    mov ecx, esi
    add ecx, 1
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    mov edx, eax
    pop eax
    cmp eax, edx
    sete al
    movzx eax, al
    test eax, eax
    jz __pas_unit_VCL_Controls_if_else_7
    mov eax, __pas_unit_VCL_Controls_string_1
    push eax
    push 7
    call _jit_raise
    add esp, 8
    jmp __pas_unit_VCL_Controls_if_end_8
__pas_unit_VCL_Controls_if_else_7:
__pas_unit_VCL_Controls_if_end_8:
    mov esp, ebp
    pop ebp
    ret

; procedure TControl.DestroyHandle
global __pas_method_tcontrol_destroyhandle
__pas_method_tcontrol_destroyhandle:
    push ebp
    mov ebp, esp
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    mov edx, eax
    pop eax
    cmp eax, edx
    sete al
    movzx eax, al
    test eax, eax
    jz __pas_unit_VCL_Controls_if_else_9
    mov esp, ebp
    pop ebp
    ret
    jmp __pas_unit_VCL_Controls_if_end_10
__pas_unit_VCL_Controls_if_else_9:
__pas_unit_VCL_Controls_if_end_10:
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    call _IsWindow@4
    test eax, eax
    jz __pas_unit_VCL_Controls_if_else_11
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    call _DestroyWindow@4
    jmp __pas_unit_VCL_Controls_if_end_12
__pas_unit_VCL_Controls_if_else_11:
__pas_unit_VCL_Controls_if_end_12:
    mov eax, 0
    push eax
    mov ecx, esi
    add ecx, 1
    pop eax
    mov dword ptr [ecx], eax
    mov esp, ebp
    pop ebp
    ret

; constructor TControl.Create
global __pas_method_tcontrol_create
__pas_method_tcontrol_create:
    push ebp
    mov ebp, esp
    push esi
    call __pas_method_tobject_create
    pop esi
    mov eax, 0
    push eax
    mov ecx, esi
    add ecx, 1
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_tcontrol_create_aparent_0
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 5
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_tcontrol_create_acontrolid_1
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 9
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 0
    push eax
    mov ecx, esi
    add ecx, 13
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 0
    push eax
    mov ecx, esi
    add ecx, 17
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 80
    push eax
    mov ecx, esi
    add ecx, 21
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 25
    push eax
    mov ecx, esi
    add ecx, 25
    pop eax
    mov dword ptr [ecx], eax
    mov eax, __pas_unit_VCL_Controls_string_0
    push eax
    mov ecx, esi
    add ecx, 29
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 1
    push eax
    mov ecx, esi
    add ecx, 33
    pop eax
    mov byte ptr [ecx], al
    mov eax, 1
    push eax
    mov ecx, esi
    add ecx, 34
    pop eax
    mov byte ptr [ecx], al
    mov esp, ebp
    pop ebp
    ret

; destructor TControl.Destroy
global __pas_method_tcontrol_destroy
__pas_method_tcontrol_destroy:
    push ebp
    mov ebp, esp
    push esi
    call __pas_method_tcontrol_destroyhandle
    pop esi
    push esi
    call __pas_method_tobject_destroy
    pop esi
    mov esp, ebp
    pop ebp
    ret

; procedure TControl.SetBounds
global __pas_method_tcontrol_setbounds
__pas_method_tcontrol_setbounds:
    push ebp
    mov ebp, esp
    mov ecx, __pas_param_tcontrol_setbounds_aleft_6
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 13
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_tcontrol_setbounds_atop_7
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 17
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_tcontrol_setbounds_awidth_8
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 21
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_tcontrol_setbounds_aheight_9
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 25
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    mov edx, eax
    pop eax
    cmp eax, edx
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_unit_VCL_Controls_if_else_13
    mov eax, 1
    push eax
    mov ecx, esi
    add ecx, 25
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 21
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 17
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 13
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    call _MoveWindow@24
    jmp __pas_unit_VCL_Controls_if_end_14
__pas_unit_VCL_Controls_if_else_13:
__pas_unit_VCL_Controls_if_end_14:
    mov esp, ebp
    pop ebp
    ret

; procedure TControl.SetCaption
global __pas_method_tcontrol_setcaption
__pas_method_tcontrol_setcaption:
    push ebp
    mov ebp, esp
    mov ecx, __pas_param_tcontrol_setcaption_acaption_10
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 29
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    mov edx, eax
    pop eax
    cmp eax, edx
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_unit_VCL_Controls_if_else_15
    mov ecx, esi
    add ecx, 29
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    call _SetWindowTextA@8
    jmp __pas_unit_VCL_Controls_if_end_16
__pas_unit_VCL_Controls_if_else_15:
__pas_unit_VCL_Controls_if_end_16:
    mov esp, ebp
    pop ebp
    ret

; procedure TControl.Show
global __pas_method_tcontrol_show
__pas_method_tcontrol_show:
    push ebp
    mov ebp, esp
    mov eax, 1
    push eax
    mov ecx, esi
    add ecx, 33
    pop eax
    mov byte ptr [ecx], al
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    mov edx, eax
    pop eax
    cmp eax, edx
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_unit_VCL_Controls_if_else_17
    mov eax, 5
    push eax
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    call _ShowWindow@8
    jmp __pas_unit_VCL_Controls_if_end_18
__pas_unit_VCL_Controls_if_else_17:
__pas_unit_VCL_Controls_if_end_18:
    mov esp, ebp
    pop ebp
    ret

; procedure TControl.Hide
global __pas_method_tcontrol_hide
__pas_method_tcontrol_hide:
    push ebp
    mov ebp, esp
    mov eax, 0
    push eax
    mov ecx, esi
    add ecx, 33
    pop eax
    mov byte ptr [ecx], al
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    mov edx, eax
    pop eax
    cmp eax, edx
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_unit_VCL_Controls_if_else_19
    mov eax, 0
    push eax
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    call _ShowWindow@8
    jmp __pas_unit_VCL_Controls_if_end_20
__pas_unit_VCL_Controls_if_else_19:
__pas_unit_VCL_Controls_if_end_20:
    mov esp, ebp
    pop ebp
    ret

; procedure TControl.Enable
global __pas_method_tcontrol_enable
__pas_method_tcontrol_enable:
    push ebp
    mov ebp, esp
    mov eax, 1
    push eax
    mov ecx, esi
    add ecx, 34
    pop eax
    mov byte ptr [ecx], al
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    mov edx, eax
    pop eax
    cmp eax, edx
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_unit_VCL_Controls_if_else_21
    mov eax, 1
    push eax
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    call _EnableWindow@8
    jmp __pas_unit_VCL_Controls_if_end_22
__pas_unit_VCL_Controls_if_else_21:
__pas_unit_VCL_Controls_if_end_22:
    mov esp, ebp
    pop ebp
    ret

; procedure TControl.Disable
global __pas_method_tcontrol_disable
__pas_method_tcontrol_disable:
    push ebp
    mov ebp, esp
    mov eax, 0
    push eax
    mov ecx, esi
    add ecx, 34
    pop eax
    mov byte ptr [ecx], al
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    mov eax, 0
    mov edx, eax
    pop eax
    cmp eax, edx
    setne al
    movzx eax, al
    test eax, eax
    jz __pas_unit_VCL_Controls_if_else_23
    mov eax, 0
    push eax
    mov ecx, esi
    add ecx, 1
    mov eax, dword ptr [ecx]
    push eax
    call _EnableWindow@8
    jmp __pas_unit_VCL_Controls_if_end_24
__pas_unit_VCL_Controls_if_else_23:
__pas_unit_VCL_Controls_if_end_24:
    mov esp, ebp
    pop ebp
    ret

; function TButton.GetWindowClass
global __pas_method_tbutton_getwindowclass
__pas_method_tbutton_getwindowclass:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tbutton_getwindowclass_result_14
    pop eax
    mov dword ptr [ecx], eax
    mov eax, __pas_unit_VCL_Controls_string_2
    push eax
    mov ecx, __pas_result_tbutton_getwindowclass_result_14
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tbutton_getwindowclass_result_14
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; function TButton.GetWindowStyle
global __pas_method_tbutton_getwindowstyle
__pas_method_tbutton_getwindowstyle:
    push ebp
    mov ebp, esp
    xor eax, eax
    push eax
    mov ecx, __pas_result_tbutton_getwindowstyle_result_15
    pop eax
    mov dword ptr [ecx], eax
    push esi
    call __pas_method_tcontrol_getwindowstyle
    pop esi
    push eax
    mov eax, 65536
    mov edx, eax
    pop eax
    or eax, edx
    push eax
    mov eax, 0
    mov edx, eax
    pop eax
    or eax, edx
    push eax
    mov ecx, __pas_result_tbutton_getwindowstyle_result_15
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_result_tbutton_getwindowstyle_result_15
    mov eax, dword ptr [ecx]
    mov esp, ebp
    pop ebp
    ret

; constructor TButton.Create
global __pas_method_tbutton_create
__pas_method_tbutton_create:
    push ebp
    mov ebp, esp
    mov ecx, __pas_param_tbutton_create_aparent_11
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_tcontrol_create_aparent_0
    pop eax
    mov dword ptr [ecx], eax
    mov ecx, __pas_param_tbutton_create_acontrolid_12
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_tcontrol_create_acontrolid_1
    pop eax
    mov dword ptr [ecx], eax
    push esi
    call __pas_method_tcontrol_create
    pop esi
    mov ecx, __pas_param_tbutton_create_acaption_13
    mov eax, dword ptr [ecx]
    push eax
    mov ecx, __pas_param_tcontrol_setcaption_acaption_10
    pop eax
    mov dword ptr [ecx], eax
    push esi
    call __pas_method_tcontrol_setcaption
    pop esi
    mov eax, 10
    push eax
    mov ecx, __pas_param_tcontrol_setbounds_aleft_6
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 10
    push eax
    mov ecx, __pas_param_tcontrol_setbounds_atop_7
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 100
    push eax
    mov ecx, __pas_param_tcontrol_setbounds_awidth_8
    pop eax
    mov dword ptr [ecx], eax
    mov eax, 32
    push eax
    mov ecx, __pas_param_tcontrol_setbounds_aheight_9
    pop eax
    mov dword ptr [ecx], eax
    push esi
    call __pas_method_tcontrol_setbounds
    pop esi
    push esi
    call __pas_method_tcontrol_createhandle
    pop esi
    mov esp, ebp
    pop ebp
    ret

; destructor TButton.Destroy
global __pas_method_tbutton_destroy
__pas_method_tbutton_destroy:
    push ebp
    mov ebp, esp
    push esi
    call __pas_method_tcontrol_destroy
    pop esi
    mov esp, ebp
    pop ebp
    ret

; procedure TButton.Click
global __pas_method_tbutton_click
__pas_method_tbutton_click:
    push ebp
    mov ebp, esp
    mov eax, __pas_unit_VCL_Controls_string_3
    call __pas_unit_VCL_Controls_print_string
    call __pas_unit_VCL_Controls_print_newline
    mov esp, ebp
    pop ebp
    ret

__pas_unit_VCL_Controls_write_cstring:
    push eax
    push eax
    call lstrlenA
    mov edx, eax
    pop eax
    push 0
    push __pas_unit_VCL_Controls_written
    push edx
    push eax
    push dword ptr [__pas_unit_VCL_Controls_stdout_handle]
    call WriteFile
    ret

__pas_unit_VCL_Controls_print_string:
    call __pas_unit_VCL_Controls_write_cstring
    ret

__pas_unit_VCL_Controls_print_newline:
    mov eax, __pas_unit_VCL_Controls_newline
    call __pas_unit_VCL_Controls_write_cstring
    ret

align 4
__pas_unit_VCL_Controls_fmt_s: db 37, 115, 0
__pas_unit_VCL_Controls_fmt_d: db 37, 100, 0
__pas_unit_VCL_Controls_fmt_c: db 37, 99, 0
__pas_unit_VCL_Controls_newline: db 13, 10, 0
__pas_unit_VCL_Controls_clear_sequence: db 27, 91, 50, 74, 27, 91, 72, 0
__pas_unit_VCL_Controls_range_message: db 82, 97, 110, 103, 101, 32, 101, 114, 114, 111, 114, 13, 10, 0

; Pascal-Variablen
__pas_param_tcontrol_create_aparent_0: dd 0 ; intern: integer
__pas_param_tcontrol_create_acontrolid_1: dd 0 ; intern: integer
__pas_result_tcontrol_getwindowclass_result_2: dd 0 ; intern: string
__pas_result_tcontrol_getwindowstyle_result_3: dd 0 ; intern: DWord
__pas_result_tcontrol_getwindowexstyle_result_4: dd 0 ; intern: DWord
__pas_local_tcontrol_createhandle_style_5: dd 0 ; intern: DWord
__pas_param_tcontrol_setbounds_aleft_6: dd 0 ; intern: integer
__pas_param_tcontrol_setbounds_atop_7: dd 0 ; intern: integer
__pas_param_tcontrol_setbounds_awidth_8: dd 0 ; intern: integer
__pas_param_tcontrol_setbounds_aheight_9: dd 0 ; intern: integer
__pas_param_tcontrol_setcaption_acaption_10: dd 0 ; intern: string
__pas_param_tbutton_create_aparent_11: dd 0 ; intern: integer
__pas_param_tbutton_create_acontrolid_12: dd 0 ; intern: integer
__pas_param_tbutton_create_acaption_13: dd 0 ; intern: string
__pas_result_tbutton_getwindowclass_result_14: dd 0 ; intern: string
__pas_result_tbutton_getwindowstyle_result_15: dd 0 ; intern: DWord

; Nullterminierte Windows-Latin-1-Zeichenketten
__pas_unit_VCL_Controls_string_0: db 0
__pas_unit_VCL_Controls_string_1: db 84, 67, 111, 110, 116, 114, 111, 108, 46, 67, 114, 101, 97, 116, 101, 72, 97, 110, 100, 108, 101, 58, 32, 67, 114, 101, 97, 116, 101, 87, 105, 110, 100, 111, 119, 69, 120, 65, 32, 102, 97, 105, 108, 101, 100, 46, 0
__pas_unit_VCL_Controls_string_2: db 66, 85, 84, 84, 79, 78, 0
__pas_unit_VCL_Controls_string_3: db 84, 66, 117, 116, 116, 111, 110, 58, 32, 99, 108, 105, 99, 107, 101, 100, 0
