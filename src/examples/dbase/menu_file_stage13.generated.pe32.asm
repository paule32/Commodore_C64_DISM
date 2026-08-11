bits 32

import DBaseQtInitialize, "d64qt5.dll", "DBaseQtInitialize"
import DBaseQtShowWindow, "d64qt5.dll", "DBaseQtShowWindow"
import DBaseQtProcessEvents, "d64qt5.dll", "DBaseQtProcessEvents"
import DBaseQtSetDebugVisible, "d64qt5.dll", "DBaseQtSetDebugVisible"
import DBaseQtAppendConsole, "d64qt5.dll", "DBaseQtAppendConsole"
import DBaseQtAppendDebug, "d64qt5.dll", "DBaseQtAppendDebug"
import DBaseQtSetOutputColor, "d64qt5.dll", "DBaseQtSetOutputColor"
import DBaseQtMarkProgramFinished, "d64qt5.dll", "DBaseQtMarkProgramFinished"
import DBaseQtExec, "d64qt5.dll", "DBaseQtExec"
import DBaseQtShutdown, "d64qt5.dll", "DBaseQtShutdown"
import DBaseQtMenuCreate, "d64qt5.dll", "DBaseQtMenuCreate"
import DBaseQtMenuSetText, "d64qt5.dll", "DBaseQtMenuSetText"
import DBaseQtMenuSetSeparator, "d64qt5.dll", "DBaseQtMenuSetSeparator"
import DBaseQtMenuSetShortcut, "d64qt5.dll", "DBaseQtMenuSetShortcut"
import DBaseQtMenuSetOnClick, "d64qt5.dll", "DBaseQtMenuSetOnClick"
import DBaseQtSetColorNormal, "d64qt5.dll", "DBaseQtSetColorNormal"
import __dbase_gcvt, "msvcrt.dll", "_gcvt"
import __dbase_malloc, "msvcrt.dll", "malloc"
import __dbase_memcpy, "msvcrt.dll", "memcpy"
import __dbase_memcmp, "msvcrt.dll", "memcmp"
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
    push 0
    call DBaseQtSetDebugVisible
    add esp, 4
    call DBaseQtShowWindow
    call DBaseQtProcessEvents
    xor eax, eax
    push eax
    call DBaseQtMenuCreate
    add esp, 4
    mov dword ptr [__dbase_object_app_mfenster], eax
    push 8
    push __dbase_text_1
    push dword ptr [__dbase_object_app_mfenster]
    call DBaseQtMenuSetText
    add esp, 12
    mov eax, dword ptr [__dbase_object_app_mfenster]
    push eax
    call DBaseQtMenuCreate
    add esp, 4
    mov dword ptr [__dbase_object_app_mfenster_mclose], eax
    push __dbase_procedure_mclose_onclick__void
    push dword ptr [__dbase_object_app_mfenster_mclose]
    call DBaseQtMenuSetOnClick
    add esp, 8
    push 10
    push __dbase_text_2
    push dword ptr [__dbase_object_app_mfenster_mclose]
    call DBaseQtMenuSetText
    add esp, 12
    push 7
    push __dbase_text_3
    push dword ptr [__dbase_object_app_mfenster_mclose]
    call DBaseQtMenuSetShortcut
    add esp, 12
    mov eax, __dbase_text_4
    mov dword ptr [__dbase_var_c_ptr], eax
    mov dword ptr [__dbase_var_c_len], 7
    mov dword ptr [__dbase_var_c_type], 2
    push 12
    push __dbase_text_5
    call DBaseQtSetColorNormal
    add esp, 8
    push 24
    push __dbase_text_6
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_7
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 7
    push __dbase_text_4
    call DBaseQtSetColorNormal
    add esp, 8
    push 3
    push __dbase_text_8
    call DBaseQtSetOutputColor
    add esp, 8
    push 39
    push __dbase_text_9
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_7
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    call __dbase_function_getwindowcolor__void
    mov eax, dword ptr [__dbase_function_getwindowcolor__void_result_type]
    mov dword ptr [__dbase_app_color_2_type], eax
    mov eax, dword ptr [__dbase_function_getwindowcolor__void_result_num]
    mov dword ptr [__dbase_app_color_2_num], eax
    mov eax, dword ptr [__dbase_function_getwindowcolor__void_result_num+4]
    mov dword ptr [__dbase_app_color_2_num+4], eax
    mov eax, dword ptr [__dbase_function_getwindowcolor__void_result_ptr]
    mov dword ptr [__dbase_app_color_2_ptr], eax
    mov eax, dword ptr [__dbase_function_getwindowcolor__void_result_len]
    mov dword ptr [__dbase_app_color_2_len], eax
    push dword ptr [__dbase_app_color_2_len]
    push dword ptr [__dbase_app_color_2_ptr]
    call DBaseQtSetColorNormal
    add esp, 8
    push 4
    push __dbase_text_10
    call DBaseQtSetOutputColor
    add esp, 8
    push 36
    push __dbase_text_11
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_7
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 5
    push __dbase_text_12
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_7
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    call DBaseQtMarkProgramFinished
    call DBaseQtExec
    mov dword ptr [__dbase_exit_code], eax
    call DBaseQtShutdown
    push dword ptr [__dbase_exit_code]
    call ExitProcess

__dbase_procedure_mclose_onclick__void:
    push 5
    push __dbase_text_13
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_7
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    jmp __dbase_procedure_mclose_onclick__void_end
__dbase_procedure_mclose_onclick__void_end:
    ret

__dbase_function_getwindowcolor__void:
    mov eax, __dbase_text_14
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
    db 38, 70, 101, 110, 115, 116, 101, 114
__dbase_text_2:
    db 83, 99, 104, 38, 108, 105, 101, 223, 101, 110
__dbase_text_3:
    db 67, 116, 114, 108, 43, 70, 52
__dbase_text_4:
    db 35, 70, 70, 48, 48, 56, 48
__dbase_text_5:
    db 65, 99, 116, 105, 118, 101, 66, 111, 114, 100, 101, 114
__dbase_text_6:
    db 83, 121, 115, 116, 101, 109, 102, 97, 114, 98, 101, 32, 65, 99, 116, 105, 118, 101, 66, 111, 114, 100, 101, 114
__dbase_text_7:
    db 13, 10
__dbase_text_8:
    db 87, 47, 78
__dbase_text_9:
    db 83, 99, 104, 119, 97, 114, 122, 32, 97, 117, 102, 32, 104, 101, 108, 108, 103, 114, 97, 117, 101, 109, 32, 84
    db 101, 120, 116, 45, 72, 105, 110, 116, 101, 114, 103, 114, 117, 110, 100
__dbase_text_10:
    db 78, 47, 87, 43
__dbase_text_11:
    db 87, 101, 105, 115, 115, 32, 97, 117, 102, 32, 115, 99, 104, 119, 97, 114, 122, 101, 109, 32, 84, 101, 120, 116
    db 45, 72, 105, 110, 116, 101, 114, 103, 114, 117, 110, 100
__dbase_text_12:
    db 114, 101, 97, 100, 121
__dbase_text_13:
    db 99, 108, 111, 115, 101
__dbase_text_14:
    db 87, 105, 110, 100, 111, 119
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
__dbase_app_color_2_type:
    dd 0
__dbase_app_color_2_num:
    dd 0, 0
__dbase_app_color_2_ptr:
    dd 0
__dbase_app_color_2_len:
    dd 0
__dbase_object_app_mfenster:
    dd 0
__dbase_object_app_mfenster_mclose:
    dd 0
