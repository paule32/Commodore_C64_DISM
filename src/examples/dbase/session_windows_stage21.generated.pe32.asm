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
    xor eax, eax
    push eax
    call DBaseQtSessionCreate
    add esp, 4
    mov dword ptr [__dbase_object_app_security], eax
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov eax, __dbase_text_1
    mov dword ptr [__dbase_var_username_ptr], eax
    mov dword ptr [__dbase_var_username_len], 8
    mov dword ptr [__dbase_var_username_type], 2
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov eax, __dbase_text_2
    mov dword ptr [__dbase_var_password_ptr], eax
    mov dword ptr [__dbase_var_password_len], 8
    mov dword ptr [__dbase_var_password_type], 2
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov eax, __dbase_text_3
    mov dword ptr [__dbase_var_groupname_ptr], eax
    mov dword ptr [__dbase_var_groupname_len], 5
    mov dword ptr [__dbase_var_groupname_type], 2
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov eax, dword ptr [__dbase_var_username_type]
    mov dword ptr [__dbase_session_user_4_type], eax
    mov eax, dword ptr [__dbase_var_username_num]
    mov dword ptr [__dbase_session_user_4_num], eax
    mov eax, dword ptr [__dbase_var_username_num+4]
    mov dword ptr [__dbase_session_user_4_num+4], eax
    mov eax, dword ptr [__dbase_var_username_ptr]
    mov dword ptr [__dbase_session_user_4_ptr], eax
    mov eax, dword ptr [__dbase_var_username_len]
    mov dword ptr [__dbase_session_user_4_len], eax
    mov eax, dword ptr [__dbase_var_password_type]
    mov dword ptr [__dbase_session_pass_5_type], eax
    mov eax, dword ptr [__dbase_var_password_num]
    mov dword ptr [__dbase_session_pass_5_num], eax
    mov eax, dword ptr [__dbase_var_password_num+4]
    mov dword ptr [__dbase_session_pass_5_num+4], eax
    mov eax, dword ptr [__dbase_var_password_ptr]
    mov dword ptr [__dbase_session_pass_5_ptr], eax
    mov eax, dword ptr [__dbase_var_password_len]
    mov dword ptr [__dbase_session_pass_5_len], eax
    mov eax, dword ptr [__dbase_var_groupname_type]
    mov dword ptr [__dbase_session_group_6_type], eax
    mov eax, dword ptr [__dbase_var_groupname_num]
    mov dword ptr [__dbase_session_group_6_num], eax
    mov eax, dword ptr [__dbase_var_groupname_num+4]
    mov dword ptr [__dbase_session_group_6_num+4], eax
    mov eax, dword ptr [__dbase_var_groupname_ptr]
    mov dword ptr [__dbase_session_group_6_ptr], eax
    mov eax, dword ptr [__dbase_var_groupname_len]
    mov dword ptr [__dbase_session_group_6_len], eax
    push dword ptr [__dbase_session_group_6_len]
    push dword ptr [__dbase_session_group_6_ptr]
    push dword ptr [__dbase_session_pass_5_len]
    push dword ptr [__dbase_session_pass_5_ptr]
    push dword ptr [__dbase_session_user_4_len]
    push dword ptr [__dbase_session_user_4_ptr]
    push dword ptr [__dbase_object_app_security]
    call DBaseQtSessionLogin
    add esp, 28
    mov dword ptr [__dbase_var_result_num], eax
    fild dword ptr [__dbase_var_result_num]
    fstp qword ptr [__dbase_var_result_num]
    mov dword ptr [__dbase_var_result_type], 1
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push 15
    push __dbase_text_4
    call DBaseQtAppendConsole
    add esp, 8
    fld qword ptr [__dbase_var_result_num]
    fstp qword ptr [__dbase_temp_number]
    push dword ptr [__dbase_format_buffer]
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, dword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_strlen_loop_7:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_strlen_done_8
    inc ecx
    inc edx
    jmp __dbase_strlen_loop_7
__dbase_strlen_done_8:
    push edx
    push dword ptr [__dbase_format_buffer]
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_5
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
    db 116, 101, 115, 116, 117, 115, 101, 114
__dbase_text_2:
    db 116, 101, 115, 116, 112, 97, 115, 115
__dbase_text_3:
    db 85, 115, 101, 114, 115
__dbase_text_4:
    db 76, 111, 103, 105, 110, 32, 114, 101, 115, 117, 108, 116, 32, 61, 32
__dbase_text_5:
    db 13, 10
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
__dbase_var_username_type:
    dd 0
__dbase_var_username_num:
    dd 0, 0
__dbase_var_username_ptr:
    dd 0
__dbase_var_username_len:
    dd 0
__dbase_var_password_type:
    dd 0
__dbase_var_password_num:
    dd 0, 0
__dbase_var_password_ptr:
    dd 0
__dbase_var_password_len:
    dd 0
__dbase_var_groupname_type:
    dd 0
__dbase_var_groupname_num:
    dd 0, 0
__dbase_var_groupname_ptr:
    dd 0
__dbase_var_groupname_len:
    dd 0
__dbase_var_result_type:
    dd 0
__dbase_var_result_num:
    dd 0, 0
__dbase_var_result_ptr:
    dd 0
__dbase_var_result_len:
    dd 0
__dbase_session_user_4_type:
    dd 0
__dbase_session_user_4_num:
    dd 0, 0
__dbase_session_user_4_ptr:
    dd 0
__dbase_session_user_4_len:
    dd 0
__dbase_session_pass_5_type:
    dd 0
__dbase_session_pass_5_num:
    dd 0, 0
__dbase_session_pass_5_ptr:
    dd 0
__dbase_session_pass_5_len:
    dd 0
__dbase_session_group_6_type:
    dd 0
__dbase_session_group_6_num:
    dd 0, 0
__dbase_session_group_6_ptr:
    dd 0
__dbase_session_group_6_len:
    dd 0
__dbase_object_app_security:
    dd 0
