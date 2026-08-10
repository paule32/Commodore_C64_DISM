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
    fld qword ptr [__dbase_num_1]
    fstp qword ptr [__dbase_var_foobar_num]
    mov dword ptr [__dbase_var_foobar_type], 1
    push 10
    push __dbase_text_1
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_2
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 19
    push __dbase_text_3
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_2
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 13
    push __dbase_text_4
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
    push 16
    push __dbase_text_5
    call DBaseQtAppendConsole
    add esp, 8
    fld qword ptr [__dbase_var_foobar_num]
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
    push 8
    push __dbase_text_6
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
    push 30
    push __dbase_text_7
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
    dd 0, 1075970048
__dbase_num_2:
    dd 0, 1079951360
__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_text_1:
    db 86, 65, 76, 85, 69, 32, 62, 61, 32, 53
__dbase_text_2:
    db 13, 10
__dbase_text_3:
    db 100, 101, 102, 105, 110, 101, 100, 40, 86, 65, 76, 85, 69, 41, 32, 62, 61, 32, 53
__dbase_text_4:
    db 109, 97, 107, 101, 118, 97, 114, 40, 49, 41, 32, 61, 32
__dbase_text_5:
    db 106, 111, 105, 110, 40, 102, 111, 111, 44, 98, 97, 114, 41, 32, 61, 32
__dbase_text_6:
    db 108, 111, 107, 97, 108, 32, 61, 32
__dbase_text_7:
    db 76, 79, 67, 65, 76, 95, 86, 65, 76, 85, 69, 32, 105, 115, 116, 32, 107, 111, 114, 114, 101, 107, 116, 32
    db 115, 99, 111, 112, 101, 100
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
__dbase_var_foobar_type:
    dd 0
__dbase_var_foobar_num:
    dd 0, 0
__dbase_var_foobar_ptr:
    dd 0
__dbase_var_foobar_len:
    dd 0
