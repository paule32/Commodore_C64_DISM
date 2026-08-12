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
    mov rcx, __dbase_text_1
    mov edx, 6
    sub rsp, 40
    call DBaseQtSetColorNormal
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_2
    mov edx, 3
    sub rsp, 40
    call DBaseQtSetOutputColor
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_3
    mov edx, 11
    sub rsp, 40
    call DBaseQtSetBorderColor
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_4
    mov edx, 33
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_5
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
    call DBaseQtClearScreen
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_6
    mov edx, 48
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_5
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
    mov rcx, __dbase_text_7
    mov edx, 7
    sub rsp, 40
    call DBaseQtSetBorderColor
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_8
    mov edx, 16
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_5
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
    mov rcx, __dbase_text_9
    mov edx, 12
    sub rsp, 40
    call DBaseQtSetBorderColor
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_10
    mov edx, 25
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_5
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
    sub rsp, 8
    call __dbase_function_getgreenborder__void
    add rsp, 8
    mov eax, dword ptr [__dbase_function_getgreenborder__void_result_type]
    mov dword ptr [__dbase_var_b_type], eax
    mov eax, dword ptr [__dbase_function_getgreenborder__void_result_num]
    mov dword ptr [__dbase_var_b_num], eax
    mov eax, dword ptr [__dbase_function_getgreenborder__void_result_num+4]
    mov dword ptr [__dbase_var_b_num+4], eax
    mov rax, qword ptr [__dbase_function_getgreenborder__void_result_ptr]
    mov qword ptr [__dbase_var_b_ptr], rax
    mov eax, dword ptr [__dbase_function_getgreenborder__void_result_len]
    mov dword ptr [__dbase_var_b_len], eax
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov eax, dword ptr [__dbase_var_b_type]
    mov dword ptr [__dbase_border_color_4_type], eax
    mov eax, dword ptr [__dbase_var_b_num]
    mov dword ptr [__dbase_border_color_4_num], eax
    mov eax, dword ptr [__dbase_var_b_num+4]
    mov dword ptr [__dbase_border_color_4_num+4], eax
    mov rax, qword ptr [__dbase_var_b_ptr]
    mov qword ptr [__dbase_border_color_4_ptr], rax
    mov eax, dword ptr [__dbase_var_b_len]
    mov dword ptr [__dbase_border_color_4_len], eax
    mov rcx, qword ptr [__dbase_border_color_4_ptr]
    mov edx, dword ptr [__dbase_border_color_4_len]
    sub rsp, 40
    call DBaseQtSetBorderColor
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_11
    mov edx, 26
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_5
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
    je __dbase_format_buffer_free_done_5
    xor edx, edx
    mov r8d, 32768
    sub rsp, 40
    call VirtualFree
    add rsp, 40
__dbase_format_buffer_free_done_5:
    mov qword ptr [__dbase_format_buffer], 0
    mov ecx, dword ptr [__dbase_exit_code]
    sub rsp, 40
    call ExitProcess

__dbase_function_getgreenborder__void:
    mov rax, __dbase_text_12
    mov qword ptr [__dbase_function_getgreenborder__void_result_ptr], rax
    mov dword ptr [__dbase_function_getgreenborder__void_result_len], 7
    mov dword ptr [__dbase_function_getgreenborder__void_result_type], 2
    jmp __dbase_function_getgreenborder__void_end
__dbase_function_getgreenborder__void_end:
    ret

section .data

__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_text_1:
    db 87, 105, 110, 100, 111, 119
__dbase_text_2:
    db 87, 47, 78
__dbase_text_3:
    db 87, 105, 110, 100, 111, 119, 70, 114, 97, 109, 101
__dbase_text_4:
    db 68, 105, 101, 115, 101, 114, 32, 84, 101, 120, 116, 32, 119, 105, 114, 100, 32, 103, 108, 101, 105, 99, 104, 32
    db 103, 101, 108, 111, 101, 115, 99, 104, 116
__dbase_text_5:
    db 13, 10
__dbase_text_6:
    db 67, 76, 69, 65, 82, 32, 83, 67, 82, 69, 69, 78, 58, 32, 115, 99, 104, 119, 97, 114, 122, 32, 97, 117
    db 102, 32, 104, 101, 108, 108, 103, 114, 97, 117, 101, 109, 32, 72, 105, 110, 116, 101, 114, 103, 114, 117, 110, 100
__dbase_text_7:
    db 35, 70, 70, 48, 48, 48, 48
__dbase_text_8:
    db 82, 97, 104, 109, 101, 110, 32, 106, 101, 116, 122, 116, 32, 114, 111, 116
__dbase_text_9:
    db 65, 99, 116, 105, 118, 101, 66, 111, 114, 100, 101, 114
__dbase_text_10:
    db 82, 97, 104, 109, 101, 110, 32, 106, 101, 116, 122, 116, 32, 65, 99, 116, 105, 118, 101, 66, 111, 114, 100, 101
    db 114
__dbase_text_11:
    db 82, 97, 104, 109, 101, 110, 32, 106, 101, 116, 122, 116, 32, 82, 71, 66, 40, 48, 48, 44, 70, 70, 44, 48
    db 48, 41
__dbase_text_12:
    db 35, 48, 48, 70, 70, 48, 48
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
__dbase_var_b_type:
    dd 0
__dbase_var_b_num:
    dd 0, 0
__dbase_var_b_ptr:
    dd 0, 0
__dbase_var_b_len:
    dd 0
__dbase_function_getgreenborder__void_result_type:
    dd 0
__dbase_function_getgreenborder__void_result_num:
    dd 0, 0
__dbase_function_getgreenborder__void_result_ptr:
    dd 0, 0
__dbase_function_getgreenborder__void_result_len:
    dd 0
__dbase_border_color_4_type:
    dd 0
__dbase_border_color_4_num:
    dd 0, 0
__dbase_border_color_4_ptr:
    dd 0, 0
__dbase_border_color_4_len:
    dd 0
