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
    xor eax, eax
    push eax
    call DBaseQtSessionCreate
    add esp, 4
    mov dword ptr [__dbase_object_app_security], eax
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    xor eax, eax
    push eax
    call DBaseQtDatabaseCreate
    add esp, 4
    mov dword ptr [__dbase_object_db], eax
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push dword ptr [__dbase_object_app_security]
    push dword ptr [__dbase_object_db]
    call DBaseQtDatabaseSetSession
    add esp, 8
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov eax, __dbase_text_1
    mov dword ptr [__dbase_database_property_4_ptr], eax
    mov dword ptr [__dbase_database_property_4_len], 1
    mov dword ptr [__dbase_database_property_4_type], 2
    push dword ptr [__dbase_database_property_4_len]
    push dword ptr [__dbase_database_property_4_ptr]
    push dword ptr [__dbase_object_db]
    call DBaseQtDatabaseSetPath
    add esp, 12
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov eax, __dbase_text_2
    mov dword ptr [__dbase_database_property_5_ptr], eax
    mov dword ptr [__dbase_database_property_5_len], 4
    mov dword ptr [__dbase_database_property_5_type], 2
    push dword ptr [__dbase_database_property_5_len]
    push dword ptr [__dbase_database_property_5_ptr]
    push dword ptr [__dbase_object_db]
    call DBaseQtDatabaseSetDatabaseName
    add esp, 12
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov eax, __dbase_text_3
    mov dword ptr [__dbase_database_property_6_ptr], eax
    mov dword ptr [__dbase_database_property_6_len], 0
    mov dword ptr [__dbase_database_property_6_type], 2
    push dword ptr [__dbase_database_property_6_len]
    push dword ptr [__dbase_database_property_6_ptr]
    push dword ptr [__dbase_object_db]
    call DBaseQtDatabaseSetUserName
    add esp, 12
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov eax, __dbase_text_3
    mov dword ptr [__dbase_database_property_7_ptr], eax
    mov dword ptr [__dbase_database_property_7_len], 0
    mov dword ptr [__dbase_database_property_7_type], 2
    push dword ptr [__dbase_database_property_7_len]
    push dword ptr [__dbase_database_property_7_ptr]
    push dword ptr [__dbase_object_db]
    call DBaseQtDatabaseSetPassword
    add esp, 12
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov eax, __dbase_text_3
    mov dword ptr [__dbase_database_property_8_ptr], eax
    mov dword ptr [__dbase_database_property_8_len], 0
    mov dword ptr [__dbase_database_property_8_type], 2
    push dword ptr [__dbase_database_property_8_len]
    push dword ptr [__dbase_database_property_8_ptr]
    push dword ptr [__dbase_object_db]
    call DBaseQtDatabaseSetAlias
    add esp, 12
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push dword ptr [__dbase_object_db]
    call DBaseQtDatabaseOpen
    add esp, 4
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push dword ptr [__dbase_object_db]
    call DBaseQtDatabaseCommit
    add esp, 4
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push dword ptr [__dbase_object_db]
    call DBaseQtDatabaseClose
    add esp, 4
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
    je __dbase_format_buffer_free_done_9
    push 32768
    push 0
    push eax
    call VirtualFree
__dbase_format_buffer_free_done_9:
    mov dword ptr [__dbase_format_buffer], 0
    push dword ptr [__dbase_exit_code]
    call ExitProcess

section .data

__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_text_1:
    db 46
__dbase_text_2:
    db 68, 65, 84, 65
__dbase_text_3:
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
__dbase_database_property_4_type:
    dd 0
__dbase_database_property_4_num:
    dd 0, 0
__dbase_database_property_4_ptr:
    dd 0
__dbase_database_property_4_len:
    dd 0
__dbase_database_property_5_type:
    dd 0
__dbase_database_property_5_num:
    dd 0, 0
__dbase_database_property_5_ptr:
    dd 0
__dbase_database_property_5_len:
    dd 0
__dbase_database_property_6_type:
    dd 0
__dbase_database_property_6_num:
    dd 0, 0
__dbase_database_property_6_ptr:
    dd 0
__dbase_database_property_6_len:
    dd 0
__dbase_database_property_7_type:
    dd 0
__dbase_database_property_7_num:
    dd 0, 0
__dbase_database_property_7_ptr:
    dd 0
__dbase_database_property_7_len:
    dd 0
__dbase_database_property_8_type:
    dd 0
__dbase_database_property_8_num:
    dd 0, 0
__dbase_database_property_8_ptr:
    dd 0
__dbase_database_property_8_len:
    dd 0
__dbase_object_app_security:
    dd 0
__dbase_object_db:
    dd 0
