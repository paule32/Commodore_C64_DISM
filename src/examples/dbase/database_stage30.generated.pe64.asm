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
    xor rax, rax
    mov rcx, rax
    sub rsp, 40
    call DBaseQtSessionCreate
    add rsp, 40
    mov qword ptr [__dbase_object_app_security], rax
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    xor rax, rax
    mov rcx, rax
    sub rsp, 40
    call DBaseQtDatabaseCreate
    add rsp, 40
    mov qword ptr [__dbase_object_db], rax
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, qword ptr [__dbase_object_db]
    mov rdx, qword ptr [__dbase_object_app_security]
    sub rsp, 40
    call DBaseQtDatabaseSetSession
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rax, __dbase_text_1
    mov qword ptr [__dbase_database_property_4_ptr], rax
    mov dword ptr [__dbase_database_property_4_len], 1
    mov dword ptr [__dbase_database_property_4_type], 2
    mov rcx, qword ptr [__dbase_object_db]
    mov rdx, qword ptr [__dbase_database_property_4_ptr]
    mov r8d, dword ptr [__dbase_database_property_4_len]
    sub rsp, 40
    call DBaseQtDatabaseSetPath
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rax, __dbase_text_2
    mov qword ptr [__dbase_database_property_5_ptr], rax
    mov dword ptr [__dbase_database_property_5_len], 4
    mov dword ptr [__dbase_database_property_5_type], 2
    mov rcx, qword ptr [__dbase_object_db]
    mov rdx, qword ptr [__dbase_database_property_5_ptr]
    mov r8d, dword ptr [__dbase_database_property_5_len]
    sub rsp, 40
    call DBaseQtDatabaseSetDatabaseName
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rax, __dbase_text_3
    mov qword ptr [__dbase_database_property_6_ptr], rax
    mov dword ptr [__dbase_database_property_6_len], 0
    mov dword ptr [__dbase_database_property_6_type], 2
    mov rcx, qword ptr [__dbase_object_db]
    mov rdx, qword ptr [__dbase_database_property_6_ptr]
    mov r8d, dword ptr [__dbase_database_property_6_len]
    sub rsp, 40
    call DBaseQtDatabaseSetUserName
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rax, __dbase_text_3
    mov qword ptr [__dbase_database_property_7_ptr], rax
    mov dword ptr [__dbase_database_property_7_len], 0
    mov dword ptr [__dbase_database_property_7_type], 2
    mov rcx, qword ptr [__dbase_object_db]
    mov rdx, qword ptr [__dbase_database_property_7_ptr]
    mov r8d, dword ptr [__dbase_database_property_7_len]
    sub rsp, 40
    call DBaseQtDatabaseSetPassword
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rax, __dbase_text_3
    mov qword ptr [__dbase_database_property_8_ptr], rax
    mov dword ptr [__dbase_database_property_8_len], 0
    mov dword ptr [__dbase_database_property_8_type], 2
    mov rcx, qword ptr [__dbase_object_db]
    mov rdx, qword ptr [__dbase_database_property_8_ptr]
    mov r8d, dword ptr [__dbase_database_property_8_len]
    sub rsp, 40
    call DBaseQtDatabaseSetAlias
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, qword ptr [__dbase_object_db]
    sub rsp, 40
    call DBaseQtDatabaseOpen
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, qword ptr [__dbase_object_db]
    sub rsp, 40
    call DBaseQtDatabaseCommit
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, qword ptr [__dbase_object_db]
    sub rsp, 40
    call DBaseQtDatabaseClose
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
    je __dbase_format_buffer_free_done_9
    xor edx, edx
    mov r8d, 32768
    sub rsp, 40
    call VirtualFree
    add rsp, 40
__dbase_format_buffer_free_done_9:
    mov qword ptr [__dbase_format_buffer], 0
    mov ecx, dword ptr [__dbase_exit_code]
    sub rsp, 40
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
    dd 0, 0
__dbase_exit_code:
    dd 0
__dbase_database_property_4_type:
    dd 0
__dbase_database_property_4_num:
    dd 0, 0
__dbase_database_property_4_ptr:
    dd 0, 0
__dbase_database_property_4_len:
    dd 0
__dbase_database_property_5_type:
    dd 0
__dbase_database_property_5_num:
    dd 0, 0
__dbase_database_property_5_ptr:
    dd 0, 0
__dbase_database_property_5_len:
    dd 0
__dbase_database_property_6_type:
    dd 0
__dbase_database_property_6_num:
    dd 0, 0
__dbase_database_property_6_ptr:
    dd 0, 0
__dbase_database_property_6_len:
    dd 0
__dbase_database_property_7_type:
    dd 0
__dbase_database_property_7_num:
    dd 0, 0
__dbase_database_property_7_ptr:
    dd 0, 0
__dbase_database_property_7_len:
    dd 0
__dbase_database_property_8_type:
    dd 0
__dbase_database_property_8_num:
    dd 0, 0
__dbase_database_property_8_ptr:
    dd 0, 0
__dbase_database_property_8_len:
    dd 0
__dbase_object_app_security:
    dd 0, 0
__dbase_object_db:
    dd 0, 0
