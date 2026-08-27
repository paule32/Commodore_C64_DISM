; Von Pascal erzeugtes Windows-PE32-Unit-Modul
; Unit: Windows.kernel
bits 32
global __unit_Windows_kernel
extern __pas_System_Strings_IntToStr
extern __pas_System_Strings_StrToInt
import _GetModuleHandleA@4, "kernel32.dll", "GetModuleHandleA"
import _ExitProcess@4, "kernel32.dll", "ExitProcess"
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
__unit_Windows_kernel:
    ret

align 4
__pas_unit_Windows_kernel_fmt_s: db 37, 115, 0
__pas_unit_Windows_kernel_fmt_d: db 37, 100, 0
__pas_unit_Windows_kernel_fmt_c: db 37, 99, 0
__pas_unit_Windows_kernel_newline: db 13, 10, 0
__pas_unit_Windows_kernel_clear_sequence: db 27, 91, 50, 74, 27, 91, 72, 0
__pas_unit_Windows_kernel_range_message: db 82, 97, 110, 103, 101, 32, 101, 114, 114, 111, 114, 13, 10, 0
