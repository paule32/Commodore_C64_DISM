; Von Pascal erzeugtes Windows-PE32+-AMD64-Unit-Modul
; Unit: System
; Architektur: AMD64 / x86-64 / COFF64
bits 64
global __unit_System
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
__unit_System:
    ret

align 8
__pas_fmt_s: db 37, 115, 0
__pas_fmt_d: db 37, 100, 0
__pas_fmt_c: db 37, 99, 0
__pas_newline: db 13, 10, 0
__pas_clear_sequence: db 27, 91, 50, 74, 27, 91, 72, 0
__pas_range_message: db 82, 97, 110, 103, 101, 32, 101, 114, 114, 111, 114, 13, 10, 0
