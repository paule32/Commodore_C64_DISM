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
import DBaseQtDatabaseCreate, "d64qt5.dll", "DBaseQtDatabaseCreate"
import DBaseQtDatabaseSetPath, "d64qt5.dll", "DBaseQtDatabaseSetPath"
import DBaseQtDatabaseSetDatabaseName, "d64qt5.dll", "DBaseQtDatabaseSetDatabaseName"
import DBaseQtDatabaseSetUserName, "d64qt5.dll", "DBaseQtDatabaseSetUserName"
import DBaseQtDatabaseSetPassword, "d64qt5.dll", "DBaseQtDatabaseSetPassword"
import DBaseQtDatabaseSetAlias, "d64qt5.dll", "DBaseQtDatabaseSetAlias"
import DBaseQtDatabaseSetSession, "d64qt5.dll", "DBaseQtDatabaseSetSession"
import DBaseQtDatabaseSetActive, "d64qt5.dll", "DBaseQtDatabaseSetActive"
import DBaseQtDatabaseOpen, "d64qt5.dll", "DBaseQtDatabaseOpen"
import DBaseQtDatabaseClose, "d64qt5.dll", "DBaseQtDatabaseClose"
import DBaseQtDatabaseCommit, "d64qt5.dll", "DBaseQtDatabaseCommit"
import __dbase_gcvt, "msvcrt.dll", "_gcvt"
import __dbase_malloc, "msvcrt.dll", "malloc"
import __dbase_memcpy, "msvcrt.dll", "memcpy"
import __dbase_memcmp, "msvcrt.dll", "memcmp"
import ExitProcess, "kernel32.dll", "ExitProcess"
import VirtualAlloc, "kernel32.dll", "VirtualAlloc"
import VirtualFree, "kernel32.dll", "VirtualFree"
import DBaseQtInitializeGui, "libd64_qt5.dll", "DBaseQtInitializeGui"
import DBaseQtExec, "libd64_qt5.dll", "DBaseQtExec"
import DBaseQtShutdown, "libd64_qt5.dll", "DBaseQtShutdown"
import DBaseQtFormCreate, "libd64_qt5.dll", "DBaseQtFormCreate"
import DBaseQtControlCreateEx, "libd64_qt5.dll", "DBaseQtControlCreateEx"
import DBaseQtWidgetSetGeometry, "libd64_qt5.dll", "DBaseQtWidgetSetGeometry"
import DBaseQtWidgetSetText, "libd64_qt5.dll", "DBaseQtWidgetSetText"
import DBaseQtWidgetSetProperty, "libd64_qt5.dll", "DBaseQtWidgetSetProperty"
import DBaseQtWidgetSetFont, "libd64_qt5.dll", "DBaseQtWidgetSetFont"
import DBaseQtObjectBindEvent, "libd64_qt5.dll", "DBaseQtObjectBindEvent"
import DBaseQtTimerCreate, "libd64_qt5.dll", "DBaseQtTimerCreate"
import DBaseQtTimerSetInterval, "libd64_qt5.dll", "DBaseQtTimerSetInterval"
import DBaseQtTimerSetActive, "libd64_qt5.dll", "DBaseQtTimerSetActive"
import DBaseQtConsoleWrite, "libd64_qt5.dll", "DBaseQtConsoleWrite"
import DBaseQtFormOpen, "libd64_qt5.dll", "DBaseQtFormOpen"
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
    db 0
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

; Stage 127: eigener WFM-GUI-Programmeinstieg
.section .text
.entry __d64_wfm_entry
__d64_wfm_entry:
    push __dbase_wfm_text_143
    call DBaseQtInitializeGui
    add esp, 4
    push 5
    push __dbase_wfm_text_0
    call DBaseQtFormCreate
    add esp, 8
    mov dword ptr [__dbase_wfm_form], eax
    push 480
    push 640
    push 20
    push 10
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetGeometry
    add esp, 20
    push 1
    push 0
    push 0
    push 1
    push 12
    push 8
    push __dbase_wfm_text_1
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetFont
    add esp, 32
    push 4
    push __dbase_wfm_text_3
    push 4
    push __dbase_wfm_text_2
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 5
    push __dbase_wfm_text_5
    push 4
    push __dbase_wfm_text_4
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 9
    push __dbase_wfm_text_7
    push 9
    push __dbase_wfm_text_6
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_9
    push 9
    push __dbase_wfm_text_8
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 17
    push __dbase_wfm_text_11
    push 13
    push __dbase_wfm_text_10
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_13
    push 10
    push __dbase_wfm_text_12
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 2
    push __dbase_wfm_text_15
    push 13
    push __dbase_wfm_text_14
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 2
    push __dbase_wfm_text_17
    push 14
    push __dbase_wfm_text_16
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 5
    push __dbase_wfm_text_19
    push 11
    push __dbase_wfm_text_18
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_21
    push 11
    push __dbase_wfm_text_20
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_23
    push 11
    push __dbase_wfm_text_22
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_25
    push 11
    push __dbase_wfm_text_24
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_27
    push 15
    push __dbase_wfm_text_26
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_29
    push 15
    push __dbase_wfm_text_28
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_31
    push 15
    push __dbase_wfm_text_30
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_33
    push 15
    push __dbase_wfm_text_32
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 3
    push __dbase_wfm_text_35
    push 10
    push __dbase_wfm_text_34
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 6
    push __dbase_wfm_text_37
    push 15
    push __dbase_wfm_text_36
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_39
    push 14
    push __dbase_wfm_text_38
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_41
    push 15
    push __dbase_wfm_text_40
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 3
    push __dbase_wfm_text_43
    push 9
    push __dbase_wfm_text_42
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 5
    push __dbase_wfm_text_45
    push 14
    push __dbase_wfm_text_44
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_47
    push 13
    push __dbase_wfm_text_46
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_49
    push 14
    push __dbase_wfm_text_48
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 3
    push __dbase_wfm_text_51
    push 11
    push __dbase_wfm_text_50
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 5
    push __dbase_wfm_text_53
    push 16
    push __dbase_wfm_text_52
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_55
    push 15
    push __dbase_wfm_text_54
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_57
    push 16
    push __dbase_wfm_text_56
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 3
    push __dbase_wfm_text_59
    push 12
    push __dbase_wfm_text_58
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 5
    push __dbase_wfm_text_61
    push 17
    push __dbase_wfm_text_60
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_63
    push 16
    push __dbase_wfm_text_62
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_65
    push 17
    push __dbase_wfm_text_64
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 3
    push __dbase_wfm_text_67
    push 9
    push __dbase_wfm_text_66
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_69
    push 14
    push __dbase_wfm_text_68
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_71
    push 14
    push __dbase_wfm_text_70
    push dword ptr [__dbase_wfm_form]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_73
    push dword ptr [__dbase_wfm_form]
    push 10
    push __dbase_wfm_text_72
    call DBaseQtControlCreateEx
    add esp, 20
    mov dword ptr [__dbase_wfm_obj_THIS_PushButton1], eax
    push 85
    push 174
    push 40
    push 30
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetGeometry
    add esp, 20
    push 1
    push 0
    push 0
    push 1
    push 9
    push 5
    push __dbase_wfm_text_74
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetFont
    add esp, 32
    push 11
    push __dbase_wfm_text_76
    push 4
    push __dbase_wfm_text_75
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_78
    push 9
    push __dbase_wfm_text_77
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_80
    push 9
    push __dbase_wfm_text_79
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 4
    push __dbase_wfm_text_82
    push 13
    push __dbase_wfm_text_81
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_84
    push 10
    push __dbase_wfm_text_83
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 2
    push __dbase_wfm_text_86
    push 13
    push __dbase_wfm_text_85
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 2
    push __dbase_wfm_text_88
    push 14
    push __dbase_wfm_text_87
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 6
    push __dbase_wfm_text_90
    push 11
    push __dbase_wfm_text_89
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_92
    push 11
    push __dbase_wfm_text_91
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_94
    push 11
    push __dbase_wfm_text_93
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_96
    push 11
    push __dbase_wfm_text_95
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_98
    push 15
    push __dbase_wfm_text_97
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_100
    push 15
    push __dbase_wfm_text_99
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_102
    push 15
    push __dbase_wfm_text_101
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_104
    push 15
    push __dbase_wfm_text_103
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 3
    push __dbase_wfm_text_106
    push 10
    push __dbase_wfm_text_105
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 6
    push __dbase_wfm_text_108
    push 15
    push __dbase_wfm_text_107
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_110
    push 14
    push __dbase_wfm_text_109
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_112
    push 15
    push __dbase_wfm_text_111
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 3
    push __dbase_wfm_text_114
    push 9
    push __dbase_wfm_text_113
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 6
    push __dbase_wfm_text_116
    push 14
    push __dbase_wfm_text_115
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_118
    push 13
    push __dbase_wfm_text_117
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_120
    push 14
    push __dbase_wfm_text_119
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 3
    push __dbase_wfm_text_122
    push 11
    push __dbase_wfm_text_121
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 6
    push __dbase_wfm_text_124
    push 16
    push __dbase_wfm_text_123
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_126
    push 15
    push __dbase_wfm_text_125
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_128
    push 16
    push __dbase_wfm_text_127
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 3
    push __dbase_wfm_text_130
    push 12
    push __dbase_wfm_text_129
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 6
    push __dbase_wfm_text_132
    push 17
    push __dbase_wfm_text_131
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 1
    push __dbase_wfm_text_134
    push 16
    push __dbase_wfm_text_133
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_136
    push 17
    push __dbase_wfm_text_135
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 3
    push __dbase_wfm_text_138
    push 9
    push __dbase_wfm_text_137
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_140
    push 14
    push __dbase_wfm_text_139
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push 7
    push __dbase_wfm_text_142
    push 14
    push __dbase_wfm_text_141
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetProperty
    add esp, 20
    push dword ptr [__dbase_wfm_form]
    call DBaseQtFormOpen
    add esp, 4
    call __dbase_wfm_proc___init__
    call __dbase_wfm_proc___main__
    call DBaseQtExec
    call __dbase_wfm_proc___del__
    call DBaseQtShutdown
    xor eax, eax
    ret

; Stage 133: WFM Event-/Methoden-Code
.section .text

; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: __del__
; ------------------------------------------------------------
__dbase_wfm_proc___del__:
    ret
; END WFM PROCEDURE/FUNCTION: __del__


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: __init__
; ------------------------------------------------------------
__dbase_wfm_proc___init__:
    ret
; END WFM PROCEDURE/FUNCTION: __init__


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: __main__
; ------------------------------------------------------------
__dbase_wfm_proc___main__:
    mov eax, 7
    ret
; END WFM PROCEDURE/FUNCTION: __main__

; Stage 127 WFM object handles / data
.section .data
__dbase_wfm_form:
    dd 0
__dbase_wfm_obj_THIS_PushButton1:
    dd 0
__dbase_wfm_text_0:
    db 70, 111, 114, 109, 49, 92, 48
__dbase_wfm_text_1:
    db 67, 111, 110, 115, 111, 108, 97, 115, 92, 48
__dbase_wfm_text_2:
    db 84, 101, 120, 116, 92, 48
__dbase_wfm_text_3:
    db 68, 101, 109, 111, 92, 48
__dbase_wfm_text_4:
    db 78, 97, 109, 101, 92, 48
__dbase_wfm_text_5:
    db 70, 111, 114, 109, 49, 92, 48
__dbase_wfm_text_6:
    db 66, 97, 99, 107, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_7:
    db 35, 56, 48, 48, 97, 49, 52, 49, 101, 92, 48
__dbase_wfm_text_8:
    db 70, 111, 114, 101, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_9:
    db 35, 102, 102, 102, 102, 102, 102, 92, 48
__dbase_wfm_text_10:
    db 66, 114, 117, 115, 104, 71, 114, 97, 100, 105, 101, 110, 116, 92, 48
__dbase_wfm_text_11:
    db 108, 105, 110, 101, 97, 114, 95, 104, 111, 114, 105, 122, 111, 110, 116, 97, 108, 92, 48
__dbase_wfm_text_12:
    db 66, 114, 117, 115, 104, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_13:
    db 55, 92, 48
__dbase_wfm_text_14:
    db 66, 114, 117, 115, 104, 67, 117, 116, 87, 105, 100, 116, 104, 92, 48
__dbase_wfm_text_15:
    db 54, 53, 92, 48
__dbase_wfm_text_16:
    db 66, 114, 117, 115, 104, 67, 117, 116, 72, 101, 105, 103, 104, 116, 92, 48
__dbase_wfm_text_17:
    db 52, 53, 92, 48
__dbase_wfm_text_18:
    db 66, 111, 114, 100, 101, 114, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_19:
    db 115, 111, 108, 105, 100, 92, 48
__dbase_wfm_text_20:
    db 66, 111, 114, 100, 101, 114, 87, 105, 100, 116, 104, 92, 48
__dbase_wfm_text_21:
    db 50, 92, 48
__dbase_wfm_text_22:
    db 66, 111, 114, 100, 101, 114, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_23:
    db 35, 56, 48, 56, 48, 56, 48, 92, 48
__dbase_wfm_text_24:
    db 83, 104, 97, 100, 111, 119, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_25:
    db 35, 49, 48, 49, 48, 49, 48, 92, 48
__dbase_wfm_text_26:
    db 66, 111, 114, 100, 101, 114, 82, 111, 117, 110, 100, 101, 100, 84, 76, 92, 48
__dbase_wfm_text_27:
    db 49, 92, 48
__dbase_wfm_text_28:
    db 66, 111, 114, 100, 101, 114, 82, 111, 117, 110, 100, 101, 100, 84, 82, 92, 48
__dbase_wfm_text_29:
    db 50, 92, 48
__dbase_wfm_text_30:
    db 66, 111, 114, 100, 101, 114, 82, 111, 117, 110, 100, 101, 100, 66, 76, 92, 48
__dbase_wfm_text_31:
    db 51, 92, 48
__dbase_wfm_text_32:
    db 66, 111, 114, 100, 101, 114, 82, 111, 117, 110, 100, 101, 100, 66, 82, 92, 48
__dbase_wfm_text_33:
    db 52, 92, 48
__dbase_wfm_text_34:
    db 66, 111, 114, 100, 101, 114, 76, 101, 102, 116, 92, 48
__dbase_wfm_text_35:
    db 46, 84, 46, 92, 48
__dbase_wfm_text_36:
    db 66, 111, 114, 100, 101, 114, 76, 101, 102, 116, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_37:
    db 100, 111, 117, 98, 108, 101, 92, 48
__dbase_wfm_text_38:
    db 66, 111, 114, 100, 101, 114, 76, 101, 102, 116, 83, 105, 122, 101, 92, 48
__dbase_wfm_text_39:
    db 51, 92, 48
__dbase_wfm_text_40:
    db 66, 111, 114, 100, 101, 114, 76, 101, 102, 116, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_41:
    db 35, 102, 102, 48, 48, 48, 48, 92, 48
__dbase_wfm_text_42:
    db 66, 111, 114, 100, 101, 114, 84, 111, 112, 92, 48
__dbase_wfm_text_43:
    db 46, 84, 46, 92, 48
__dbase_wfm_text_44:
    db 66, 111, 114, 100, 101, 114, 84, 111, 112, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_45:
    db 115, 111, 108, 105, 100, 92, 48
__dbase_wfm_text_46:
    db 66, 111, 114, 100, 101, 114, 84, 111, 112, 83, 105, 122, 101, 92, 48
__dbase_wfm_text_47:
    db 50, 92, 48
__dbase_wfm_text_48:
    db 66, 111, 114, 100, 101, 114, 84, 111, 112, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_49:
    db 35, 56, 48, 56, 48, 56, 48, 92, 48
__dbase_wfm_text_50:
    db 66, 111, 114, 100, 101, 114, 82, 105, 103, 104, 116, 92, 48
__dbase_wfm_text_51:
    db 46, 84, 46, 92, 48
__dbase_wfm_text_52:
    db 66, 111, 114, 100, 101, 114, 82, 105, 103, 104, 116, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_53:
    db 115, 111, 108, 105, 100, 92, 48
__dbase_wfm_text_54:
    db 66, 111, 114, 100, 101, 114, 82, 105, 103, 104, 116, 83, 105, 122, 101, 92, 48
__dbase_wfm_text_55:
    db 50, 92, 48
__dbase_wfm_text_56:
    db 66, 111, 114, 100, 101, 114, 82, 105, 103, 104, 116, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_57:
    db 35, 56, 48, 56, 48, 56, 48, 92, 48
__dbase_wfm_text_58:
    db 66, 111, 114, 100, 101, 114, 66, 111, 116, 116, 111, 109, 92, 48
__dbase_wfm_text_59:
    db 46, 84, 46, 92, 48
__dbase_wfm_text_60:
    db 66, 111, 114, 100, 101, 114, 66, 111, 116, 116, 111, 109, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_61:
    db 115, 111, 108, 105, 100, 92, 48
__dbase_wfm_text_62:
    db 66, 111, 114, 100, 101, 114, 66, 111, 116, 116, 111, 109, 83, 105, 122, 101, 92, 48
__dbase_wfm_text_63:
    db 50, 92, 48
__dbase_wfm_text_64:
    db 66, 111, 114, 100, 101, 114, 66, 111, 116, 116, 111, 109, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_65:
    db 35, 56, 48, 56, 48, 56, 48, 92, 48
__dbase_wfm_text_66:
    db 70, 111, 110, 116, 65, 108, 112, 104, 97, 92, 48
__dbase_wfm_text_67:
    db 50, 48, 48, 92, 48
__dbase_wfm_text_68:
    db 70, 111, 110, 116, 66, 97, 99, 107, 103, 114, 111, 117, 110, 100, 92, 48
__dbase_wfm_text_69:
    db 35, 50, 48, 50, 48, 50, 48, 92, 48
__dbase_wfm_text_70:
    db 70, 111, 110, 116, 70, 111, 114, 101, 103, 114, 111, 117, 110, 100, 92, 48
__dbase_wfm_text_71:
    db 35, 101, 101, 101, 101, 101, 101, 92, 48
__dbase_wfm_text_72:
    db 80, 85, 83, 72, 66, 85, 84, 84, 79, 78, 92, 48
__dbase_wfm_text_73:
    db 66, 117, 116, 116, 111, 110, 49, 92, 48
__dbase_wfm_text_74:
    db 65, 114, 105, 97, 108, 92, 48
__dbase_wfm_text_75:
    db 78, 97, 109, 101, 92, 48
__dbase_wfm_text_76:
    db 80, 117, 115, 104, 66, 117, 116, 116, 111, 110, 49, 92, 48
__dbase_wfm_text_77:
    db 66, 97, 99, 107, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_78:
    db 35, 51, 51, 51, 51, 51, 51, 92, 48
__dbase_wfm_text_79:
    db 70, 111, 114, 101, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_80:
    db 35, 101, 98, 101, 101, 102, 50, 92, 48
__dbase_wfm_text_81:
    db 66, 114, 117, 115, 104, 71, 114, 97, 100, 105, 101, 110, 116, 92, 48
__dbase_wfm_text_82:
    db 110, 111, 110, 101, 92, 48
__dbase_wfm_text_83:
    db 66, 114, 117, 115, 104, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_84:
    db 48, 92, 48
__dbase_wfm_text_85:
    db 66, 114, 117, 115, 104, 67, 117, 116, 87, 105, 100, 116, 104, 92, 48
__dbase_wfm_text_86:
    db 56, 48, 92, 48
__dbase_wfm_text_87:
    db 66, 114, 117, 115, 104, 67, 117, 116, 72, 101, 105, 103, 104, 116, 92, 48
__dbase_wfm_text_88:
    db 57, 48, 92, 48
__dbase_wfm_text_89:
    db 66, 111, 114, 100, 101, 114, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_90:
    db 100, 97, 115, 104, 101, 100, 92, 48
__dbase_wfm_text_91:
    db 66, 111, 114, 100, 101, 114, 87, 105, 100, 116, 104, 92, 48
__dbase_wfm_text_92:
    db 52, 92, 48
__dbase_wfm_text_93:
    db 66, 111, 114, 100, 101, 114, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_94:
    db 35, 53, 53, 102, 102, 55, 102, 92, 48
__dbase_wfm_text_95:
    db 83, 104, 97, 100, 111, 119, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_96:
    db 35, 48, 48, 48, 48, 48, 48, 92, 48
__dbase_wfm_text_97:
    db 66, 111, 114, 100, 101, 114, 82, 111, 117, 110, 100, 101, 100, 84, 76, 92, 48
__dbase_wfm_text_98:
    db 48, 92, 48
__dbase_wfm_text_99:
    db 66, 111, 114, 100, 101, 114, 82, 111, 117, 110, 100, 101, 100, 84, 82, 92, 48
__dbase_wfm_text_100:
    db 48, 92, 48
__dbase_wfm_text_101:
    db 66, 111, 114, 100, 101, 114, 82, 111, 117, 110, 100, 101, 100, 66, 76, 92, 48
__dbase_wfm_text_102:
    db 48, 92, 48
__dbase_wfm_text_103:
    db 66, 111, 114, 100, 101, 114, 82, 111, 117, 110, 100, 101, 100, 66, 82, 92, 48
__dbase_wfm_text_104:
    db 48, 92, 48
__dbase_wfm_text_105:
    db 66, 111, 114, 100, 101, 114, 76, 101, 102, 116, 92, 48
__dbase_wfm_text_106:
    db 46, 84, 46, 92, 48
__dbase_wfm_text_107:
    db 66, 111, 114, 100, 101, 114, 76, 101, 102, 116, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_108:
    db 100, 97, 115, 104, 101, 100, 92, 48
__dbase_wfm_text_109:
    db 66, 111, 114, 100, 101, 114, 76, 101, 102, 116, 83, 105, 122, 101, 92, 48
__dbase_wfm_text_110:
    db 52, 92, 48
__dbase_wfm_text_111:
    db 66, 111, 114, 100, 101, 114, 76, 101, 102, 116, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_112:
    db 35, 53, 53, 102, 102, 55, 102, 92, 48
__dbase_wfm_text_113:
    db 66, 111, 114, 100, 101, 114, 84, 111, 112, 92, 48
__dbase_wfm_text_114:
    db 46, 84, 46, 92, 48
__dbase_wfm_text_115:
    db 66, 111, 114, 100, 101, 114, 84, 111, 112, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_116:
    db 100, 97, 115, 104, 101, 100, 92, 48
__dbase_wfm_text_117:
    db 66, 111, 114, 100, 101, 114, 84, 111, 112, 83, 105, 122, 101, 92, 48
__dbase_wfm_text_118:
    db 52, 92, 48
__dbase_wfm_text_119:
    db 66, 111, 114, 100, 101, 114, 84, 111, 112, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_120:
    db 35, 53, 53, 102, 102, 55, 102, 92, 48
__dbase_wfm_text_121:
    db 66, 111, 114, 100, 101, 114, 82, 105, 103, 104, 116, 92, 48
__dbase_wfm_text_122:
    db 46, 70, 46, 92, 48
__dbase_wfm_text_123:
    db 66, 111, 114, 100, 101, 114, 82, 105, 103, 104, 116, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_124:
    db 100, 111, 116, 116, 101, 100, 92, 48
__dbase_wfm_text_125:
    db 66, 111, 114, 100, 101, 114, 82, 105, 103, 104, 116, 83, 105, 122, 101, 92, 48
__dbase_wfm_text_126:
    db 52, 92, 48
__dbase_wfm_text_127:
    db 66, 111, 114, 100, 101, 114, 82, 105, 103, 104, 116, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_128:
    db 35, 53, 53, 102, 102, 55, 102, 92, 48
__dbase_wfm_text_129:
    db 66, 111, 114, 100, 101, 114, 66, 111, 116, 116, 111, 109, 92, 48
__dbase_wfm_text_130:
    db 46, 84, 46, 92, 48
__dbase_wfm_text_131:
    db 66, 111, 114, 100, 101, 114, 66, 111, 116, 116, 111, 109, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_132:
    db 100, 97, 115, 104, 101, 100, 92, 48
__dbase_wfm_text_133:
    db 66, 111, 114, 100, 101, 114, 66, 111, 116, 116, 111, 109, 83, 105, 122, 101, 92, 48
__dbase_wfm_text_134:
    db 52, 92, 48
__dbase_wfm_text_135:
    db 66, 111, 114, 100, 101, 114, 66, 111, 116, 116, 111, 109, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_136:
    db 35, 53, 53, 102, 102, 55, 102, 92, 48
__dbase_wfm_text_137:
    db 70, 111, 110, 116, 65, 108, 112, 104, 97, 92, 48
__dbase_wfm_text_138:
    db 49, 50, 51, 92, 48
__dbase_wfm_text_139:
    db 70, 111, 110, 116, 66, 97, 99, 107, 103, 114, 111, 117, 110, 100, 92, 48
__dbase_wfm_text_140:
    db 35, 49, 49, 49, 49, 49, 49, 92, 48
__dbase_wfm_text_141:
    db 70, 111, 110, 116, 70, 111, 114, 101, 103, 114, 111, 117, 110, 100, 92, 48
__dbase_wfm_text_142:
    db 35, 101, 101, 101, 101, 101, 101, 92, 48
__dbase_wfm_text_143:
    db 70, 111, 114, 109, 49, 92, 48
