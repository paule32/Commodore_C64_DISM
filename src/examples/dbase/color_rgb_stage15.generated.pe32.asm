bits 32

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
    push __dbase_text_0
    call DBaseQtInitialize
    add esp, 4
    test eax, eax
    jne __dbase_qt_init_ok_2
    push 1
    call ExitProcess
__dbase_qt_init_ok_2:
    push 4
    push 12288
    push 96
    push 0
    call VirtualAlloc
    test eax, eax
    jne __dbase_format_buffer_alloc_ok_3
    call DBaseQtShutdown
    push 1
    call ExitProcess
__dbase_format_buffer_alloc_ok_3:
    mov dword ptr [__dbase_format_buffer], eax
    push 0
    call DBaseQtSetDebugVisible
    add esp, 4
    call DBaseQtEnsureDefaultMenu
    call DBaseQtShowWindow
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov eax, __dbase_text_1
    mov dword ptr [__dbase_var_c_ptr], eax
    mov dword ptr [__dbase_var_c_len], 7
    mov dword ptr [__dbase_var_c_type], 2
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push 12
    push __dbase_text_2
    call DBaseQtSetColorNormal
    add esp, 8
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push 24
    push __dbase_text_3
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push 7
    push __dbase_text_1
    call DBaseQtSetColorNormal
    add esp, 8
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push 3
    push __dbase_text_5
    call DBaseQtSetOutputColor
    add esp, 8
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push 39
    push __dbase_text_6
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    call __dbase_function_getwindowcolor__void
    mov eax, dword ptr [__dbase_function_getwindowcolor__void_result_type]
    mov dword ptr [__dbase_app_color_4_type], eax
    mov eax, dword ptr [__dbase_function_getwindowcolor__void_result_num]
    mov dword ptr [__dbase_app_color_4_num], eax
    mov eax, dword ptr [__dbase_function_getwindowcolor__void_result_num+4]
    mov dword ptr [__dbase_app_color_4_num+4], eax
    mov eax, dword ptr [__dbase_function_getwindowcolor__void_result_ptr]
    mov dword ptr [__dbase_app_color_4_ptr], eax
    mov eax, dword ptr [__dbase_function_getwindowcolor__void_result_len]
    mov dword ptr [__dbase_app_color_4_len], eax
    push dword ptr [__dbase_app_color_4_len]
    push dword ptr [__dbase_app_color_4_ptr]
    call DBaseQtSetColorNormal
    add esp, 8
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push 4
    push __dbase_text_7
    call DBaseQtSetOutputColor
    add esp, 8
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push 36
    push __dbase_text_8
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    call DBaseQtMarkProgramFinished
    call DBaseQtExec
    mov dword ptr [__dbase_exit_code], eax
__dbase_program_cleanup_1:
    call DBaseQtShutdown
    mov eax, dword ptr [__dbase_format_buffer]
    test eax, eax
    je __dbase_format_buffer_free_done_5
    push 32768
    push 0
    push eax
    call VirtualFree
__dbase_format_buffer_free_done_5:
    mov dword ptr [__dbase_format_buffer], 0
    push dword ptr [__dbase_exit_code]
    call ExitProcess

__dbase_function_getwindowcolor__void:
    mov eax, __dbase_text_9
    mov dword ptr [__dbase_function_getwindowcolor__void_result_ptr], eax
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
    dd 0
__dbase_exit_code:
    dd 0
__dbase_var_c_type:
    dd 0
__dbase_var_c_num:
    dd 0, 0
__dbase_var_c_ptr:
    dd 0
__dbase_var_c_len:
    dd 0
__dbase_function_getwindowcolor__void_result_type:
    dd 0
__dbase_function_getwindowcolor__void_result_num:
    dd 0, 0
__dbase_function_getwindowcolor__void_result_ptr:
    dd 0
__dbase_function_getwindowcolor__void_result_len:
    dd 0
__dbase_app_color_4_type:
    dd 0
__dbase_app_color_4_num:
    dd 0, 0
__dbase_app_color_4_ptr:
    dd 0
__dbase_app_color_4_len:
    dd 0
