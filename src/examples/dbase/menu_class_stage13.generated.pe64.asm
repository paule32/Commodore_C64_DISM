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
import DBaseQtMenuCreate, "d64qt5.dll", "DBaseQtMenuCreate"
import DBaseQtMenuSetText, "d64qt5.dll", "DBaseQtMenuSetText"
import DBaseQtMenuSetSeparator, "d64qt5.dll", "DBaseQtMenuSetSeparator"
import DBaseQtMenuSetShortcut, "d64qt5.dll", "DBaseQtMenuSetShortcut"
import DBaseQtMenuSetOnClick, "d64qt5.dll", "DBaseQtMenuSetOnClick"
import __dbase_gcvt, "msvcrt.dll", "_gcvt"
import __dbase_malloc, "msvcrt.dll", "malloc"
import __dbase_memcpy, "msvcrt.dll", "memcpy"
import __dbase_memcmp, "msvcrt.dll", "memcmp"
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
    mov ecx, 0
    sub rsp, 40
    call DBaseQtSetDebugVisible
    add rsp, 40
    sub rsp, 40
    call DBaseQtShowWindow
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    xor rax, rax
    mov rcx, rax
    sub rsp, 40
    call DBaseQtMenuCreate
    add rsp, 40
    mov qword ptr [__dbase_object_app_mfenster], rax
    mov rcx, qword ptr [__dbase_object_app_mfenster]
    mov rdx, __dbase_text_1
    mov r8d, 8
    sub rsp, 40
    call DBaseQtMenuSetText
    add rsp, 40
    mov rax, qword ptr [__dbase_object_app_mfenster]
    mov rcx, rax
    sub rsp, 40
    call DBaseQtMenuCreate
    add rsp, 40
    mov qword ptr [__dbase_object_app_mfenster_mcascade], rax
    mov rcx, qword ptr [__dbase_object_app_mfenster_mcascade]
    mov rdx, __dbase_procedure_mcascade_onclick__void
    sub rsp, 40
    call DBaseQtMenuSetOnClick
    add rsp, 40
    mov rcx, qword ptr [__dbase_object_app_mfenster_mcascade]
    mov rdx, __dbase_text_2
    mov r8d, 12
    sub rsp, 40
    call DBaseQtMenuSetText
    add rsp, 40
    mov rax, qword ptr [__dbase_object_app_mfenster]
    mov rcx, rax
    sub rsp, 40
    call DBaseQtMenuCreate
    add rsp, 40
    mov qword ptr [__dbase_object_app_mfenster_mhorizontal], rax
    mov rcx, qword ptr [__dbase_object_app_mfenster_mhorizontal]
    mov rdx, __dbase_procedure_mhorizontal_onclick__void
    sub rsp, 40
    call DBaseQtMenuSetOnClick
    add rsp, 40
    mov rcx, qword ptr [__dbase_object_app_mfenster_mhorizontal]
    mov rdx, __dbase_text_3
    mov r8d, 20
    sub rsp, 40
    call DBaseQtMenuSetText
    add rsp, 40
    mov rax, qword ptr [__dbase_object_app_mfenster]
    mov rcx, rax
    sub rsp, 40
    call DBaseQtMenuCreate
    add rsp, 40
    mov qword ptr [__dbase_object_app_mfenster_mvertikal], rax
    mov rcx, qword ptr [__dbase_object_app_mfenster_mvertikal]
    mov rdx, __dbase_procedure_mvertikal_onclick__void
    sub rsp, 40
    call DBaseQtMenuSetOnClick
    add rsp, 40
    mov rcx, qword ptr [__dbase_object_app_mfenster_mvertikal]
    mov rdx, __dbase_text_4
    mov r8d, 18
    sub rsp, 40
    call DBaseQtMenuSetText
    add rsp, 40
    mov rax, qword ptr [__dbase_object_app_mfenster]
    mov rcx, rax
    sub rsp, 40
    call DBaseQtMenuCreate
    add rsp, 40
    mov qword ptr [__dbase_object_app_mfenster_msymbole], rax
    mov rcx, qword ptr [__dbase_object_app_mfenster_msymbole]
    mov rdx, __dbase_procedure_msymbole_onclick__void
    sub rsp, 40
    call DBaseQtMenuSetOnClick
    add rsp, 40
    mov rcx, qword ptr [__dbase_object_app_mfenster_msymbole]
    mov rdx, __dbase_text_5
    mov r8d, 17
    sub rsp, 40
    call DBaseQtMenuSetText
    add rsp, 40
    mov rax, qword ptr [__dbase_object_app_mfenster]
    mov rcx, rax
    sub rsp, 40
    call DBaseQtMenuCreate
    add rsp, 40
    mov qword ptr [__dbase_object_app_mfenster_menusep], rax
    mov rcx, qword ptr [__dbase_object_app_mfenster_menusep]
    mov rdx, __dbase_text_6
    mov r8d, 0
    sub rsp, 40
    call DBaseQtMenuSetText
    add rsp, 40
    mov rcx, qword ptr [__dbase_object_app_mfenster_menusep]
    mov edx, 1
    sub rsp, 40
    call DBaseQtMenuSetSeparator
    add rsp, 40
    mov rax, qword ptr [__dbase_object_app_mfenster]
    mov rcx, rax
    sub rsp, 40
    call DBaseQtMenuCreate
    add rsp, 40
    mov qword ptr [__dbase_object_app_mfenster_mclose], rax
    mov rcx, qword ptr [__dbase_object_app_mfenster_mclose]
    mov rdx, __dbase_procedure_mclose_onclick__void
    sub rsp, 40
    call DBaseQtMenuSetOnClick
    add rsp, 40
    mov rcx, qword ptr [__dbase_object_app_mfenster_mclose]
    mov rdx, __dbase_text_7
    mov r8d, 10
    sub rsp, 40
    call DBaseQtMenuSetText
    add rsp, 40
    mov rcx, qword ptr [__dbase_object_app_mfenster_mclose]
    mov rdx, __dbase_text_8
    mov r8d, 7
    sub rsp, 40
    call DBaseQtMenuSetShortcut
    add rsp, 40
    mov rax, qword ptr [__dbase_object_app_mfenster]
    mov rcx, rax
    sub rsp, 40
    call DBaseQtMenuCreate
    add rsp, 40
    mov qword ptr [__dbase_object_app_mfenster_malleschliessen], rax
    mov rcx, qword ptr [__dbase_object_app_mfenster_malleschliessen]
    mov rdx, 0
    sub rsp, 40
    call DBaseQtMenuSetOnClick
    add rsp, 40
    mov rcx, qword ptr [__dbase_object_app_mfenster_malleschliessen]
    mov rdx, __dbase_text_9
    mov r8d, 15
    sub rsp, 40
    call DBaseQtMenuSetText
    add rsp, 40
    mov rcx, __dbase_text_10
    mov edx, 11
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_11
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

__dbase_procedure_mcascade_onclick__void:
    mov rcx, __dbase_text_12
    mov edx, 7
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_11
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    jmp __dbase_procedure_mcascade_onclick__void_end
__dbase_procedure_mcascade_onclick__void_end:
    ret

__dbase_procedure_mhorizontal_onclick__void:
    mov rcx, __dbase_text_13
    mov edx, 10
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_11
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    jmp __dbase_procedure_mhorizontal_onclick__void_end
__dbase_procedure_mhorizontal_onclick__void_end:
    ret

__dbase_procedure_mvertikal_onclick__void:
    mov rcx, __dbase_text_14
    mov edx, 8
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_11
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    jmp __dbase_procedure_mvertikal_onclick__void_end
__dbase_procedure_mvertikal_onclick__void_end:
    ret

__dbase_procedure_msymbole_onclick__void:
    mov rcx, __dbase_text_15
    mov edx, 7
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_11
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    jmp __dbase_procedure_msymbole_onclick__void_end
__dbase_procedure_msymbole_onclick__void_end:
    ret

__dbase_procedure_mclose_onclick__void:
    mov rcx, __dbase_text_16
    mov edx, 5
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_11
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
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
    dd 0, 0
__dbase_object_app_mfenster_mcascade:
    dd 0, 0
__dbase_object_app_mfenster_mhorizontal:
    dd 0, 0
__dbase_object_app_mfenster_mvertikal:
    dd 0, 0
__dbase_object_app_mfenster_msymbole:
    dd 0, 0
__dbase_object_app_mfenster_menusep:
    dd 0, 0
__dbase_object_app_mfenster_mclose:
    dd 0, 0
__dbase_object_app_mfenster_malleschliessen:
    dd 0, 0
