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
    fld qword ptr [__dbase_num_0]
    fstp qword ptr [__dbase_var_value1_num]
    mov dword ptr [__dbase_var_value1_type], 1
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push 10
    push __dbase_text_1
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_2
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push 6
    push __dbase_text_3
    call DBaseQtAppendConsole
    add esp, 8
    push 67
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    push 9
    push __dbase_text_5
    call DBaseQtAppendConsole
    add esp, 8
    fld qword ptr [__dbase_num_1]
    fstp qword ptr [__dbase_temp_number]
    push dword ptr [__dbase_format_buffer]
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, dword ptr [__dbase_format_buffer]
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
    push dword ptr [__dbase_format_buffer]
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_2
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
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
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push 7
    push __dbase_text_10
    call DBaseQtAppendConsole
    add esp, 8
    fld qword ptr [__dbase_num_2]
    fstp qword ptr [__dbase_temp_number]
    push dword ptr [__dbase_format_buffer]
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, dword ptr [__dbase_format_buffer]
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
    push dword ptr [__dbase_format_buffer]
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_2
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push 13
    push __dbase_text_11
    call DBaseQtAppendConsole
    add esp, 8
    fld qword ptr [__dbase_var_value1_num]
    fstp qword ptr [__dbase_temp_number]
    push dword ptr [__dbase_format_buffer]
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, dword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_strlen_loop_8:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_strlen_done_9
    inc ecx
    inc edx
    jmp __dbase_strlen_loop_8
__dbase_strlen_done_9:
    push edx
    push dword ptr [__dbase_format_buffer]
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_2
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
    je __dbase_format_buffer_free_done_10
    push 32768
    push 0
    push eax
    call VirtualFree
__dbase_format_buffer_free_done_10:
    mov dword ptr [__dbase_format_buffer], 0
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
    dd 0
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
