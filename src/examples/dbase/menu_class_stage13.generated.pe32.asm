bits 32

import DBaseQtInitialize, "d64qt5.dll", "DBaseQtInitialize"
import DBaseQtShowWindow, "d64qt5.dll", "DBaseQtShowWindow"
import DBaseQtProcessEvents, "d64qt5.dll", "DBaseQtProcessEvents"
import DBaseQtSetDebugVisible, "d64qt5.dll", "DBaseQtSetDebugVisible"
import DBaseQtAppendConsole, "d64qt5.dll", "DBaseQtAppendConsole"
import DBaseQtAppendDebug, "d64qt5.dll", "DBaseQtAppendDebug"
import DBaseQtSetOutputColor, "d64qt5.dll", "DBaseQtSetOutputColor"
import DBaseQtClearScreen, "d64qt5.dll", "DBaseQtClearScreen"
import DBaseQtSetBorderColor, "d64qt5.dll", "DBaseQtSetBorderColor"
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
    mov dword ptr [__dbase_object_app_mfenster_mcascade], eax
    push __dbase_procedure_mcascade_onclick__void
    push dword ptr [__dbase_object_app_mfenster_mcascade]
    call DBaseQtMenuSetOnClick
    add esp, 8
    push 12
    push __dbase_text_2
    push dword ptr [__dbase_object_app_mfenster_mcascade]
    call DBaseQtMenuSetText
    add esp, 12
    mov eax, dword ptr [__dbase_object_app_mfenster]
    push eax
    call DBaseQtMenuCreate
    add esp, 4
    mov dword ptr [__dbase_object_app_mfenster_mhorizontal], eax
    push __dbase_procedure_mhorizontal_onclick__void
    push dword ptr [__dbase_object_app_mfenster_mhorizontal]
    call DBaseQtMenuSetOnClick
    add esp, 8
    push 20
    push __dbase_text_3
    push dword ptr [__dbase_object_app_mfenster_mhorizontal]
    call DBaseQtMenuSetText
    add esp, 12
    mov eax, dword ptr [__dbase_object_app_mfenster]
    push eax
    call DBaseQtMenuCreate
    add esp, 4
    mov dword ptr [__dbase_object_app_mfenster_mvertikal], eax
    push __dbase_procedure_mvertikal_onclick__void
    push dword ptr [__dbase_object_app_mfenster_mvertikal]
    call DBaseQtMenuSetOnClick
    add esp, 8
    push 18
    push __dbase_text_4
    push dword ptr [__dbase_object_app_mfenster_mvertikal]
    call DBaseQtMenuSetText
    add esp, 12
    mov eax, dword ptr [__dbase_object_app_mfenster]
    push eax
    call DBaseQtMenuCreate
    add esp, 4
    mov dword ptr [__dbase_object_app_mfenster_msymbole], eax
    push __dbase_procedure_msymbole_onclick__void
    push dword ptr [__dbase_object_app_mfenster_msymbole]
    call DBaseQtMenuSetOnClick
    add esp, 8
    push 17
    push __dbase_text_5
    push dword ptr [__dbase_object_app_mfenster_msymbole]
    call DBaseQtMenuSetText
    add esp, 12
    mov eax, dword ptr [__dbase_object_app_mfenster]
    push eax
    call DBaseQtMenuCreate
    add esp, 4
    mov dword ptr [__dbase_object_app_mfenster_menusep], eax
    push 0
    push __dbase_text_6
    push dword ptr [__dbase_object_app_mfenster_menusep]
    call DBaseQtMenuSetText
    add esp, 12
    push 1
    push dword ptr [__dbase_object_app_mfenster_menusep]
    call DBaseQtMenuSetSeparator
    add esp, 8
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
    push __dbase_text_7
    push dword ptr [__dbase_object_app_mfenster_mclose]
    call DBaseQtMenuSetText
    add esp, 12
    push 7
    push __dbase_text_8
    push dword ptr [__dbase_object_app_mfenster_mclose]
    call DBaseQtMenuSetShortcut
    add esp, 12
    mov eax, dword ptr [__dbase_object_app_mfenster]
    push eax
    call DBaseQtMenuCreate
    add esp, 4
    mov dword ptr [__dbase_object_app_mfenster_malleschliessen], eax
    push 0
    push dword ptr [__dbase_object_app_mfenster_malleschliessen]
    call DBaseQtMenuSetOnClick
    add esp, 8
    push 15
    push __dbase_text_9
    push dword ptr [__dbase_object_app_mfenster_malleschliessen]
    call DBaseQtMenuSetText
    add esp, 12
    push 11
    push __dbase_text_10
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_11
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    call DBaseQtMarkProgramFinished
    call DBaseQtExec
    mov dword ptr [__dbase_exit_code], eax
    call DBaseQtShutdown
    push dword ptr [__dbase_exit_code]
    call ExitProcess

__dbase_procedure_mcascade_onclick__void:
    push 7
    push __dbase_text_12
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_11
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    jmp __dbase_procedure_mcascade_onclick__void_end
__dbase_procedure_mcascade_onclick__void_end:
    ret

__dbase_procedure_mhorizontal_onclick__void:
    push 10
    push __dbase_text_13
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_11
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    jmp __dbase_procedure_mhorizontal_onclick__void_end
__dbase_procedure_mhorizontal_onclick__void_end:
    ret

__dbase_procedure_mvertikal_onclick__void:
    push 8
    push __dbase_text_14
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_11
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    jmp __dbase_procedure_mvertikal_onclick__void_end
__dbase_procedure_mvertikal_onclick__void_end:
    ret

__dbase_procedure_msymbole_onclick__void:
    push 7
    push __dbase_text_15
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_11
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    jmp __dbase_procedure_msymbole_onclick__void_end
__dbase_procedure_msymbole_onclick__void_end:
    ret

__dbase_procedure_mclose_onclick__void:
    push 5
    push __dbase_text_16
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_11
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    jmp __dbase_procedure_mclose_onclick__void_end
__dbase_procedure_mclose_onclick__void_end:
    ret

section .data

__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_text_1:
    db 38, 70, 101, 110, 115, 116, 101, 114
__dbase_text_2:
    db 220, 38, 98, 101, 114, 108, 97, 112, 112, 101, 110, 100
__dbase_text_3:
    db 38, 72, 111, 114, 105, 122, 111, 110, 116, 97, 108, 32, 97, 110, 111, 114, 100, 110, 101, 110
__dbase_text_4:
    db 38, 86, 101, 114, 116, 105, 107, 97, 108, 32, 97, 110, 111, 114, 100, 110, 101, 110
__dbase_text_5:
    db 38, 83, 121, 109, 98, 111, 108, 101, 32, 97, 110, 111, 114, 100, 110, 101, 110
__dbase_text_6:
    db 0
__dbase_text_7:
    db 83, 99, 104, 38, 108, 105, 101, 223, 101, 110
__dbase_text_8:
    db 67, 116, 114, 108, 43, 70, 52
__dbase_text_9:
    db 38, 65, 108, 108, 101, 32, 115, 99, 104, 108, 105, 101, 223, 101, 110
__dbase_text_10:
    db 77, 101, 110, 252, 32, 98, 101, 114, 101, 105, 116
__dbase_text_11:
    db 13, 10
__dbase_text_12:
    db 67, 97, 115, 99, 97, 100, 101
__dbase_text_13:
    db 72, 111, 114, 105, 122, 111, 110, 116, 97, 108
__dbase_text_14:
    db 86, 101, 114, 116, 105, 107, 97, 108
__dbase_text_15:
    db 83, 121, 109, 98, 111, 108, 101
__dbase_text_16:
    db 67, 108, 111, 115, 101
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
__dbase_object_app_mfenster:
    dd 0
__dbase_object_app_mfenster_mcascade:
    dd 0
__dbase_object_app_mfenster_mhorizontal:
    dd 0
__dbase_object_app_mfenster_mvertikal:
    dd 0
__dbase_object_app_mfenster_msymbole:
    dd 0
__dbase_object_app_mfenster_menusep:
    dd 0
__dbase_object_app_mfenster_mclose:
    dd 0
__dbase_object_app_mfenster_malleschliessen:
    dd 0
