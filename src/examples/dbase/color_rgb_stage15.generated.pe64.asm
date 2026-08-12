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
    mov rax, __dbase_text_1
    mov qword ptr [__dbase_var_c_ptr], rax
    mov dword ptr [__dbase_var_c_len], 7
    mov dword ptr [__dbase_var_c_type], 2
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_2
    mov edx, 12
    sub rsp, 40
    call DBaseQtSetColorNormal
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_3
    mov edx, 24
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_4
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
    mov rcx, __dbase_text_1
    mov edx, 7
    sub rsp, 40
    call DBaseQtSetColorNormal
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_5
    mov edx, 3
    sub rsp, 40
    call DBaseQtSetOutputColor
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_6
    mov edx, 39
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_4
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
    call __dbase_function_getwindowcolor__void
    add rsp, 8
    mov eax, dword ptr [__dbase_function_getwindowcolor__void_result_type]
    mov dword ptr [__dbase_app_color_4_type], eax
    mov eax, dword ptr [__dbase_function_getwindowcolor__void_result_num]
    mov dword ptr [__dbase_app_color_4_num], eax
    mov eax, dword ptr [__dbase_function_getwindowcolor__void_result_num+4]
    mov dword ptr [__dbase_app_color_4_num+4], eax
    mov rax, qword ptr [__dbase_function_getwindowcolor__void_result_ptr]
    mov qword ptr [__dbase_app_color_4_ptr], rax
    mov eax, dword ptr [__dbase_function_getwindowcolor__void_result_len]
    mov dword ptr [__dbase_app_color_4_len], eax
    mov rcx, qword ptr [__dbase_app_color_4_ptr]
    mov edx, dword ptr [__dbase_app_color_4_len]
    sub rsp, 40
    call DBaseQtSetColorNormal
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_7
    mov edx, 4
    sub rsp, 40
    call DBaseQtSetOutputColor
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_8
    mov edx, 36
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_4
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

__dbase_function_getwindowcolor__void:
    mov rax, __dbase_text_9
    mov qword ptr [__dbase_function_getwindowcolor__void_result_ptr], rax
    mov dword ptr [__dbase_function_getwindowcolor__void_result_len], 6
    mov dword ptr [__dbase_function_getwindowcolor__void_result_type], 2
    jmp __dbase_function_getwindowcolor__void_end
__dbase_function_getwindowcolor__void_end:
    ret

section .data

__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_text_1:
    db 35, 70, 70, 48, 48, 56, 48
__dbase_text_2:
    db 65, 99, 116, 105, 118, 101, 66, 111, 114, 100, 101, 114
__dbase_text_3:
    db 83, 121, 115, 116, 101, 109, 102, 97, 114, 98, 101, 32, 65, 99, 116, 105, 118, 101, 66, 111, 114, 100, 101, 114
__dbase_text_4:
    db 13, 10
__dbase_text_5:
    db 87, 47, 78
__dbase_text_6:
    db 83, 99, 104, 119, 97, 114, 122, 32, 97, 117, 102, 32, 104, 101, 108, 108, 103, 114, 97, 117, 101, 109, 32, 84
    db 101, 120, 116, 45, 72, 105, 110, 116, 101, 114, 103, 114, 117, 110, 100
__dbase_text_7:
    db 78, 47, 87, 43
__dbase_text_8:
    db 87, 101, 105, 115, 115, 32, 97, 117, 102, 32, 115, 99, 104, 119, 97, 114, 122, 101, 109, 32, 84, 101, 120, 116
    db 45, 72, 105, 110, 116, 101, 114, 103, 114, 117, 110, 100
__dbase_text_9:
    db 87, 105, 110, 100, 111, 119
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
__dbase_var_c_type:
    dd 0
__dbase_var_c_num:
    dd 0, 0
__dbase_var_c_ptr:
    dd 0, 0
__dbase_var_c_len:
    dd 0
__dbase_function_getwindowcolor__void_result_type:
    dd 0
__dbase_function_getwindowcolor__void_result_num:
    dd 0, 0
__dbase_function_getwindowcolor__void_result_ptr:
    dd 0, 0
__dbase_function_getwindowcolor__void_result_len:
    dd 0
__dbase_app_color_4_type:
    dd 0
__dbase_app_color_4_num:
    dd 0, 0
__dbase_app_color_4_ptr:
    dd 0, 0
__dbase_app_color_4_len:
    dd 0
