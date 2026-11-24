%include "RuntimeDB.generated.pe32.extern.inc"
bits 32


section .text


section .data

__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_text_1:
    db 85, 110, 98, 101, 104, 97, 110, 100, 101, 108, 116, 101, 32, 69, 120, 99, 101, 112, 116, 105, 111, 110, 58, 32
__dbase_text_2:
    db 58, 32
__dbase_text_3:
    db 13, 10
__dbase_output_format_screen:
    dd 1
__dbase_output_debug_override:
    dd -1
__dbase_workstation_lazy_console_marker:
    db 68, 54, 52, 68, 66, 65, 83, 69, 95, 76, 65, 90, 89, 95, 67, 79, 78, 83, 79, 76, 69, 95, 86, 49, 0

section .bss

__dbase_ffi_return:
    resq 1
__dbase_temp_number:
    resd 1
__dbase_temp_number_hi:
    resd 1
__dbase_int_cw:
    resw 1
__dbase_int_cw_trunc:
    resw 1
__dbase_call_number:
    resq 1
__dbase_format_buffer:
    resd 1
__dbase_exit_code:
    resd 1
__dbase_output_debug_visible:
    resd 1
__dbase_console_number_len:
    resd 1
