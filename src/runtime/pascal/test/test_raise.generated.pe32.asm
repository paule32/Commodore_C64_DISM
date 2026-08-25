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
extern GetConsoleMode
extern SetConsoleMode
extern WriteFile
extern lstrlenA
extern wsprintfA
import _calloc, "msvcrt.dll", "calloc"
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
import _jit_exception_push, "libruntime_mini.dll", "_jit_exception_push"
import _jit_exception_pop, "libruntime_mini.dll", "_jit_exception_pop"
import _jit_setjmp, "libruntime_mini.dll", "_jit_setjmp"
import _jit_read_string, "libruntime_mini.dll", "_jit_read_string"
import _jit_read_int, "libruntime_mini.dll", "_jit_read_int"
import _jit_free, "libruntime_mini.dll", "_jit_free"
_start:
    call __pas_console_init
    mov dword ptr [__pas_exc_frame_2], __pas_exc_env_1
    push __pas_exc_frame_2
    call _jit_exception_push
    add esp, 4
    push __pas_exc_env_1
    call _jit_setjmp
    add esp, 4
    test eax, eax
    jnz __pas_try_handler_3
    mov eax, __pas_string_0
    call __pas_print_string
    call __pas_print_newline
    mov eax, __pas_string_1
    push eax
    push 7
    call _jit_raise
    add esp, 8
    mov eax, __pas_string_2
    call __pas_print_string
    call __pas_print_newline
    call _jit_exception_pop
    jmp __pas_try_end_4
__pas_try_handler_3:
    call _jit_exception_pop
    mov eax, __pas_string_3
    call __pas_print_string
    call __pas_print_newline
__pas_try_end_4:
    mov eax, __pas_string_4
    call __pas_print_string
    call __pas_print_newline
    call _jit_read_string
    push eax
    call _jit_free
    add esp, 4
    push 0
    call ExitProcess

__pas_console_init:
    call AllocConsole
    push -11
    call GetStdHandle
    mov dword ptr [__pas_stdout_handle], eax
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
__pas_stdout_handle: dd 0
__pas_console_rect: dw 0, 0, 79, 24
__pas_console_mode: dd 0
__pas_written: dd 0
__pas_format_buffer: db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
__pas_char_buffer: db 0, 0
__pas_fmt_s: db 37, 115, 0
__pas_fmt_d: db 37, 100, 0
__pas_fmt_c: db 37, 99, 0
__pas_newline: db 13, 10, 0
__pas_clear_sequence: db 27, 91, 50, 74, 27, 91, 72, 0
__pas_range_message: db 82, 97, 110, 103, 101, 32, 101, 114, 114, 111, 114, 13, 10, 0

; Pascal TRY/EXCEPT exception frames (PE32)
__pas_exc_env_1: db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
__pas_exc_frame_2: db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

; Nullterminierte Windows-Latin-1-Zeichenketten
__pas_string_0: db 98, 101, 102, 111, 114, 101, 32, 114, 97, 105, 115, 101, 0
__pas_string_1: db 102, 117, 122, 122, 0
__pas_string_2: db 117, 110, 114, 101, 97, 99, 104, 97, 98, 108, 101, 0
__pas_string_3: db 101, 120, 99, 101, 112, 116, 105, 111, 110, 32, 99, 97, 117, 103, 104, 116, 0
__pas_string_4: db 97, 102, 116, 101, 114, 32, 101, 120, 99, 101, 112, 116, 0
