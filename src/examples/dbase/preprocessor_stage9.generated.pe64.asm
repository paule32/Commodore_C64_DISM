bits 64

import DBaseQtInitialize, "d64qt5.dll", "DBaseQtInitialize"
import DBaseQtShowWindow, "d64qt5.dll", "DBaseQtShowWindow"
import DBaseQtProcessEvents, "d64qt5.dll", "DBaseQtProcessEvents"
import DBaseQtSetDebugVisible, "d64qt5.dll", "DBaseQtSetDebugVisible"
import DBaseQtAppendConsole, "d64qt5.dll", "DBaseQtAppendConsole"
import DBaseQtAppendDebug, "d64qt5.dll", "DBaseQtAppendDebug"
import DBaseQtSetOutputColor, "d64qt5.dll", "DBaseQtSetOutputColor"
import DBaseQtClearScreen, "d64qt5.dll", "DBaseQtClearScreen"
import DBaseQtClearScreenChar, "d64qt5.dll", "DBaseQtClearScreenChar"
import DBaseQtClearScreenColor, "d64qt5.dll", "DBaseQtClearScreenColor"
import DBaseQtSetBorderColor, "d64qt5.dll", "DBaseQtSetBorderColor"
import DBaseQtMarkProgramFinished, "d64qt5.dll", "DBaseQtMarkProgramFinished"
import DBaseQtExec, "d64qt5.dll", "DBaseQtExec"
import DBaseQtShutdownRequested, "d64qt5.dll", "DBaseQtShutdownRequested"
import DBaseQtShutdown, "d64qt5.dll", "DBaseQtShutdown"
import DBaseQtMenuCreate, "d64qt5.dll", "DBaseQtMenuCreate"
import DBaseQtMenuSetText, "d64qt5.dll", "DBaseQtMenuSetText"
import DBaseQtMenuSetSeparator, "d64qt5.dll", "DBaseQtMenuSetSeparator"
import DBaseQtMenuSetShortcut, "d64qt5.dll", "DBaseQtMenuSetShortcut"
import DBaseQtMenuSetOnClick, "d64qt5.dll", "DBaseQtMenuSetOnClick"
import DBaseQtEnsureDefaultMenu, "d64qt5.dll", "DBaseQtEnsureDefaultMenu"
import DBaseQtSetColorNormal, "d64qt5.dll", "DBaseQtSetColorNormal"
import DBaseQtSessionCreate, "d64qt5.dll", "DBaseQtSessionCreate"
import DBaseQtGetLoginSession, "d64qt5.dll", "DBaseQtGetLoginSession"
import DBaseQtSessionLogin, "d64qt5.dll", "DBaseQtSessionLogin"
import __dbase_gcvt, "msvcrt.dll", "_gcvt"
import __dbase_malloc, "msvcrt.dll", "malloc"
import __dbase_memcpy, "msvcrt.dll", "memcpy"
import __dbase_memcmp, "msvcrt.dll", "memcmp"
import ExitProcess, "kernel32.dll", "ExitProcess"
import VirtualAlloc, "kernel32.dll", "VirtualAlloc"
import VirtualFree, "kernel32.dll", "VirtualFree"
global _start
entry _start

section .text

_start:
    mov rcx, __dbase_text_0
    sub rsp, 40
    call DBaseQtInitialize
    add rsp, 40
    test eax, eax
    jne __dbase_qt_init_ok_2
    mov ecx, 1
    sub rsp, 40
    call ExitProcess
__dbase_qt_init_ok_2:
    xor ecx, ecx
    mov edx, 96
    mov r8d, 12288
    mov r9d, 4
    sub rsp, 40
    call VirtualAlloc
    add rsp, 40
    test rax, rax
    jne __dbase_format_buffer_alloc_ok_3
    sub rsp, 40
    call DBaseQtShutdown
    add rsp, 40
    mov ecx, 1
    sub rsp, 40
    call ExitProcess
__dbase_format_buffer_alloc_ok_3:
    mov qword ptr [__dbase_format_buffer], rax
    mov ecx, 0
    sub rsp, 40
    call DBaseQtSetDebugVisible
    add rsp, 40
    sub rsp, 40
    call DBaseQtEnsureDefaultMenu
    call DBaseQtShowWindow
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    fld qword ptr [__dbase_num_0]
    fstp qword ptr [__dbase_var_value1_num]
    mov dword ptr [__dbase_var_value1_type], 1
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_1
    mov edx, 10
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
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_3
    mov edx, 6
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_4
    mov edx, 67
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_5
    mov edx, 9
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    fld qword ptr [__dbase_num_1]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, qword ptr [__dbase_format_buffer]
    sub rsp, 40
    call __dbase_gcvt
    add rsp, 40
    mov rcx, qword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_strlen_loop_4:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_strlen_done_5
    inc rcx
    inc edx
    jmp __dbase_strlen_loop_4
__dbase_strlen_done_5:
    mov rcx, qword ptr [__dbase_format_buffer]
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
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_6
    mov edx, 7
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_7
    mov edx, 11
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_8
    mov edx, 1
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_9
    mov edx, 8
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
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_10
    mov edx, 7
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    fld qword ptr [__dbase_num_2]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, qword ptr [__dbase_format_buffer]
    sub rsp, 40
    call __dbase_gcvt
    add rsp, 40
    mov rcx, qword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_strlen_loop_6:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_strlen_done_7
    inc rcx
    inc edx
    jmp __dbase_strlen_loop_6
__dbase_strlen_done_7:
    mov rcx, qword ptr [__dbase_format_buffer]
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
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_11
    mov edx, 13
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    fld qword ptr [__dbase_var_value1_num]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, qword ptr [__dbase_format_buffer]
    sub rsp, 40
    call __dbase_gcvt
    add rsp, 40
    mov rcx, qword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_strlen_loop_8:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_strlen_done_9
    inc rcx
    inc edx
    jmp __dbase_strlen_loop_8
__dbase_strlen_done_9:
    mov rcx, qword ptr [__dbase_format_buffer]
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
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    sub rsp, 40
    call DBaseQtMarkProgramFinished
    add rsp, 40
    sub rsp, 40
    call DBaseQtExec
    add rsp, 40
    mov dword ptr [__dbase_exit_code], eax
__dbase_program_cleanup_1:
    sub rsp, 40
    call DBaseQtShutdown
    add rsp, 40
    mov rcx, qword ptr [__dbase_format_buffer]
    test rcx, rcx
    je __dbase_format_buffer_free_done_10
    xor edx, edx
    mov r8d, 32768
    sub rsp, 40
    call VirtualFree
    add rsp, 40
__dbase_format_buffer_free_done_10:
    mov qword ptr [__dbase_format_buffer], 0
    mov ecx, dword ptr [__dbase_exit_code]
    sub rsp, 40
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
    db 47, 109, 110, 116, 47, 100, 97, 116, 97, 47, 115, 116, 97, 103, 101, 50, 57, 95, 119, 111, 114, 107, 47, 115
    db 114, 99, 47, 101, 120, 97, 109, 112, 108, 101, 115, 47, 100, 98, 97, 115, 101, 47, 112, 114, 101, 112, 114, 111
    db 99, 101, 115, 115, 111, 114, 95, 115, 116, 97, 103, 101, 57, 46, 100, 98, 97, 115, 101
__dbase_text_5:
    db 44, 32, 90, 101, 105, 108, 101, 58, 32
__dbase_text_6:
    db 66, 117, 105, 108, 100, 58, 32
__dbase_text_7:
    db 65, 117, 103, 32, 49, 50, 32, 50, 48, 50, 54
__dbase_text_8:
    db 32
__dbase_text_9:
    db 49, 55, 58, 52, 53, 58, 51, 50
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
    dd 0, 0
__dbase_exit_code:
    dd 0
__dbase_var_value1_type:
    dd 0
__dbase_var_value1_num:
    dd 0, 0
__dbase_var_value1_ptr:
    dd 0, 0
__dbase_var_value1_len:
    dd 0
