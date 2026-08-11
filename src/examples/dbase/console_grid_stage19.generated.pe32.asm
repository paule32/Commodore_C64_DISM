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
    push 0
    call DBaseQtSetDebugVisible
    add esp, 4
    push 4
    push __dbase_text_1
    call DBaseQtSetOutputColor
    add esp, 8
    push 12
    push __dbase_text_2
    call DBaseQtSetBorderColor
    add esp, 8
    call DBaseQtClearScreen
    push 80
    push __dbase_text_3
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 17
    push __dbase_text_5
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_6
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_7
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_8
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_9
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_10
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_11
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_12
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_13
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_14
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_15
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_16
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_17
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_18
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_19
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_20
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_21
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_22
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_23
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_24
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_25
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_26
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 2
    push __dbase_text_27
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    push 33
    push __dbase_text_28
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    call DBaseQtMarkProgramFinished
    call DBaseQtExec
    mov dword ptr [__dbase_exit_code], eax
    call DBaseQtShutdown
    push dword ptr [__dbase_exit_code]
    call ExitProcess

section .data

__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_text_1:
    db 78, 47, 87, 43
__dbase_text_2:
    db 65, 99, 116, 105, 118, 101, 66, 111, 114, 100, 101, 114
__dbase_text_3:
    db 49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 49, 50, 51, 52
    db 53, 54, 55, 56, 57, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 49, 50, 51, 52, 53, 54, 55, 56
    db 57, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 48, 49, 50
    db 51, 52, 53, 54, 55, 56, 57, 48
__dbase_text_4:
    db 13, 10
__dbase_text_5:
    db 48, 50, 32, 45, 32, 56, 48, 120, 50, 53, 32, 82, 97, 115, 116, 101, 114
__dbase_text_6:
    db 48, 51
__dbase_text_7:
    db 48, 52
__dbase_text_8:
    db 48, 53
__dbase_text_9:
    db 48, 54
__dbase_text_10:
    db 48, 55
__dbase_text_11:
    db 48, 56
__dbase_text_12:
    db 48, 57
__dbase_text_13:
    db 49, 48
__dbase_text_14:
    db 49, 49
__dbase_text_15:
    db 49, 50
__dbase_text_16:
    db 49, 51
__dbase_text_17:
    db 49, 52
__dbase_text_18:
    db 49, 53
__dbase_text_19:
    db 49, 54
__dbase_text_20:
    db 49, 55
__dbase_text_21:
    db 49, 56
__dbase_text_22:
    db 49, 57
__dbase_text_23:
    db 50, 48
__dbase_text_24:
    db 50, 49
__dbase_text_25:
    db 50, 50
__dbase_text_26:
    db 50, 51
__dbase_text_27:
    db 50, 52
__dbase_text_28:
    db 50, 53, 32, 45, 32, 108, 101, 116, 122, 116, 101, 32, 115, 105, 99, 104, 116, 98, 97, 114, 101, 32, 82, 97
    db 115, 116, 101, 114, 122, 101, 105, 108, 101
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
