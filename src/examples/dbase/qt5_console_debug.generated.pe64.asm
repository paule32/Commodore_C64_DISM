bits 64

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
import ExitProcess, "kernel32.dll", "ExitProcess"
global _start
entry _start

section .text

_start:
    mov rcx, __dbase_text_0
    sub rsp, 40
    call DBaseQtInitialize
    add rsp, 40
    test eax, eax
    jne __dbase_qt_init_ok_1
    mov ecx, 1
    sub rsp, 40
    call ExitProcess
__dbase_qt_init_ok_1:
    sub rsp, 40
    call DBaseQtShowWindow
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    mov ecx, 0
    sub rsp, 40
    call DBaseQtSetDebugVisible
    add rsp, 40
    fld qword ptr [__dbase_num_0]
    fld qword ptr [__dbase_num_1]
    fld qword ptr [__dbase_num_2]
    fmulp
    faddp
    fstp qword ptr [__dbase_var_x_num]
    mov dword ptr [__dbase_var_x_type], 1
    mov rcx, __dbase_text_1
    mov edx, 13
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    fld qword ptr [__dbase_var_x_num]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, __dbase_format_buffer
    sub rsp, 40
    call __dbase_gcvt
    add rsp, 40
    mov rcx, __dbase_format_buffer
    xor edx, edx
__dbase_strlen_loop_2:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_strlen_done_3
    inc rcx
    inc edx
    jmp __dbase_strlen_loop_2
__dbase_strlen_done_3:
    mov rcx, __dbase_format_buffer
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_2
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    mov ecx, 1
    sub rsp, 40
    call DBaseQtSetDebugVisible
    add rsp, 40
    mov rcx, __dbase_text_3
    mov edx, 11
    sub rsp, 40
    call DBaseQtAppendDebug
    add rsp, 40
    fld qword ptr [__dbase_var_x_num]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, __dbase_format_buffer
    sub rsp, 40
    call __dbase_gcvt
    add rsp, 40
    mov rcx, __dbase_format_buffer
    xor edx, edx
__dbase_strlen_loop_4:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_strlen_done_5
    inc rcx
    inc edx
    jmp __dbase_strlen_loop_4
__dbase_strlen_done_5:
    mov rcx, __dbase_format_buffer
    sub rsp, 40
    call DBaseQtAppendDebug
    add rsp, 40
    mov rcx, __dbase_text_2
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendDebug
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    mov rcx, __dbase_text_4
    mov edx, 18
    sub rsp, 40
    call DBaseQtAppendDebug
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    mov ecx, 0
    sub rsp, 40
    call DBaseQtSetDebugVisible
    add rsp, 40
    mov rcx, __dbase_text_5
    mov edx, 14
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_2
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    sub rsp, 40
    call DBaseQtMarkProgramFinished
    add rsp, 40
    sub rsp, 40
    call DBaseQtExec
    add rsp, 40
    mov dword ptr [__dbase_exit_code], eax
    sub rsp, 40
    call DBaseQtShutdown
    add rsp, 40
    mov ecx, dword ptr [__dbase_exit_code]
    sub rsp, 40
    call ExitProcess

section .data

__dbase_num_0:
    dd 0, 1073741824
__dbase_num_1:
    dd 0, 1074266112
__dbase_num_2:
    dd 0, 1074790400
__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_text_1:
    db 87, 101, 114, 116, 32, 118, 111, 110, 32, 88, 32, 61, 32
__dbase_text_2:
    db 13, 10
__dbase_text_3:
    db 68, 69, 66, 85, 71, 58, 32, 88, 32, 61, 32
__dbase_text_4:
    db 68, 69, 66, 85, 71, 32, 111, 104, 110, 101, 32, 78, 101, 119, 76, 105, 110, 101
__dbase_text_5:
    db 87, 105, 101, 100, 101, 114, 32, 75, 111, 110, 115, 111, 108, 101
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
__dbase_var_x_type:
    dd 0
__dbase_var_x_num:
    dd 0, 0
__dbase_var_x_ptr:
    dd 0, 0
__dbase_var_x_len:
    dd 0
