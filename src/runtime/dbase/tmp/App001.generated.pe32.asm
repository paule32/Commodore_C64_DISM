%include "App001.generated.pe32.extern.inc"
bits 32

global _start
entry _start

section .text

_start:
    push __dbase_format_buffer
    push 0
    push 0
    push 0
    push __dbase_text_0
    call DBaseQtRuntimeStartup
    add esp, 20
    test eax, eax
    jne __dbase_qt_init_ok_2
    push 1
    call ExitProcess
__dbase_qt_init_ok_2:
    push 0
    call DBaseQtSetDebugVisible
    add esp, 4
    call DBaseQtEnsureDefaultMenu
    call DBaseQtShowWindow
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    cmp dword ptr [__dbase_output_debug_override], -1
    jne __dbase_output_override_ready_3
    cmp dword ptr [__dbase_output_format_screen], 0
    je __dbase_output_console_4
    jmp __dbase_output_show_done_5
__dbase_output_override_ready_3:
    cmp dword ptr [__dbase_output_debug_override], 0
    je __dbase_output_console_4
__dbase_output_show_done_5:
    cmp dword ptr [__dbase_output_debug_visible], 0
    jne __dbase_output_already_visible_7
    mov dword ptr [__dbase_output_debug_visible], 1
    push 1
    call DBaseQtSetDebugVisible
    add esp, 4
__dbase_output_already_visible_7:
    push 4
    push __dbase_text_1
    call DBaseQtAppendDebug
    add esp, 8
    jmp __dbase_output_done_6
__dbase_output_console_4:
    push 4
    push __dbase_text_1
    call DBaseConsoleWrite
    add esp, 8
__dbase_output_done_6:
    cmp dword ptr [__dbase_output_debug_override], -1
    jne __dbase_output_override_ready_8
    cmp dword ptr [__dbase_output_format_screen], 0
    je __dbase_output_console_9
    jmp __dbase_output_show_done_10
__dbase_output_override_ready_8:
    cmp dword ptr [__dbase_output_debug_override], 0
    je __dbase_output_console_9
__dbase_output_show_done_10:
    cmp dword ptr [__dbase_output_debug_visible], 0
    jne __dbase_output_already_visible_12
    mov dword ptr [__dbase_output_debug_visible], 1
    push 1
    call DBaseQtSetDebugVisible
    add esp, 4
__dbase_output_already_visible_12:
    push 2
    push __dbase_text_2
    call DBaseQtAppendDebug
    add esp, 8
    jmp __dbase_output_done_11
__dbase_output_console_9:
    push 2
    push __dbase_text_2
    call DBaseConsoleWrite
    add esp, 8
__dbase_output_done_11:
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    call DBaseQtMarkProgramFinished
    call DBaseQtExec
    mov dword ptr [__dbase_exit_code], eax
__dbase_program_cleanup_1:
    call DBaseConsoleShutdown
    push __dbase_format_buffer
    call DBaseQtRuntimeShutdown
    add esp, 4
    push dword ptr [__dbase_exit_code]
    call ExitProcess

section .data

__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_text_1:
    db 104, 105, 104, 105
__dbase_text_2:
    db 13, 10
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
__dbase_output_format_screen:
    resd 1
__dbase_output_debug_visible:
    resd 1
__dbase_console_number_len:
    resd 1
