bits 32

import DBaseQtInitialize, "d64qt5.dll", "DBaseQtInitialize"
import DBaseQtShowWindow, "d64qt5.dll", "DBaseQtShowWindow"
import DBaseQtProcessEvents, "d64qt5.dll", "DBaseQtProcessEvents"
import DBaseQtSetDebugVisible, "d64qt5.dll", "DBaseQtSetDebugVisible"
import DBaseQtAppendConsole, "d64qt5.dll", "DBaseQtAppendConsole"
import DBaseQtAppendDebug, "d64qt5.dll", "DBaseQtAppendDebug"
import DBaseQtMarkProgramFinished, "d64qt5.dll", "DBaseQtMarkProgramFinished"
import DBaseQtExec, "d64qt5.dll", "DBaseQtExec"
import DBaseQtShutdown, "d64qt5.dll", "DBaseQtShutdown"
import __dbase_gcvt, "msvcrt.dll", "_gcvt"
import __dbase_malloc, "msvcrt.dll", "malloc"
import __dbase_memcpy, "msvcrt.dll", "memcpy"
import ExitProcess, "kernel32.dll", "ExitProcess"
global _start
entry _start

section .text

_start:
    push __dbase_text_0
    call DBaseQtInitialize
    add esp, 4
    test eax, eax
    jne __dbase_qt_init_ok_1
    push 1
    call ExitProcess
__dbase_qt_init_ok_1:
    call DBaseQtShowWindow
    call DBaseQtProcessEvents
    push 0
    call DBaseQtSetDebugVisible
    add esp, 4
    fld qword ptr [__dbase_num_0]
    fstp qword ptr [__dbase_var_value1_num]
    mov dword ptr [__dbase_var_value1_type], 1
    push 10
    push __dbase_text_1
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_2
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 6
    push __dbase_text_3
    call DBaseQtAppendConsole
    add esp, 8
    push 40
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    push 9
    push __dbase_text_5
    call DBaseQtAppendConsole
    add esp, 8
    fld qword ptr [__dbase_num_1]
    fstp qword ptr [__dbase_temp_number]
    push __dbase_format_buffer
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, __dbase_format_buffer
    xor edx, edx
__dbase_strlen_loop_2:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_strlen_done_3
    inc ecx
    inc edx
    jmp __dbase_strlen_loop_2
__dbase_strlen_done_3:
    push edx
    push __dbase_format_buffer
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_2
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 7
    push __dbase_text_6
    call DBaseQtAppendConsole
    add esp, 8
    push 11
    push __dbase_text_7
    call DBaseQtAppendConsole
    add esp, 8
    push 1
    push __dbase_text_8
    call DBaseQtAppendConsole
    add esp, 8
    push 8
    push __dbase_text_9
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_2
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 7
    push __dbase_text_10
    call DBaseQtAppendConsole
    add esp, 8
    fld qword ptr [__dbase_num_2]
    fstp qword ptr [__dbase_temp_number]
    push __dbase_format_buffer
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, __dbase_format_buffer
    xor edx, edx
__dbase_strlen_loop_4:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_strlen_done_5
    inc ecx
    inc edx
    jmp __dbase_strlen_loop_4
__dbase_strlen_done_5:
    push edx
    push __dbase_format_buffer
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_2
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 13
    push __dbase_text_11
    call DBaseQtAppendConsole
    add esp, 8
    fld qword ptr [__dbase_var_value1_num]
    fstp qword ptr [__dbase_temp_number]
    push __dbase_format_buffer
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, __dbase_format_buffer
    xor edx, edx
__dbase_strlen_loop_6:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_strlen_done_7
    inc ecx
    inc edx
    jmp __dbase_strlen_loop_6
__dbase_strlen_done_7:
    push edx
    push __dbase_format_buffer
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_2
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    call DBaseQtMarkProgramFinished
    call DBaseQtExec
    mov dword ptr [__dbase_exit_code], eax
    call DBaseQtShutdown
    push dword ptr [__dbase_exit_code]
    call ExitProcess

section .data

__dbase_num_0:
    dd 0, 1076625408
__dbase_num_1:
    dd 0, 1077280768
__dbase_num_2:
    dd 0, 1077542912
__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_text_1:
    db 86, 65, 76, 85, 69, 32, 62, 61, 32, 53
__dbase_text_2:
    db 13, 10
__dbase_text_3:
    db 70, 105, 108, 101, 58, 32
__dbase_text_4:
    db 101, 120, 97, 109, 112, 108, 101, 115, 47, 100, 98, 97, 115, 101, 47, 112, 114, 101, 112, 114, 111, 99, 101, 115
    db 115, 111, 114, 95, 115, 116, 97, 103, 101, 57, 46, 100, 98, 97, 115, 101
__dbase_text_5:
    db 44, 32, 90, 101, 105, 108, 101, 58, 32
__dbase_text_6:
    db 66, 117, 105, 108, 100, 58, 32
__dbase_text_7:
    db 65, 117, 103, 32, 49, 48, 32, 50, 48, 50, 54
__dbase_text_8:
    db 32
__dbase_text_9:
    db 49, 57, 58, 50, 57, 58, 51, 49
__dbase_text_10:
    db 72, 69, 82, 69, 32, 61, 32
__dbase_text_11:
    db 109, 97, 107, 101, 118, 97, 114, 40, 49, 41, 32, 61, 32
__dbase_temp_number:
    dd 0
__dbase_temp_number_hi:
    dd 0
__dbase_call_number:
    dd 0, 0
__dbase_format_buffer:
    db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
__dbase_exit_code:
    dd 0
__dbase_var_value1_type:
    dd 0
__dbase_var_value1_num:
    dd 0, 0
__dbase_var_value1_ptr:
    dd 0
__dbase_var_value1_len:
    dd 0
