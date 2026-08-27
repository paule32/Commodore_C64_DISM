; Von Pascal erzeugtes Windows-PE32-Unit-Modul
; Unit: VCL
bits 32
global __unit_VCL
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
extern __pas_method_tform_create
extern __pas_method_tform_destroy
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
extern __pas_method_twindow_create
extern __pas_method_twindow_destroy
extern __pas_method_twindow_dispatchmessage
extern __pas_method_twindow_gethandle
__unit_VCL:
    ret

align 4
__pas_fmt_s: db 37, 115, 0
__pas_fmt_d: db 37, 100, 0
__pas_fmt_c: db 37, 99, 0
__pas_newline: db 13, 10, 0
__pas_clear_sequence: db 27, 91, 50, 74, 27, 91, 72, 0
__pas_range_message: db 82, 97, 110, 103, 101, 32, 101, 114, 114, 111, 114, 13, 10, 0
