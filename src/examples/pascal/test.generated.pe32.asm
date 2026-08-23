; Von Pascal erzeugter IA-32-Assembler
; Ziel: Windows PE32 / integrierter COFF32-Linker
; Grafikbackend: Direct2D
; Programm: Unbenannt
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
_start:
    call __pas_console_init
    mov eax, __pas_string_0
    call __pas_print_string
    call __pas_print_newline
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

; Nullterminierte Windows-Latin-1-Zeichenketten
__pas_string_0: db 72, 97, 108, 108, 111, 0
