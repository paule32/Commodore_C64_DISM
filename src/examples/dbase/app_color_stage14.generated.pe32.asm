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
    push 12
    push __dbase_text_1
    call DBaseQtSetColorNormal
    add esp, 8
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push 34
    push __dbase_text_2
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_3
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push 74
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_3
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
    je __dbase_format_buffer_free_done_4
    push 32768
    push 0
    push eax
    call VirtualFree
__dbase_format_buffer_free_done_4:
    mov dword ptr [__dbase_format_buffer], 0
    push dword ptr [__dbase_exit_code]
    call ExitProcess

section .data

__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_text_1:
    db 65, 99, 116, 105, 118, 101, 66, 111, 114, 100, 101, 114
__dbase_text_2:
    db 75, 111, 110, 115, 111, 108, 101, 110, 104, 105, 110, 116, 101, 114, 103, 114, 117, 110, 100, 32, 61, 32, 65, 99
    db 116, 105, 118, 101, 66, 111, 114, 100, 101, 114
__dbase_text_3:
    db 13, 10
__dbase_text_4:
    db 68, 105, 101, 32, 70, 97, 114, 98, 101, 32, 119, 105, 114, 100, 32, 122, 117, 114, 32, 76, 97, 117, 102, 122
    db 101, 105, 116, 32, 117, 101, 98, 101, 114, 32, 71, 101, 116, 83, 121, 115, 67, 111, 108, 111, 114, 40, 67, 79
    db 76, 79, 82, 95, 65, 67, 84, 73, 86, 69, 66, 79, 82, 68, 69, 82, 41, 32, 103, 101, 108, 101, 115, 101
    db 110, 46
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
