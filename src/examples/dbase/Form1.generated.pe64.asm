bits 64

import DBaseQtSetWorkstationMode, "libd64_qt5.dll", "DBaseQtSetWorkstationMode"
import DBaseQtSetDebugTheme, "libd64_qt5.dll", "DBaseQtSetDebugTheme"
import DBaseQtInitialize, "libd64_qt5.dll", "DBaseQtInitialize"
import DBaseQtShowWindow, "libd64_qt5.dll", "DBaseQtShowWindow"
import DBaseQtProcessEvents, "libd64_qt5.dll", "DBaseQtProcessEvents"
import DBaseQtSetDebugVisible, "libd64_qt5.dll", "DBaseQtSetDebugVisible"
import DBaseQtAppendConsole, "libd64_qt5.dll", "DBaseQtAppendConsole"
import DBaseQtAppendDebug, "libd64_qt5.dll", "DBaseQtAppendDebug"
import DBaseQtSetOutputColor, "libd64_qt5.dll", "DBaseQtSetOutputColor"
import DBaseQtClearScreen, "libd64_qt5.dll", "DBaseQtClearScreen"
import DBaseQtClearScreenChar, "libd64_qt5.dll", "DBaseQtClearScreenChar"
import DBaseQtClearScreenColor, "libd64_qt5.dll", "DBaseQtClearScreenColor"
import DBaseQtSetBorderColor, "libd64_qt5.dll", "DBaseQtSetBorderColor"
import DBaseQtMarkProgramFinished, "libd64_qt5.dll", "DBaseQtMarkProgramFinished"
import DBaseQtExec, "libd64_qt5.dll", "DBaseQtExec"
import DBaseQtShutdownRequested, "libd64_qt5.dll", "DBaseQtShutdownRequested"
import DBaseQtShutdown, "libd64_qt5.dll", "DBaseQtShutdown"
import DBaseQtMenuCreate, "libd64_qt5.dll", "DBaseQtMenuCreate"
import DBaseQtMenuSetText, "libd64_qt5.dll", "DBaseQtMenuSetText"
import DBaseQtMenuSetSeparator, "libd64_qt5.dll", "DBaseQtMenuSetSeparator"
import DBaseQtMenuSetShortcut, "libd64_qt5.dll", "DBaseQtMenuSetShortcut"
import DBaseQtMenuSetOnClick, "libd64_qt5.dll", "DBaseQtMenuSetOnClick"
import DBaseQtEnsureDefaultMenu, "libd64_qt5.dll", "DBaseQtEnsureDefaultMenu"
import DBaseQtSetColorNormal, "libd64_qt5.dll", "DBaseQtSetColorNormal"
import DBaseQtSessionCreate, "libd64_qt5.dll", "DBaseQtSessionCreate"
import DBaseQtGetLoginSession, "libd64_qt5.dll", "DBaseQtGetLoginSession"
import DBaseQtSessionLogin, "libd64_qt5.dll", "DBaseQtSessionLogin"
import DBaseQtDatabaseCreate, "libd64_qt5.dll", "DBaseQtDatabaseCreate"
import DBaseQtDatabaseSetPath, "libd64_qt5.dll", "DBaseQtDatabaseSetPath"
import DBaseQtDatabaseSetDatabaseName, "libd64_qt5.dll", "DBaseQtDatabaseSetDatabaseName"
import DBaseQtDatabaseSetUserName, "libd64_qt5.dll", "DBaseQtDatabaseSetUserName"
import DBaseQtDatabaseSetPassword, "libd64_qt5.dll", "DBaseQtDatabaseSetPassword"
import DBaseQtDatabaseSetAlias, "libd64_qt5.dll", "DBaseQtDatabaseSetAlias"
import DBaseQtDatabaseSetSession, "libd64_qt5.dll", "DBaseQtDatabaseSetSession"
import DBaseQtDatabaseSetActive, "libd64_qt5.dll", "DBaseQtDatabaseSetActive"
import DBaseQtDatabaseOpen, "libd64_qt5.dll", "DBaseQtDatabaseOpen"
import DBaseQtDatabaseClose, "libd64_qt5.dll", "DBaseQtDatabaseClose"
import DBaseQtDatabaseCommit, "libd64_qt5.dll", "DBaseQtDatabaseCommit"
import __dbase_gcvt, "msvcrt.dll", "_gcvt"
import __dbase_malloc, "msvcrt.dll", "malloc"
import __dbase_memcpy, "msvcrt.dll", "memcpy"
import __dbase_memcmp, "msvcrt.dll", "memcmp"
import ExitProcess, "kernel32.dll", "ExitProcess"
import VirtualAlloc, "kernel32.dll", "VirtualAlloc"
import VirtualFree, "kernel32.dll", "VirtualFree"
import AllocConsole, "kernel32.dll", "AllocConsole"
import FreeConsole, "kernel32.dll", "FreeConsole"
import GetStdHandle, "kernel32.dll", "GetStdHandle"
import CreateFileA, "kernel32.dll", "CreateFileA"
import GetConsoleScreenBufferInfo, "kernel32.dll", "GetConsoleScreenBufferInfo"
import SetConsoleScreenBufferSize, "kernel32.dll", "SetConsoleScreenBufferSize"
import SetConsoleOutputCP, "kernel32.dll", "SetConsoleOutputCP"
import SetConsoleTitleA, "kernel32.dll", "SetConsoleTitleA"
import GetConsoleWindow, "kernel32.dll", "GetConsoleWindow"
import ShowWindow, "user32.dll", "ShowWindow"
import SetWindowPos, "user32.dll", "SetWindowPos"
import SetForegroundWindow, "user32.dll", "SetForegroundWindow"
import WriteFile, "kernel32.dll", "WriteFile"
import DBaseQtInitializeGui, "libd64_qt5.dll", "DBaseQtInitializeGui"
import DBaseQtFormCreate, "libd64_qt5.dll", "DBaseQtFormCreate"
import DBaseQtControlCreateEx, "libd64_qt5.dll", "DBaseQtControlCreateEx"
import DBaseQtWidgetSetGeometry, "libd64_qt5.dll", "DBaseQtWidgetSetGeometry"
import DBaseQtWidgetSetProperty, "libd64_qt5.dll", "DBaseQtWidgetSetProperty"
import DBaseQtWidgetSetFont, "libd64_qt5.dll", "DBaseQtWidgetSetFont"
import DBaseQtObjectBindEvent, "libd64_qt5.dll", "DBaseQtObjectBindEvent"
import DBaseQtTimerCreate, "libd64_qt5.dll", "DBaseQtTimerCreate"
import DBaseQtFormOpen, "libd64_qt5.dll", "DBaseQtFormOpen"
import DBaseQtConsoleWrite, "libd64_qt5.dll", "DBaseQtConsoleWrite"
import GetSystemMetrics, "user32.dll", "GetSystemMetrics"
import GetRawInputDeviceList, "user32.dll", "GetRawInputDeviceList"
import __dbase_upper_buffer, "libd64_qt5.dll", "DBaseUpperBuffer"
global _start
entry _start

section .text

_start:
    mov ecx, 0
    sub rsp, 40
    call DBaseQtSetWorkstationMode
    add rsp, 40
    mov ecx, 0
    sub rsp, 40
    call DBaseQtSetDebugTheme
    add rsp, 40
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
    cmp dword ptr [__dbase_output_debug_override], -1
    jne __dbase_output_override_ready_4
    cmp dword ptr [__dbase_output_format_screen], 0
    je __dbase_output_console_5
    jmp __dbase_output_show_done_6
__dbase_output_override_ready_4:
    cmp dword ptr [__dbase_output_debug_override], 0
    je __dbase_output_console_5
__dbase_output_show_done_6:
    cmp dword ptr [__dbase_output_debug_visible], 0
    jne __dbase_output_already_visible_8
    mov dword ptr [__dbase_output_debug_visible], 1
    mov ecx, 1
    sub rsp, 40
    call DBaseQtSetDebugVisible
    add rsp, 40
__dbase_output_already_visible_8:
    jmp __dbase_output_done_7
__dbase_output_console_5:
    mov rcx, __dbase_text_2
    mov edx, 0
    sub rsp, 8
    call __dbase_console_write
    add rsp, 8
__dbase_output_done_7:
    sub rsp, 40
    call DBaseQtProcessEvents
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
    sub rsp, 8
    call __dbase_console_shutdown
    add rsp, 8
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

; Stage 109: lazy Win32 console for dBase ? / ??
__dbase_console_ensure:
    cmp dword ptr [__dbase_console_ready], 0
    jne __dbase_console_ensure_done
    sub rsp, 40
    call AllocConsole
    add rsp, 40
    sub rsp, 56
    mov rcx, __dbase_console_out_name
    mov edx, 3221225472
    mov r8d, 3
    xor r9d, r9d
    mov qword ptr [rsp+32], 3
    mov qword ptr [rsp+40], 0
    mov qword ptr [rsp+48], 0
    call CreateFileA
    add rsp, 56
    test rax, rax
    je __dbase_console_handle_fallback
    cmp rax, -1
    je __dbase_console_handle_fallback
    mov qword ptr [__dbase_console_handle], rax
    jmp __dbase_console_handle_ready
__dbase_console_handle_fallback:
    mov ecx, -11
    sub rsp, 40
    call GetStdHandle
    add rsp, 40
    test rax, rax
    je __dbase_console_ensure_done
    cmp rax, -1
    je __dbase_console_ensure_done
    mov qword ptr [__dbase_console_handle], rax
__dbase_console_handle_ready:
    mov ecx, 1252
    sub rsp, 40
    call SetConsoleOutputCP
    add rsp, 40
    mov rcx, qword ptr [__dbase_console_handle]
    mov rdx, __dbase_console_info
    sub rsp, 40
    call GetConsoleScreenBufferInfo
    add rsp, 40
    test eax, eax
    je __dbase_console_buffer_fallback
    mov edx, dword ptr [__dbase_console_info]
    and edx, 65535
    or edx, 32768000
    jmp __dbase_console_buffer_ready
__dbase_console_buffer_fallback:
    mov edx, 32768080
__dbase_console_buffer_ready:
    mov rcx, qword ptr [__dbase_console_handle]
    sub rsp, 40
    call SetConsoleScreenBufferSize
    add rsp, 40
    mov rcx, __dbase_text_1
    sub rsp, 40
    call SetConsoleTitleA
    add rsp, 40
    sub rsp, 40
    call GetConsoleWindow
    add rsp, 40
    test rax, rax
    je __dbase_console_window_ready
    mov qword ptr [__dbase_console_window], rax
    mov rcx, rax
    mov edx, 5
    sub rsp, 40
    call ShowWindow
    add rsp, 40
    mov rcx, qword ptr [__dbase_console_window]
    mov rdx, -1
    xor r8d, r8d
    xor r9d, r9d
    sub rsp, 56
    mov qword ptr [rsp+32], 0
    mov qword ptr [rsp+40], 0
    mov dword ptr [rsp+48], 67
    call SetWindowPos
    add rsp, 56
    mov rcx, qword ptr [__dbase_console_window]
    sub rsp, 40
    call SetForegroundWindow
    add rsp, 40
__dbase_console_window_ready:
    mov dword ptr [__dbase_console_ready], 1
__dbase_console_ensure_done:
    ret

__dbase_console_write:
    sub rsp, 56
    mov qword ptr [rsp+40], rcx
    mov dword ptr [rsp+48], edx
    call __dbase_console_ensure
    cmp dword ptr [__dbase_console_ready], 0
    je __dbase_console_write_done
    cmp dword ptr [rsp+48], 0
    je __dbase_console_write_done
    mov rcx, qword ptr [__dbase_console_handle]
    mov rdx, qword ptr [rsp+40]
    mov r8d, dword ptr [rsp+48]
    mov r9, __dbase_console_written
    mov qword ptr [rsp+32], 0
    call WriteFile
__dbase_console_write_done:
    add rsp, 56
    ret

__dbase_console_shutdown:
    cmp dword ptr [__dbase_console_ready], 0
    je __dbase_console_shutdown_done
    sub rsp, 40
    call FreeConsole
    add rsp, 40
    mov qword ptr [__dbase_console_handle], 0
    mov qword ptr [__dbase_console_window], 0
    mov dword ptr [__dbase_console_ready], 0
__dbase_console_shutdown_done:
    ret

section .data

__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_text_1:
    db 100, 66, 97, 115, 101, 32, 67, 111, 110, 115, 111, 108, 101, 32, 91, 77, 79, 68, 65, 76, 32, 84, 69, 83
    db 84, 93, 0
__dbase_output_debug_override:
    dd -1
__dbase_console_out_name:
    db 67, 79, 78, 79, 85, 84, 36, 0
__dbase_workstation_lazy_console_marker:
    db 68, 54, 52, 68, 66, 65, 83, 69, 95, 76, 65, 90, 89, 95, 67, 79, 78, 83, 79, 76, 69, 95, 86, 49, 0

section .bss

__dbase_temp_number:
    resd 1
__dbase_temp_number_hi:
    resd 1
__dbase_int_cw:
    resw 1
__dbase_int_cw_trunc:
    resw 1
__dbase_call_number:
    resq 1
__dbase_format_buffer:
    resq 1
__dbase_exit_code:
    resd 1
__dbase_output_format_screen:
    resd 1
__dbase_output_debug_visible:
    resd 1
__dbase_console_ready:
    resd 1
__dbase_console_handle:
    resq 1
__dbase_console_window:
    resq 1
__dbase_console_written:
    resd 1
__dbase_console_number_len:
    resd 1
__dbase_console_info:
    resd 8
__dbase_text_2:
    resb 1

; Stage 127: eigener WFM-GUI-Programmeinstieg
.section .text
.entry __d64_wfm_entry
__d64_wfm_entry:
    mov rax, __dbase_wfm_qt_output_marker
    mov ecx, 0
    sub rsp, 40
    call DBaseQtSetWorkstationMode
    add rsp, 40
    mov ecx, 0
    sub rsp, 40
    call DBaseQtSetDebugTheme
    add rsp, 40
    mov rcx, __dbase_wfm_text_0
    sub rsp, 40
    call DBaseQtInitializeGui
    add rsp, 40
    xor ecx, ecx
    mov edx, 96
    mov r8d, 12288
    mov r9d, 4
    sub rsp, 40
    call VirtualAlloc
    add rsp, 40
    test rax, rax
    jne __dbase_wfm_format_buffer_ok
    mov ecx, 1
    sub rsp, 40
    call ExitProcess
__dbase_wfm_format_buffer_ok:
    mov qword ptr [__dbase_format_buffer], rax
    mov rcx, __dbase_wfm_text_0
    mov edx, 5
    sub rsp, 40
    call DBaseQtFormCreate
    add rsp, 40
    mov qword ptr [__dbase_wfm_form], rax
    mov rcx, qword ptr [__dbase_wfm_form]
    mov edx, 10
    mov r8d, 20
    mov r9d, 640
    sub rsp, 48
    mov dword ptr [rsp+32], 480
    call DBaseQtWidgetSetGeometry
    add rsp, 48
    mov rcx, qword ptr [__dbase_wfm_form]
    mov rdx, __dbase_wfm_text_1
    mov r8d, 8
    mov r9d, 12
    sub rsp, 72
    mov dword ptr [rsp+32], 1
    mov dword ptr [rsp+40], 0
    mov dword ptr [rsp+48], 0
    mov dword ptr [rsp+56], 1
    call DBaseQtWidgetSetFont
    add rsp, 72
    mov rcx, qword ptr [__dbase_wfm_form]
    mov rdx, __dbase_wfm_property_table_0
    mov r8d, 35
    sub rsp, 40
    call __dbase_wfm_set_properties_packed
    add rsp, 40
    mov rcx, __dbase_wfm_text_57
    mov edx, 10
    mov r8, qword ptr [__dbase_wfm_form]
    mov r9, __dbase_wfm_text_58
    sub rsp, 48
    mov dword ptr [rsp+32], 7
    call DBaseQtControlCreateEx
    add rsp, 48
    mov qword ptr [__dbase_wfm_obj_THIS_PushButton1], rax
    mov rcx, qword ptr [__dbase_wfm_obj_THIS_PushButton1]
    mov edx, 30
    mov r8d, 40
    mov r9d, 174
    sub rsp, 48
    mov dword ptr [rsp+32], 85
    call DBaseQtWidgetSetGeometry
    add rsp, 48
    mov rcx, qword ptr [__dbase_wfm_obj_THIS_PushButton1]
    mov rdx, __dbase_wfm_text_59
    mov r8d, 5
    mov r9d, 9
    sub rsp, 72
    mov dword ptr [rsp+32], 1
    mov dword ptr [rsp+40], 0
    mov dword ptr [rsp+48], 0
    mov dword ptr [rsp+56], 1
    call DBaseQtWidgetSetFont
    add rsp, 72
    mov rcx, qword ptr [__dbase_wfm_obj_THIS_PushButton1]
    mov rdx, __dbase_wfm_property_table_1
    mov r8d, 34
    sub rsp, 40
    call __dbase_wfm_set_properties_packed
    add rsp, 40
    mov rcx, qword ptr [__dbase_wfm_obj_THIS_PushButton1]
    mov rdx, __dbase_wfm_text_74
    mov r8d, 7
    mov r9, __dbase_wfm_proc_PushButton1_onClick
    sub rsp, 40
    call DBaseQtObjectBindEvent
    add rsp, 40
    sub rsp, 40
    mov rcx, 51
    mov rdx, 4
    call __dbase_wfm_proc___init__
    add rsp, 40
    mov rcx, qword ptr [__dbase_wfm_form]
    sub rsp, 40
    call DBaseQtFormOpen
    add rsp, 40
    sub rsp, 40
    call __dbase_wfm_proc___main__
    add rsp, 40
    sub rsp, 40
    call DBaseQtExec
    add rsp, 40
    sub rsp, 40
    call __dbase_wfm_proc___del__
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdown
    add rsp, 40
    mov rcx, qword ptr [__dbase_format_buffer]
    test rcx, rcx
    je __dbase_wfm_format_buffer_free_done
    xor edx, edx
    mov r8d, 32768
    sub rsp, 40
    call VirtualFree
    add rsp, 40
    mov qword ptr [__dbase_format_buffer], 0
__dbase_wfm_format_buffer_free_done:
    xor ecx, ecx
    sub rsp, 40
    call ExitProcess

; Stage 133: WFM Event-/Methoden-Code
.section .text

; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: __del__
; ------------------------------------------------------------
__dbase_wfm_proc___del__:
    sub rsp, 40
    jmp __dbase_wfm_flow_method_exit_1
__dbase_wfm_flow_method_exit_1:
    add rsp, 40
    ret
; END WFM PROCEDURE/FUNCTION: __del__


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: __init__
; ------------------------------------------------------------
__dbase_wfm_proc___init__:
    sub rsp, 40
    mov qword ptr [__dbase_wfm_param___init___p1], rcx
    mov qword ptr [__dbase_wfm_param___init___p2], rdx
    ; ? "p1 = " + p1
    mov rcx, __dbase_wfm_output_text_75
    mov edx, 5
    mov r8d, 0
    call DBaseQtConsoleWrite
    cmp dword ptr [__dbase_wfm_mem_p1_type], 0
    je __dbase_wfm_print_null_0
    cmp dword ptr [__dbase_wfm_mem_p1_type], 3
    je __dbase_wfm_print_string_0
    cmp dword ptr [__dbase_wfm_mem_p1_type], 4
    je __dbase_wfm_print_object_0
    cmp dword ptr [__dbase_wfm_mem_p1_type], 1
    je __dbase_wfm_print_number_0
    cmp dword ptr [__dbase_wfm_mem_p1_type], 2
    je __dbase_wfm_print_number_0
    jmp __dbase_wfm_print_null_0
__dbase_wfm_print_number_0:
    fld qword ptr [__dbase_wfm_mem_p1_num]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, qword ptr [__dbase_format_buffer]
    call __dbase_gcvt
    mov rcx, qword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_wfm_strlen_0:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_wfm_strlen_done_0
    inc rcx
    inc edx
    jmp __dbase_wfm_strlen_0
__dbase_wfm_strlen_done_0:
    mov rcx, qword ptr [__dbase_format_buffer]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_0
__dbase_wfm_print_string_0:
    mov rcx, qword ptr [__dbase_wfm_mem_p1_ptr]
    test rcx, rcx
    je __dbase_wfm_print_null_0
    mov edx, dword ptr [__dbase_wfm_mem_p1_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_0
__dbase_wfm_print_object_0:
    mov rax, qword ptr [__dbase_wfm_mem_p1_ptr]
    test rax, rax
    je __dbase_wfm_print_null_0
    mov rcx, __dbase_wfm_output_text_77
    mov edx, 8
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_0
__dbase_wfm_print_null_0:
    mov rcx, __dbase_wfm_output_text_76
    mov edx, 6
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_print_done_0:
    ; ? "p2 = " + p2
    mov rcx, __dbase_wfm_output_text_78
    mov edx, 5
    mov r8d, 0
    call DBaseQtConsoleWrite
    cmp dword ptr [__dbase_wfm_mem_p2_type], 0
    je __dbase_wfm_print_null_1
    cmp dword ptr [__dbase_wfm_mem_p2_type], 3
    je __dbase_wfm_print_string_1
    cmp dword ptr [__dbase_wfm_mem_p2_type], 4
    je __dbase_wfm_print_object_1
    cmp dword ptr [__dbase_wfm_mem_p2_type], 1
    je __dbase_wfm_print_number_1
    cmp dword ptr [__dbase_wfm_mem_p2_type], 2
    je __dbase_wfm_print_number_1
    jmp __dbase_wfm_print_null_1
__dbase_wfm_print_number_1:
    fld qword ptr [__dbase_wfm_mem_p2_num]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, qword ptr [__dbase_format_buffer]
    call __dbase_gcvt
    mov rcx, qword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_wfm_strlen_1:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_wfm_strlen_done_1
    inc rcx
    inc edx
    jmp __dbase_wfm_strlen_1
__dbase_wfm_strlen_done_1:
    mov rcx, qword ptr [__dbase_format_buffer]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_1
__dbase_wfm_print_string_1:
    mov rcx, qword ptr [__dbase_wfm_mem_p2_ptr]
    test rcx, rcx
    je __dbase_wfm_print_null_1
    mov edx, dword ptr [__dbase_wfm_mem_p2_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_1
__dbase_wfm_print_object_1:
    mov rax, qword ptr [__dbase_wfm_mem_p2_ptr]
    test rax, rax
    je __dbase_wfm_print_null_1
    mov rcx, __dbase_wfm_output_text_80
    mov edx, 8
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_1
__dbase_wfm_print_null_1:
    mov rcx, __dbase_wfm_output_text_79
    mov edx, 6
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_print_done_1:
    jmp __dbase_wfm_flow_method_exit_2
__dbase_wfm_flow_method_exit_2:
    add rsp, 40
    ret
; END WFM PROCEDURE/FUNCTION: __init__


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: __main__
; ------------------------------------------------------------
__dbase_wfm_proc___main__:
    sub rsp, 40
    mov eax, 7
    jmp __dbase_wfm_flow_method_exit_3
__dbase_wfm_flow_method_exit_3:
    add rsp, 40
    ret
; END WFM PROCEDURE/FUNCTION: __main__


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: PushButton1_onClick
; ------------------------------------------------------------
__dbase_wfm_proc_PushButton1_onClick:
    sub rsp, 40
    mov qword ptr [__dbase_wfm_param_PushButton1_onClick_Sender], rcx
    ; STORE 101.42 TO Ausdruck
    fld qword ptr [__dbase_wfm_numconst_0]
    fstp qword ptr [__dbase_wfm_mem_Ausdruck_num]
    mov dword ptr [__dbase_wfm_mem_Ausdruck_type], 2
    mov dword ptr [__dbase_wfm_mem_Ausdruck_len], 0
    mov qword ptr [__dbase_wfm_mem_Ausdruck_ptr], 0
    ; Ausdruck = 101.42
    fld qword ptr [__dbase_wfm_numconst_1]
    fstp qword ptr [__dbase_wfm_mem_Ausdruck_num]
    mov dword ptr [__dbase_wfm_mem_Ausdruck_type], 2
    mov dword ptr [__dbase_wfm_mem_Ausdruck_len], 0
    mov qword ptr [__dbase_wfm_mem_Ausdruck_ptr], 0
    ; ? Ausdruck
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 0
    je __dbase_wfm_print_null_2
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 3
    je __dbase_wfm_print_string_2
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 4
    je __dbase_wfm_print_object_2
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 1
    je __dbase_wfm_print_number_2
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 2
    je __dbase_wfm_print_number_2
    jmp __dbase_wfm_print_null_2
__dbase_wfm_print_number_2:
    fld qword ptr [__dbase_wfm_mem_Ausdruck_num]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, qword ptr [__dbase_format_buffer]
    call __dbase_gcvt
    mov rcx, qword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_wfm_strlen_2:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_wfm_strlen_done_2
    inc rcx
    inc edx
    jmp __dbase_wfm_strlen_2
__dbase_wfm_strlen_done_2:
    mov rcx, qword ptr [__dbase_format_buffer]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_2
__dbase_wfm_print_string_2:
    mov rcx, qword ptr [__dbase_wfm_mem_Ausdruck_ptr]
    test rcx, rcx
    je __dbase_wfm_print_null_2
    mov edx, dword ptr [__dbase_wfm_mem_Ausdruck_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_2
__dbase_wfm_print_object_2:
    mov rax, qword ptr [__dbase_wfm_mem_Ausdruck_ptr]
    test rax, rax
    je __dbase_wfm_print_null_2
    mov rcx, __dbase_wfm_output_text_82
    mov edx, 8
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_2
__dbase_wfm_print_null_2:
    mov rcx, __dbase_wfm_output_text_81
    mov edx, 6
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_print_done_2:
    ; STORE INT(Ausdruck) TO Ausdruck
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 1
    je __dbase_wfm_int_numeric_3
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 2
    je __dbase_wfm_int_numeric_3
    mov dword ptr [__dbase_wfm_mem_Ausdruck_type], 0
    mov dword ptr [__dbase_wfm_mem_Ausdruck_len], 0
    mov qword ptr [__dbase_wfm_mem_Ausdruck_ptr], 0
    jmp __dbase_wfm_int_done_3
__dbase_wfm_int_numeric_3:
    fld qword ptr [__dbase_wfm_mem_Ausdruck_num]
    sub rsp, 8
    fnstcw word ptr [rsp]
    mov eax, dword ptr [rsp]
    or eax, 0x0C00
    mov dword ptr [rsp+4], eax
    fldcw word ptr [rsp+4]
    frndint
    fldcw word ptr [rsp]
    add rsp, 8
    fstp qword ptr [__dbase_wfm_mem_Ausdruck_num]
    mov dword ptr [__dbase_wfm_mem_Ausdruck_type], 1
    mov dword ptr [__dbase_wfm_mem_Ausdruck_len], 0
    mov qword ptr [__dbase_wfm_mem_Ausdruck_ptr], 0
__dbase_wfm_int_done_3:
    ; ? Ausdruck
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 0
    je __dbase_wfm_print_null_4
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 3
    je __dbase_wfm_print_string_4
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 4
    je __dbase_wfm_print_object_4
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 1
    je __dbase_wfm_print_number_4
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 2
    je __dbase_wfm_print_number_4
    jmp __dbase_wfm_print_null_4
__dbase_wfm_print_number_4:
    fld qword ptr [__dbase_wfm_mem_Ausdruck_num]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, qword ptr [__dbase_format_buffer]
    call __dbase_gcvt
    mov rcx, qword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_wfm_strlen_3:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_wfm_strlen_done_3
    inc rcx
    inc edx
    jmp __dbase_wfm_strlen_3
__dbase_wfm_strlen_done_3:
    mov rcx, qword ptr [__dbase_format_buffer]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_4
__dbase_wfm_print_string_4:
    mov rcx, qword ptr [__dbase_wfm_mem_Ausdruck_ptr]
    test rcx, rcx
    je __dbase_wfm_print_null_4
    mov edx, dword ptr [__dbase_wfm_mem_Ausdruck_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_4
__dbase_wfm_print_object_4:
    mov rax, qword ptr [__dbase_wfm_mem_Ausdruck_ptr]
    test rax, rax
    je __dbase_wfm_print_null_4
    mov rcx, __dbase_wfm_output_text_84
    mov edx, 8
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_4
__dbase_wfm_print_null_4:
    mov rcx, __dbase_wfm_output_text_83
    mov edx, 6
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_print_done_4:
    ; ? "1: " + 101.42
    mov rcx, __dbase_wfm_output_text_85
    mov edx, 3
    mov r8d, 0
    call DBaseQtConsoleWrite
    mov rcx, __dbase_wfm_output_text_86
    mov edx, 6
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; ? "2: " + INT(101.42)
    mov rcx, __dbase_wfm_output_text_87
    mov edx, 3
    mov r8d, 0
    call DBaseQtConsoleWrite
    mov rcx, __dbase_wfm_output_text_88
    mov edx, 3
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; ? "3: " + Ausdruck
    mov rcx, __dbase_wfm_output_text_89
    mov edx, 3
    mov r8d, 0
    call DBaseQtConsoleWrite
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 0
    je __dbase_wfm_print_null_5
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 3
    je __dbase_wfm_print_string_5
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 4
    je __dbase_wfm_print_object_5
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 1
    je __dbase_wfm_print_number_5
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 2
    je __dbase_wfm_print_number_5
    jmp __dbase_wfm_print_null_5
__dbase_wfm_print_number_5:
    fld qword ptr [__dbase_wfm_mem_Ausdruck_num]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, qword ptr [__dbase_format_buffer]
    call __dbase_gcvt
    mov rcx, qword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_wfm_strlen_4:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_wfm_strlen_done_4
    inc rcx
    inc edx
    jmp __dbase_wfm_strlen_4
__dbase_wfm_strlen_done_4:
    mov rcx, qword ptr [__dbase_format_buffer]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_5
__dbase_wfm_print_string_5:
    mov rcx, qword ptr [__dbase_wfm_mem_Ausdruck_ptr]
    test rcx, rcx
    je __dbase_wfm_print_null_5
    mov edx, dword ptr [__dbase_wfm_mem_Ausdruck_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_5
__dbase_wfm_print_object_5:
    mov rax, qword ptr [__dbase_wfm_mem_Ausdruck_ptr]
    test rax, rax
    je __dbase_wfm_print_null_5
    mov rcx, __dbase_wfm_output_text_91
    mov edx, 8
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_5
__dbase_wfm_print_null_5:
    mov rcx, __dbase_wfm_output_text_90
    mov edx, 6
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_print_done_5:
    ; STORE "Zeichenstring" TO SpeicherVar
    mov rax, __dbase_wfm_output_text_92
    mov qword ptr [__dbase_wfm_mem_SpeicherVar_ptr], rax
    mov dword ptr [__dbase_wfm_mem_SpeicherVar_len], 13
    mov dword ptr [__dbase_wfm_mem_SpeicherVar_type], 3
    ; ? "4: " + SpeicherVar
    mov rcx, __dbase_wfm_output_text_93
    mov edx, 3
    mov r8d, 0
    call DBaseQtConsoleWrite
    cmp dword ptr [__dbase_wfm_mem_SpeicherVar_type], 0
    je __dbase_wfm_print_null_6
    cmp dword ptr [__dbase_wfm_mem_SpeicherVar_type], 3
    je __dbase_wfm_print_string_6
    cmp dword ptr [__dbase_wfm_mem_SpeicherVar_type], 4
    je __dbase_wfm_print_object_6
    cmp dword ptr [__dbase_wfm_mem_SpeicherVar_type], 1
    je __dbase_wfm_print_number_6
    cmp dword ptr [__dbase_wfm_mem_SpeicherVar_type], 2
    je __dbase_wfm_print_number_6
    jmp __dbase_wfm_print_null_6
__dbase_wfm_print_number_6:
    fld qword ptr [__dbase_wfm_mem_SpeicherVar_num]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, qword ptr [__dbase_format_buffer]
    call __dbase_gcvt
    mov rcx, qword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_wfm_strlen_5:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_wfm_strlen_done_5
    inc rcx
    inc edx
    jmp __dbase_wfm_strlen_5
__dbase_wfm_strlen_done_5:
    mov rcx, qword ptr [__dbase_format_buffer]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_6
__dbase_wfm_print_string_6:
    mov rcx, qword ptr [__dbase_wfm_mem_SpeicherVar_ptr]
    test rcx, rcx
    je __dbase_wfm_print_null_6
    mov edx, dword ptr [__dbase_wfm_mem_SpeicherVar_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_6
__dbase_wfm_print_object_6:
    mov rax, qword ptr [__dbase_wfm_mem_SpeicherVar_ptr]
    test rax, rax
    je __dbase_wfm_print_null_6
    mov rcx, __dbase_wfm_output_text_95
    mov edx, 8
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_6
__dbase_wfm_print_null_6:
    mov rcx, __dbase_wfm_output_text_94
    mov edx, 6
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_print_done_6:
    cmp dword ptr [__dbase_wfm_mem_SpeicherVar_type], 3
    je __wfm_upper_7_valid
    mov ecx, 13
    call ExitProcess
__wfm_upper_7_valid:
    fld qword ptr [__dbase_wfm_numconst_2]
    fstp qword ptr [__dbase_wfm_mem___string_arg_9_num]
    mov dword ptr [__dbase_wfm_mem___string_arg_9_type], 2
    mov dword ptr [__dbase_wfm_mem___string_arg_9_len], 0
    mov qword ptr [__dbase_wfm_mem___string_arg_9_ptr], 0
    fld qword ptr [__dbase_wfm_numconst_3]
    fstp qword ptr [__dbase_wfm_mem___string_arg_10_num]
    mov dword ptr [__dbase_wfm_mem___string_arg_10_type], 2
    mov dword ptr [__dbase_wfm_mem___string_arg_10_len], 0
    mov qword ptr [__dbase_wfm_mem___string_arg_10_ptr], 0
    mov eax, dword ptr [__dbase_wfm_mem_SpeicherVar_len]
    add eax, 1
    mov ecx, eax
    call __dbase_malloc
    test rax, rax
    jne __wfm_upper_8_allocated
    mov ecx, 8
    call ExitProcess
__wfm_upper_8_allocated:
    mov qword ptr [__dbase_wfm_mem___string_arg_8_ptr], rax
    push rbx
    push rsi
    push rdi
    push rbp
    sub rsp, 16
    xor ebx, ebx
    mov eax, dword ptr [__dbase_wfm_mem___string_arg_9_num+4]
    test eax, eax
    js __wfm_upper_8_start_done
    cmp eax, 0x41E00000
    jb __wfm_upper_8_start_convert
    mov ebx, 2147483647
    jmp __wfm_upper_8_start_done
__wfm_upper_8_start_convert:
    fnstcw word ptr [rsp]
    movzx eax, word ptr [rsp]
    or eax, 0x0C00
    mov dword ptr [rsp+4], eax
    fldcw word ptr [rsp+4]
    fld qword ptr [__dbase_wfm_mem___string_arg_9_num]
    fistp dword ptr [rsp+8]
    fldcw word ptr [rsp]
    mov ebx, dword ptr [rsp+8]
__wfm_upper_8_start_done:
    test ebx, ebx
    je __wfm_upper_8_start_ready
    dec ebx
__wfm_upper_8_start_ready:
    xor ecx, ecx
    mov eax, dword ptr [__dbase_wfm_mem___string_arg_10_num+4]
    test eax, eax
    js __wfm_upper_8_count_done
    cmp eax, 0x41E00000
    jb __wfm_upper_8_count_convert
    mov ecx, 2147483647
    jmp __wfm_upper_8_count_done
__wfm_upper_8_count_convert:
    fnstcw word ptr [rsp]
    movzx eax, word ptr [rsp]
    or eax, 0x0C00
    mov dword ptr [rsp+4], eax
    fldcw word ptr [rsp+4]
    fld qword ptr [__dbase_wfm_mem___string_arg_10_num]
    fistp dword ptr [rsp+8]
    fldcw word ptr [rsp]
    mov ecx, dword ptr [rsp+8]
__wfm_upper_8_count_done:
    add rsp, 16
    mov rsi, qword ptr [__dbase_wfm_mem_SpeicherVar_ptr]
    mov rdi, qword ptr [__dbase_wfm_mem___string_arg_8_ptr]
    mov edx, dword ptr [__dbase_wfm_mem_SpeicherVar_len]
__wfm_upper_8_loop:
    test edx, edx
    je __wfm_upper_8_done
    test ecx, ecx
    je __wfm_upper_8_done
    movzx eax, byte ptr [rsi]
    mov ebp, 1
    cmp eax, 194
    jb __wfm_upper_8_width
    cmp eax, 245
    jae __wfm_upper_8_width
    mov ebp, 2
    cmp eax, 224
    jb __wfm_upper_8_width
    mov ebp, 3
    cmp eax, 240
    jb __wfm_upper_8_width
    mov ebp, 4
__wfm_upper_8_width:
    cmp ebp, edx
    jbe __wfm_upper_8_bounded
    mov ebp, 1
__wfm_upper_8_bounded:
    sub edx, ebp
    test ebx, ebx
    je __wfm_upper_8_copy
    add rsi, rbp
    dec ebx
    jmp __wfm_upper_8_loop
__wfm_upper_8_copy:
    movzx eax, byte ptr [rsi]
    mov byte ptr [rdi], al
    inc rsi
    inc rdi
    dec ebp
    jne __wfm_upper_8_copy
    dec ecx
    jmp __wfm_upper_8_loop
__wfm_upper_8_done:
    mov byte ptr [rdi], 0
    sub rdi, qword ptr [__dbase_wfm_mem___string_arg_8_ptr]
    mov dword ptr [__dbase_wfm_mem___string_arg_8_len], edi
    mov dword ptr [__dbase_wfm_mem___string_arg_8_type], 3
    pop rbp
    pop rdi
    pop rsi
    pop rbx
    mov eax, dword ptr [__dbase_wfm_mem___string_arg_8_len]
    mov ecx, eax
    add eax, ecx
    add eax, ecx
    add eax, 1
    mov ecx, eax
    call __dbase_malloc
    test rax, rax
    jne __wfm_upper_11_allocated
    mov ecx, 8
    call ExitProcess
__wfm_upper_11_allocated:
    mov qword ptr [__dbase_wfm_mem___string_arg_11_ptr], rax
    mov rcx, qword ptr [__dbase_wfm_mem___string_arg_11_ptr]
    mov edx, dword ptr [__dbase_wfm_mem___string_arg_8_len]
    mov eax, edx
    add edx, eax
    add edx, eax
    add edx, 1
    mov r8, qword ptr [__dbase_wfm_mem___string_arg_8_ptr]
    mov r9d, dword ptr [__dbase_wfm_mem___string_arg_8_len]
    call __dbase_upper_buffer
    cmp eax, -1
    jne __wfm_upper_11_converted
    mov ecx, 13
    call ExitProcess
__wfm_upper_11_converted:
    mov dword ptr [__dbase_wfm_mem___string_arg_11_len], eax
    mov dword ptr [__dbase_wfm_mem___string_arg_11_type], 3
    ; ? "5: " + !($(SpeicherVar, 8, 6))
    mov rcx, __dbase_wfm_output_text_96
    mov edx, 3
    mov r8d, 0
    call DBaseQtConsoleWrite
    cmp dword ptr [__dbase_wfm_mem___string_arg_11_type], 0
    je __dbase_wfm_print_null_12
    cmp dword ptr [__dbase_wfm_mem___string_arg_11_type], 3
    je __dbase_wfm_print_string_12
    cmp dword ptr [__dbase_wfm_mem___string_arg_11_type], 4
    je __dbase_wfm_print_object_12
    cmp dword ptr [__dbase_wfm_mem___string_arg_11_type], 1
    je __dbase_wfm_print_number_12
    cmp dword ptr [__dbase_wfm_mem___string_arg_11_type], 2
    je __dbase_wfm_print_number_12
    jmp __dbase_wfm_print_null_12
__dbase_wfm_print_number_12:
    fld qword ptr [__dbase_wfm_mem___string_arg_11_num]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, qword ptr [__dbase_format_buffer]
    call __dbase_gcvt
    mov rcx, qword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_wfm_strlen_6:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_wfm_strlen_done_6
    inc rcx
    inc edx
    jmp __dbase_wfm_strlen_6
__dbase_wfm_strlen_done_6:
    mov rcx, qword ptr [__dbase_format_buffer]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_12
__dbase_wfm_print_string_12:
    mov rcx, qword ptr [__dbase_wfm_mem___string_arg_11_ptr]
    test rcx, rcx
    je __dbase_wfm_print_null_12
    mov edx, dword ptr [__dbase_wfm_mem___string_arg_11_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_12
__dbase_wfm_print_object_12:
    mov rax, qword ptr [__dbase_wfm_mem___string_arg_11_ptr]
    test rax, rax
    je __dbase_wfm_print_null_12
    mov rcx, __dbase_wfm_output_text_98
    mov edx, 8
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_12
__dbase_wfm_print_null_12:
    mov rcx, __dbase_wfm_output_text_97
    mov edx, 6
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_print_done_12:
    ; TestAndNotXor()
    call __dbase_wfm_proc_TestAndNotXor
    mov ecx, 19
    call GetSystemMetrics
    test eax, eax
    setne al
    movzx eax, al
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fstp qword ptr [__dbase_wfm_mem_HatMaus_num]
    mov dword ptr [__dbase_wfm_mem_HatMaus_type], 1
    mov dword ptr [__dbase_wfm_mem_HatMaus_len], 0
    mov qword ptr [__dbase_wfm_mem_HatMaus_ptr], 0
    ; IF HatMaus = 1
    fld qword ptr [__dbase_wfm_mem_HatMaus_num]
    fld qword ptr [__dbase_wfm_numconst_4]
    fucomip st0, st1
    fstp st0
    jne __dbase_wfm_flow_if_false_5
    ; ? "Eine Maus ist vorhanden."
    mov rcx, __dbase_wfm_output_text_99
    mov edx, 24
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_flow_if_end_6
__dbase_wfm_flow_if_false_5:
    ; ? "Keine Maus erkannt."
    mov rcx, __dbase_wfm_output_text_100
    mov edx, 19
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_flow_if_end_6:
    ; IF ismouse() .AND. HatMaus = 1
    mov ecx, 19
    call GetSystemMetrics
    test eax, eax
    setne al
    movzx eax, al
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fldz
    fucomip st0, st1
    fstp st0
    je __dbase_wfm_flow_if_false_7
    fld qword ptr [__dbase_wfm_mem_HatMaus_num]
    fld qword ptr [__dbase_wfm_numconst_5]
    fucomip st0, st1
    fstp st0
    jne __dbase_wfm_flow_if_false_7
    ; ? "Maus kann verwendet werden."
    mov rcx, __dbase_wfm_output_text_101
    mov edx, 27
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_flow_if_false_7:
__dbase_wfm_flow_if_end_8:
    mov ecx, 19
    call GetSystemMetrics
    test eax, eax
    setne al
    movzx eax, al
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fstp qword ptr [__dbase_wfm_mem___wfm_ismouse_print_num]
    mov dword ptr [__dbase_wfm_mem___wfm_ismouse_print_type], 1
    mov dword ptr [__dbase_wfm_mem___wfm_ismouse_print_len], 0
    mov qword ptr [__dbase_wfm_mem___wfm_ismouse_print_ptr], 0
    ; ? ismouse()
    cmp dword ptr [__dbase_wfm_mem___wfm_ismouse_print_type], 0
    je __dbase_wfm_print_null_13
    cmp dword ptr [__dbase_wfm_mem___wfm_ismouse_print_type], 3
    je __dbase_wfm_print_string_13
    cmp dword ptr [__dbase_wfm_mem___wfm_ismouse_print_type], 4
    je __dbase_wfm_print_object_13
    cmp dword ptr [__dbase_wfm_mem___wfm_ismouse_print_type], 1
    je __dbase_wfm_print_number_13
    cmp dword ptr [__dbase_wfm_mem___wfm_ismouse_print_type], 2
    je __dbase_wfm_print_number_13
    jmp __dbase_wfm_print_null_13
__dbase_wfm_print_number_13:
    fld qword ptr [__dbase_wfm_mem___wfm_ismouse_print_num]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, qword ptr [__dbase_format_buffer]
    call __dbase_gcvt
    mov rcx, qword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_wfm_strlen_7:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_wfm_strlen_done_7
    inc rcx
    inc edx
    jmp __dbase_wfm_strlen_7
__dbase_wfm_strlen_done_7:
    mov rcx, qword ptr [__dbase_format_buffer]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_13
__dbase_wfm_print_string_13:
    mov rcx, qword ptr [__dbase_wfm_mem___wfm_ismouse_print_ptr]
    test rcx, rcx
    je __dbase_wfm_print_null_13
    mov edx, dword ptr [__dbase_wfm_mem___wfm_ismouse_print_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_13
__dbase_wfm_print_object_13:
    mov rax, qword ptr [__dbase_wfm_mem___wfm_ismouse_print_ptr]
    test rax, rax
    je __dbase_wfm_print_null_13
    mov rcx, __dbase_wfm_output_text_103
    mov edx, 8
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_13
__dbase_wfm_print_null_13:
    mov rcx, __dbase_wfm_output_text_102
    mov edx, 6
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_print_done_13:
    sub rsp, 64
    mov dword ptr [rsp+32], 0
    mov qword ptr [rsp+40], 0
    mov dword ptr [rsp+48], 0
    xor ecx, ecx
    lea rdx, [rsp+32]
    mov r8d, 16
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_9_done
    mov edx, dword ptr [rsp+32]
    test edx, edx
    jz __dbase_wfm_flow_iskeyboard_9_done
    cmp edx, 268435455
    ja __dbase_wfm_flow_iskeyboard_9_done
    shl rdx, 4
    xor ecx, ecx
    mov r8d, 12288
    mov r9d, 4
    call VirtualAlloc
    test rax, rax
    jz __dbase_wfm_flow_iskeyboard_9_done
    mov qword ptr [rsp+40], rax
    mov rcx, rax
    lea rdx, [rsp+32]
    mov r8d, 16
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_9_release
    test eax, eax
    jz __dbase_wfm_flow_iskeyboard_9_release
    mov r10d, eax
    mov r11, qword ptr [rsp+40]
__dbase_wfm_flow_iskeyboard_9_scan:
    cmp dword ptr [r11+8], 1
    je __dbase_wfm_flow_iskeyboard_9_present
    add r11, 16
    dec r10d
    jnz __dbase_wfm_flow_iskeyboard_9_scan
    jmp __dbase_wfm_flow_iskeyboard_9_release
__dbase_wfm_flow_iskeyboard_9_present:
    mov dword ptr [rsp+48], 1
__dbase_wfm_flow_iskeyboard_9_release:
    mov rcx, qword ptr [rsp+40]
    xor edx, edx
    mov r8d, 32768
    call VirtualFree
__dbase_wfm_flow_iskeyboard_9_done:
    mov eax, dword ptr [rsp+48]
    add rsp, 64
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fstp qword ptr [__dbase_wfm_mem_HatTastatur_num]
    mov dword ptr [__dbase_wfm_mem_HatTastatur_type], 1
    mov dword ptr [__dbase_wfm_mem_HatTastatur_len], 0
    mov qword ptr [__dbase_wfm_mem_HatTastatur_ptr], 0
    ; IF HatTastatur = 1
    fld qword ptr [__dbase_wfm_mem_HatTastatur_num]
    fld qword ptr [__dbase_wfm_numconst_6]
    fucomip st0, st1
    fstp st0
    jne __dbase_wfm_flow_if_false_10
    ; ? "Eine Tastatur ist vorhanden."
    mov rcx, __dbase_wfm_output_text_104
    mov edx, 28
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_flow_if_end_11
__dbase_wfm_flow_if_false_10:
    ; ? "Keine Tastatur erkannt."
    mov rcx, __dbase_wfm_output_text_105
    mov edx, 23
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_flow_if_end_11:
    ; IF iskeyboard() .AND. ismouse()
    sub rsp, 64
    mov dword ptr [rsp+32], 0
    mov qword ptr [rsp+40], 0
    mov dword ptr [rsp+48], 0
    xor ecx, ecx
    lea rdx, [rsp+32]
    mov r8d, 16
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_14_done
    mov edx, dword ptr [rsp+32]
    test edx, edx
    jz __dbase_wfm_flow_iskeyboard_14_done
    cmp edx, 268435455
    ja __dbase_wfm_flow_iskeyboard_14_done
    shl rdx, 4
    xor ecx, ecx
    mov r8d, 12288
    mov r9d, 4
    call VirtualAlloc
    test rax, rax
    jz __dbase_wfm_flow_iskeyboard_14_done
    mov qword ptr [rsp+40], rax
    mov rcx, rax
    lea rdx, [rsp+32]
    mov r8d, 16
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_14_release
    test eax, eax
    jz __dbase_wfm_flow_iskeyboard_14_release
    mov r10d, eax
    mov r11, qword ptr [rsp+40]
__dbase_wfm_flow_iskeyboard_14_scan:
    cmp dword ptr [r11+8], 1
    je __dbase_wfm_flow_iskeyboard_14_present
    add r11, 16
    dec r10d
    jnz __dbase_wfm_flow_iskeyboard_14_scan
    jmp __dbase_wfm_flow_iskeyboard_14_release
__dbase_wfm_flow_iskeyboard_14_present:
    mov dword ptr [rsp+48], 1
__dbase_wfm_flow_iskeyboard_14_release:
    mov rcx, qword ptr [rsp+40]
    xor edx, edx
    mov r8d, 32768
    call VirtualFree
__dbase_wfm_flow_iskeyboard_14_done:
    mov eax, dword ptr [rsp+48]
    add rsp, 64
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fldz
    fucomip st0, st1
    fstp st0
    je __dbase_wfm_flow_if_false_12
    mov ecx, 19
    call GetSystemMetrics
    test eax, eax
    setne al
    movzx eax, al
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fldz
    fucomip st0, st1
    fstp st0
    je __dbase_wfm_flow_if_false_12
    ; ? "Maus und Tastatur sind vorhanden."
    mov rcx, __dbase_wfm_output_text_106
    mov edx, 33
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_flow_if_false_12:
__dbase_wfm_flow_if_end_13:
    ; IF .NOT. iskeyboard()
    sub rsp, 64
    mov dword ptr [rsp+32], 0
    mov qword ptr [rsp+40], 0
    mov dword ptr [rsp+48], 0
    xor ecx, ecx
    lea rdx, [rsp+32]
    mov r8d, 16
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_18_done
    mov edx, dword ptr [rsp+32]
    test edx, edx
    jz __dbase_wfm_flow_iskeyboard_18_done
    cmp edx, 268435455
    ja __dbase_wfm_flow_iskeyboard_18_done
    shl rdx, 4
    xor ecx, ecx
    mov r8d, 12288
    mov r9d, 4
    call VirtualAlloc
    test rax, rax
    jz __dbase_wfm_flow_iskeyboard_18_done
    mov qword ptr [rsp+40], rax
    mov rcx, rax
    lea rdx, [rsp+32]
    mov r8d, 16
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_18_release
    test eax, eax
    jz __dbase_wfm_flow_iskeyboard_18_release
    mov r10d, eax
    mov r11, qword ptr [rsp+40]
__dbase_wfm_flow_iskeyboard_18_scan:
    cmp dword ptr [r11+8], 1
    je __dbase_wfm_flow_iskeyboard_18_present
    add r11, 16
    dec r10d
    jnz __dbase_wfm_flow_iskeyboard_18_scan
    jmp __dbase_wfm_flow_iskeyboard_18_release
__dbase_wfm_flow_iskeyboard_18_present:
    mov dword ptr [rsp+48], 1
__dbase_wfm_flow_iskeyboard_18_release:
    mov rcx, qword ptr [rsp+40]
    xor edx, edx
    mov r8d, 32768
    call VirtualFree
__dbase_wfm_flow_iskeyboard_18_done:
    mov eax, dword ptr [rsp+48]
    add rsp, 64
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fldz
    fucomip st0, st1
    fstp st0
    je __dbase_wfm_flow_not_true_17
    jmp __dbase_wfm_flow_if_false_15
__dbase_wfm_flow_not_true_17:
    ; ? "Keine Tastatur gefunden."
    mov rcx, __dbase_wfm_output_text_107
    mov edx, 24
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_flow_if_false_15:
__dbase_wfm_flow_if_end_16:
    sub rsp, 64
    mov dword ptr [rsp+32], 0
    mov qword ptr [rsp+40], 0
    mov dword ptr [rsp+48], 0
    xor ecx, ecx
    lea rdx, [rsp+32]
    mov r8d, 16
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_19_done
    mov edx, dword ptr [rsp+32]
    test edx, edx
    jz __dbase_wfm_flow_iskeyboard_19_done
    cmp edx, 268435455
    ja __dbase_wfm_flow_iskeyboard_19_done
    shl rdx, 4
    xor ecx, ecx
    mov r8d, 12288
    mov r9d, 4
    call VirtualAlloc
    test rax, rax
    jz __dbase_wfm_flow_iskeyboard_19_done
    mov qword ptr [rsp+40], rax
    mov rcx, rax
    lea rdx, [rsp+32]
    mov r8d, 16
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_19_release
    test eax, eax
    jz __dbase_wfm_flow_iskeyboard_19_release
    mov r10d, eax
    mov r11, qword ptr [rsp+40]
__dbase_wfm_flow_iskeyboard_19_scan:
    cmp dword ptr [r11+8], 1
    je __dbase_wfm_flow_iskeyboard_19_present
    add r11, 16
    dec r10d
    jnz __dbase_wfm_flow_iskeyboard_19_scan
    jmp __dbase_wfm_flow_iskeyboard_19_release
__dbase_wfm_flow_iskeyboard_19_present:
    mov dword ptr [rsp+48], 1
__dbase_wfm_flow_iskeyboard_19_release:
    mov rcx, qword ptr [rsp+40]
    xor edx, edx
    mov r8d, 32768
    call VirtualFree
__dbase_wfm_flow_iskeyboard_19_done:
    mov eax, dword ptr [rsp+48]
    add rsp, 64
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fstp qword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_num]
    mov dword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_type], 1
    mov dword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_len], 0
    mov qword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_ptr], 0
    ; ? iskeyboard()
    cmp dword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_type], 0
    je __dbase_wfm_print_null_14
    cmp dword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_type], 3
    je __dbase_wfm_print_string_14
    cmp dword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_type], 4
    je __dbase_wfm_print_object_14
    cmp dword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_type], 1
    je __dbase_wfm_print_number_14
    cmp dword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_type], 2
    je __dbase_wfm_print_number_14
    jmp __dbase_wfm_print_null_14
__dbase_wfm_print_number_14:
    fld qword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_num]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, qword ptr [__dbase_format_buffer]
    call __dbase_gcvt
    mov rcx, qword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_wfm_strlen_8:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_wfm_strlen_done_8
    inc rcx
    inc edx
    jmp __dbase_wfm_strlen_8
__dbase_wfm_strlen_done_8:
    mov rcx, qword ptr [__dbase_format_buffer]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_14
__dbase_wfm_print_string_14:
    mov rcx, qword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_ptr]
    test rcx, rcx
    je __dbase_wfm_print_null_14
    mov edx, dword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_14
__dbase_wfm_print_object_14:
    mov rax, qword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_ptr]
    test rax, rax
    je __dbase_wfm_print_null_14
    mov rcx, __dbase_wfm_output_text_109
    mov edx, 8
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_print_done_14
__dbase_wfm_print_null_14:
    mov rcx, __dbase_wfm_output_text_108
    mov edx, 6
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_print_done_14:
    jmp __dbase_wfm_flow_method_exit_4
__dbase_wfm_flow_method_exit_4:
    add rsp, 40
    ret
; END WFM PROCEDURE/FUNCTION: PushButton1_onClick


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: TestAndNotXor
; ------------------------------------------------------------
__dbase_wfm_proc_TestAndNotXor:
    sub rsp, 40
    ; IF A > 0 .AND. C < 10
    fld qword ptr [__dbase_wfm_mem_A_num]
    fld qword ptr [__dbase_wfm_numconst_7]
    fucomip st0, st1
    fstp st0
    jae __dbase_wfm_flow_if_false_21
    fld qword ptr [__dbase_wfm_mem_C_num]
    fld qword ptr [__dbase_wfm_numconst_8]
    fucomip st0, st1
    fstp st0
    jbe __dbase_wfm_flow_if_false_21
    ; ? "Beide Bedingungen erfüllt"
    mov rcx, __dbase_wfm_output_text_110
    mov edx, 26
    mov r8d, 1
    call DBaseQtConsoleWrite
    jmp __dbase_wfm_flow_if_end_22
__dbase_wfm_flow_if_false_21:
    ; ? "Bedingung nicht erfüllt"
    mov rcx, __dbase_wfm_output_text_111
    mov edx, 24
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_flow_if_end_22:
    ; IF .NOT. (A = 0 .OR. C >= 10)
    fld qword ptr [__dbase_wfm_mem_A_num]
    fld qword ptr [__dbase_wfm_numconst_9]
    fucomip st0, st1
    fstp st0
    jne __dbase_wfm_flow_not_true_27
    jmp __dbase_wfm_flow_or_true_26
__dbase_wfm_flow_not_true_27:
    fld qword ptr [__dbase_wfm_mem_C_num]
    fld qword ptr [__dbase_wfm_numconst_10]
    fucomip st0, st1
    fstp st0
    ja __dbase_wfm_flow_not_true_25
__dbase_wfm_flow_or_true_26:
    jmp __dbase_wfm_flow_if_false_23
__dbase_wfm_flow_not_true_25:
    ; ? "NOT und OR funktionieren"
    mov rcx, __dbase_wfm_output_text_112
    mov edx, 24
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_flow_if_false_23:
__dbase_wfm_flow_if_end_24:
    ; IF (A > 0) .XOR. (C < 0)
    fld qword ptr [__dbase_wfm_mem_A_num]
    fld qword ptr [__dbase_wfm_numconst_11]
    fucomip st0, st1
    fstp st0
    jae __dbase_wfm_flow_xor_left_false_30
    fld qword ptr [__dbase_wfm_mem_C_num]
    fld qword ptr [__dbase_wfm_numconst_12]
    fucomip st0, st1
    fstp st0
    jbe __dbase_wfm_flow_not_true_32
    jmp __dbase_wfm_flow_if_false_28
__dbase_wfm_flow_not_true_32:
    jmp __dbase_wfm_flow_xor_done_31
__dbase_wfm_flow_xor_left_false_30:
    fld qword ptr [__dbase_wfm_mem_C_num]
    fld qword ptr [__dbase_wfm_numconst_13]
    fucomip st0, st1
    fstp st0
    jbe __dbase_wfm_flow_if_false_28
__dbase_wfm_flow_xor_done_31:
    ; ? "Genau eine Bedingung ist wahr"
    mov rcx, __dbase_wfm_output_text_113
    mov edx, 29
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_flow_if_false_28:
__dbase_wfm_flow_if_end_29:
    jmp __dbase_wfm_flow_method_exit_20
__dbase_wfm_flow_method_exit_20:
    add rsp, 40
    ret
; END WFM PROCEDURE/FUNCTION: TestAndNotXor

; Stage 224: local packed WFM property decoder (PE32+)
.section .text
__dbase_wfm_set_properties_packed:
    sub rsp, 72
    mov qword ptr [rsp+40], rcx
    mov qword ptr [rsp+48], rdx
    mov dword ptr [rsp+56], r8d
__dbase_wfm_set_properties_packed_loop:
    cmp dword ptr [rsp+56], 0
    jle __dbase_wfm_set_properties_packed_done
    mov r10, qword ptr [rsp+48]
    mov rcx, qword ptr [rsp+40]
    movzx eax, byte ptr [r10]
    mov r9, qword ptr [r10+1]
    movzx r8d, byte ptr [r10+9]
    mov rdx, qword ptr [r10+10]
    mov dword ptr [rsp+32], eax
    call DBaseQtWidgetSetProperty
    mov r10, qword ptr [rsp+48]
    add r10, 18
    mov qword ptr [rsp+48], r10
    mov eax, dword ptr [rsp+56]
    dec eax
    mov dword ptr [rsp+56], eax
    jmp __dbase_wfm_set_properties_packed_loop
__dbase_wfm_set_properties_packed_done:
    add rsp, 72
    ret

; Stage 127 WFM initialized data
.section .data
__dbase_wfm_qt_output_marker:
    db 68, 54, 52, 68, 66, 65, 83, 69, 95, 87, 70, 77, 95, 81, 84, 95, 79, 85, 84, 80, 85, 84, 95, 86, 49, 0
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
    db 66, 97, 99, 107, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_6:
    db 35, 56, 48, 48, 97, 49, 52, 49, 101, 92, 48
__dbase_wfm_text_7:
    db 70, 111, 114, 101, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_8:
    db 35, 102, 102, 102, 102, 102, 102, 92, 48
__dbase_wfm_text_9:
    db 66, 114, 117, 115, 104, 71, 114, 97, 100, 105, 101, 110, 116, 92, 48
__dbase_wfm_text_10:
    db 108, 105, 110, 101, 97, 114, 95, 104, 111, 114, 105, 122, 111, 110, 116, 97, 108, 92, 48
__dbase_wfm_text_11:
    db 66, 114, 117, 115, 104, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_12:
    db 55, 92, 48
__dbase_wfm_text_13:
    db 66, 114, 117, 115, 104, 67, 117, 116, 87, 105, 100, 116, 104, 92, 48
__dbase_wfm_text_14:
    db 54, 53, 92, 48
__dbase_wfm_text_15:
    db 66, 114, 117, 115, 104, 67, 117, 116, 72, 101, 105, 103, 104, 116, 92, 48
__dbase_wfm_text_16:
    db 52, 53, 92, 48
__dbase_wfm_text_17:
    db 66, 111, 114, 100, 101, 114, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_18:
    db 115, 111, 108, 105, 100, 92, 48
__dbase_wfm_text_19:
    db 66, 111, 114, 100, 101, 114, 87, 105, 100, 116, 104, 92, 48
__dbase_wfm_text_20:
    db 50, 92, 48
__dbase_wfm_text_21:
    db 66, 111, 114, 100, 101, 114, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_22:
    db 35, 56, 48, 56, 48, 56, 48, 92, 48
__dbase_wfm_text_23:
    db 83, 104, 97, 100, 111, 119, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_24:
    db 35, 49, 48, 49, 48, 49, 48, 92, 48
__dbase_wfm_text_25:
    db 66, 111, 114, 100, 101, 114, 82, 111, 117, 110, 100, 101, 100, 84, 76, 92, 48
__dbase_wfm_text_26:
    db 49, 92, 48
__dbase_wfm_text_27:
    db 66, 111, 114, 100, 101, 114, 82, 111, 117, 110, 100, 101, 100, 84, 82, 92, 48
__dbase_wfm_text_28:
    db 66, 111, 114, 100, 101, 114, 82, 111, 117, 110, 100, 101, 100, 66, 76, 92, 48
__dbase_wfm_text_29:
    db 51, 92, 48
__dbase_wfm_text_30:
    db 66, 111, 114, 100, 101, 114, 82, 111, 117, 110, 100, 101, 100, 66, 82, 92, 48
__dbase_wfm_text_31:
    db 52, 92, 48
__dbase_wfm_text_32:
    db 66, 111, 114, 100, 101, 114, 76, 101, 102, 116, 92, 48
__dbase_wfm_text_33:
    db 46, 84, 46, 92, 48
__dbase_wfm_text_34:
    db 66, 111, 114, 100, 101, 114, 76, 101, 102, 116, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_35:
    db 100, 111, 117, 98, 108, 101, 92, 48
__dbase_wfm_text_36:
    db 66, 111, 114, 100, 101, 114, 76, 101, 102, 116, 83, 105, 122, 101, 92, 48
__dbase_wfm_text_37:
    db 66, 111, 114, 100, 101, 114, 76, 101, 102, 116, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_38:
    db 35, 102, 102, 48, 48, 48, 48, 92, 48
__dbase_wfm_text_39:
    db 66, 111, 114, 100, 101, 114, 84, 111, 112, 92, 48
__dbase_wfm_text_40:
    db 66, 111, 114, 100, 101, 114, 84, 111, 112, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_41:
    db 66, 111, 114, 100, 101, 114, 84, 111, 112, 83, 105, 122, 101, 92, 48
__dbase_wfm_text_42:
    db 66, 111, 114, 100, 101, 114, 84, 111, 112, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_43:
    db 66, 111, 114, 100, 101, 114, 82, 105, 103, 104, 116, 92, 48
__dbase_wfm_text_44:
    db 66, 111, 114, 100, 101, 114, 82, 105, 103, 104, 116, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_45:
    db 66, 111, 114, 100, 101, 114, 82, 105, 103, 104, 116, 83, 105, 122, 101, 92, 48
__dbase_wfm_text_46:
    db 66, 111, 114, 100, 101, 114, 82, 105, 103, 104, 116, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_47:
    db 66, 111, 114, 100, 101, 114, 66, 111, 116, 116, 111, 109, 92, 48
__dbase_wfm_text_48:
    db 66, 111, 114, 100, 101, 114, 66, 111, 116, 116, 111, 109, 83, 116, 121, 108, 101, 92, 48
__dbase_wfm_text_49:
    db 66, 111, 114, 100, 101, 114, 66, 111, 116, 116, 111, 109, 83, 105, 122, 101, 92, 48
__dbase_wfm_text_50:
    db 66, 111, 114, 100, 101, 114, 66, 111, 116, 116, 111, 109, 67, 111, 108, 111, 114, 92, 48
__dbase_wfm_text_51:
    db 70, 111, 110, 116, 65, 108, 112, 104, 97, 92, 48
__dbase_wfm_text_52:
    db 50, 48, 48, 92, 48
__dbase_wfm_text_53:
    db 70, 111, 110, 116, 66, 97, 99, 107, 103, 114, 111, 117, 110, 100, 92, 48
__dbase_wfm_text_54:
    db 35, 50, 48, 50, 48, 50, 48, 92, 48
__dbase_wfm_text_55:
    db 70, 111, 110, 116, 70, 111, 114, 101, 103, 114, 111, 117, 110, 100, 92, 48
__dbase_wfm_text_56:
    db 35, 101, 101, 101, 101, 101, 101, 92, 48
__dbase_wfm_text_57:
    db 80, 85, 83, 72, 66, 85, 84, 84, 79, 78, 92, 48
__dbase_wfm_text_58:
    db 66, 117, 116, 116, 111, 110, 49, 92, 48
__dbase_wfm_text_59:
    db 65, 114, 105, 97, 108, 92, 48
__dbase_wfm_text_60:
    db 80, 117, 115, 104, 66, 117, 116, 116, 111, 110, 49, 92, 48
__dbase_wfm_text_61:
    db 35, 51, 51, 51, 51, 51, 51, 92, 48
__dbase_wfm_text_62:
    db 35, 101, 98, 101, 101, 102, 50, 92, 48
__dbase_wfm_text_63:
    db 110, 111, 110, 101, 92, 48
__dbase_wfm_text_64:
    db 48, 92, 48
__dbase_wfm_text_65:
    db 56, 48, 92, 48
__dbase_wfm_text_66:
    db 57, 48, 92, 48
__dbase_wfm_text_67:
    db 100, 97, 115, 104, 101, 100, 92, 48
__dbase_wfm_text_68:
    db 35, 53, 53, 102, 102, 55, 102, 92, 48
__dbase_wfm_text_69:
    db 35, 48, 48, 48, 48, 48, 48, 92, 48
__dbase_wfm_text_70:
    db 46, 70, 46, 92, 48
__dbase_wfm_text_71:
    db 100, 111, 116, 116, 101, 100, 92, 48
__dbase_wfm_text_72:
    db 49, 50, 51, 92, 48
__dbase_wfm_text_73:
    db 35, 49, 49, 49, 49, 49, 49, 92, 48
__dbase_wfm_text_74:
    db 79, 110, 67, 108, 105, 99, 107, 92, 48
__dbase_wfm_output_text_75:
    db 112, 49, 32, 61, 32
__dbase_wfm_output_text_76:
    db 60, 110, 117, 108, 108, 62
__dbase_wfm_output_text_77:
    db 60, 111, 98, 106, 101, 99, 116, 62
__dbase_wfm_output_text_78:
    db 112, 50, 32, 61, 32
__dbase_wfm_output_text_79:
    db 60, 110, 117, 108, 108, 62
__dbase_wfm_output_text_80:
    db 60, 111, 98, 106, 101, 99, 116, 62
__dbase_wfm_output_text_81:
    db 60, 110, 117, 108, 108, 62
__dbase_wfm_output_text_82:
    db 60, 111, 98, 106, 101, 99, 116, 62
__dbase_wfm_output_text_83:
    db 60, 110, 117, 108, 108, 62
__dbase_wfm_output_text_84:
    db 60, 111, 98, 106, 101, 99, 116, 62
__dbase_wfm_output_text_85:
    db 49, 58, 32
__dbase_wfm_output_text_86:
    db 49, 48, 49, 46, 52, 50
__dbase_wfm_output_text_87:
    db 50, 58, 32
__dbase_wfm_output_text_88:
    db 49, 48, 49
__dbase_wfm_output_text_89:
    db 51, 58, 32
__dbase_wfm_output_text_90:
    db 60, 110, 117, 108, 108, 62
__dbase_wfm_output_text_91:
    db 60, 111, 98, 106, 101, 99, 116, 62
__dbase_wfm_output_text_92:
    db 90, 101, 105, 99, 104, 101, 110, 115, 116, 114, 105, 110, 103
__dbase_wfm_output_text_93:
    db 52, 58, 32
__dbase_wfm_output_text_94:
    db 60, 110, 117, 108, 108, 62
__dbase_wfm_output_text_95:
    db 60, 111, 98, 106, 101, 99, 116, 62
__dbase_wfm_output_text_96:
    db 53, 58, 32
__dbase_wfm_output_text_97:
    db 60, 110, 117, 108, 108, 62
__dbase_wfm_output_text_98:
    db 60, 111, 98, 106, 101, 99, 116, 62
__dbase_wfm_output_text_99:
    db 69, 105, 110, 101, 32, 77, 97, 117, 115, 32, 105, 115, 116, 32, 118, 111, 114, 104, 97, 110, 100, 101, 110, 46
__dbase_wfm_output_text_100:
    db 75, 101, 105, 110, 101, 32, 77, 97, 117, 115, 32, 101, 114, 107, 97, 110, 110, 116, 46
__dbase_wfm_output_text_101:
    db 77, 97, 117, 115, 32, 107, 97, 110, 110, 32, 118, 101, 114, 119, 101, 110, 100, 101, 116, 32, 119, 101, 114, 100, 101, 110, 46
__dbase_wfm_output_text_102:
    db 60, 110, 117, 108, 108, 62
__dbase_wfm_output_text_103:
    db 60, 111, 98, 106, 101, 99, 116, 62
__dbase_wfm_output_text_104:
    db 69, 105, 110, 101, 32, 84, 97, 115, 116, 97, 116, 117, 114, 32, 105, 115, 116, 32, 118, 111, 114, 104, 97, 110, 100, 101, 110, 46
__dbase_wfm_output_text_105:
    db 75, 101, 105, 110, 101, 32, 84, 97, 115, 116, 97, 116, 117, 114, 32, 101, 114, 107, 97, 110, 110, 116, 46
__dbase_wfm_output_text_106:
    db 77, 97, 117, 115, 32, 117, 110, 100, 32, 84, 97, 115, 116, 97, 116, 117, 114, 32, 115, 105, 110, 100, 32, 118, 111, 114, 104, 97, 110, 100, 101, 110, 46
__dbase_wfm_output_text_107:
    db 75, 101, 105, 110, 101, 32, 84, 97, 115, 116, 97, 116, 117, 114, 32, 103, 101, 102, 117, 110, 100, 101, 110, 46
__dbase_wfm_output_text_108:
    db 60, 110, 117, 108, 108, 62
__dbase_wfm_output_text_109:
    db 60, 111, 98, 106, 101, 99, 116, 62
__dbase_wfm_output_text_110:
    db 66, 101, 105, 100, 101, 32, 66, 101, 100, 105, 110, 103, 117, 110, 103, 101, 110, 32, 101, 114, 102, 195, 188, 108, 108, 116
__dbase_wfm_output_text_111:
    db 66, 101, 100, 105, 110, 103, 117, 110, 103, 32, 110, 105, 99, 104, 116, 32, 101, 114, 102, 195, 188, 108, 108, 116
__dbase_wfm_output_text_112:
    db 78, 79, 84, 32, 117, 110, 100, 32, 79, 82, 32, 102, 117, 110, 107, 116, 105, 111, 110, 105, 101, 114, 101, 110
__dbase_wfm_output_text_113:
    db 71, 101, 110, 97, 117, 32, 101, 105, 110, 101, 32, 66, 101, 100, 105, 110, 103, 117, 110, 103, 32, 105, 115, 116, 32, 119, 97, 104, 114

; Stage 223: compact WFM property blocks
; record = db valueLength, ptr valuePtr, db nameLength, ptr namePtr
__dbase_wfm_property_table_0:
    db 4
    dq __dbase_wfm_text_3
    db 4
    dq __dbase_wfm_text_2
    db 5
    dq __dbase_wfm_text_0
    db 4
    dq __dbase_wfm_text_4
    db 9
    dq __dbase_wfm_text_6
    db 9
    dq __dbase_wfm_text_5
    db 7
    dq __dbase_wfm_text_8
    db 9
    dq __dbase_wfm_text_7
    db 17
    dq __dbase_wfm_text_10
    db 13
    dq __dbase_wfm_text_9
    db 1
    dq __dbase_wfm_text_12
    db 10
    dq __dbase_wfm_text_11
    db 2
    dq __dbase_wfm_text_14
    db 13
    dq __dbase_wfm_text_13
    db 2
    dq __dbase_wfm_text_16
    db 14
    dq __dbase_wfm_text_15
    db 5
    dq __dbase_wfm_text_18
    db 11
    dq __dbase_wfm_text_17
    db 1
    dq __dbase_wfm_text_20
    db 11
    dq __dbase_wfm_text_19
    db 7
    dq __dbase_wfm_text_22
    db 11
    dq __dbase_wfm_text_21
    db 7
    dq __dbase_wfm_text_24
    db 11
    dq __dbase_wfm_text_23
    db 1
    dq __dbase_wfm_text_26
    db 15
    dq __dbase_wfm_text_25
    db 1
    dq __dbase_wfm_text_20
    db 15
    dq __dbase_wfm_text_27
    db 1
    dq __dbase_wfm_text_29
    db 15
    dq __dbase_wfm_text_28
    db 1
    dq __dbase_wfm_text_31
    db 15
    dq __dbase_wfm_text_30
    db 3
    dq __dbase_wfm_text_33
    db 10
    dq __dbase_wfm_text_32
    db 6
    dq __dbase_wfm_text_35
    db 15
    dq __dbase_wfm_text_34
    db 1
    dq __dbase_wfm_text_29
    db 14
    dq __dbase_wfm_text_36
    db 7
    dq __dbase_wfm_text_38
    db 15
    dq __dbase_wfm_text_37
    db 3
    dq __dbase_wfm_text_33
    db 9
    dq __dbase_wfm_text_39
    db 5
    dq __dbase_wfm_text_18
    db 14
    dq __dbase_wfm_text_40
    db 1
    dq __dbase_wfm_text_20
    db 13
    dq __dbase_wfm_text_41
    db 7
    dq __dbase_wfm_text_22
    db 14
    dq __dbase_wfm_text_42
    db 3
    dq __dbase_wfm_text_33
    db 11
    dq __dbase_wfm_text_43
    db 5
    dq __dbase_wfm_text_18
    db 16
    dq __dbase_wfm_text_44
    db 1
    dq __dbase_wfm_text_20
    db 15
    dq __dbase_wfm_text_45
    db 7
    dq __dbase_wfm_text_22
    db 16
    dq __dbase_wfm_text_46
    db 3
    dq __dbase_wfm_text_33
    db 12
    dq __dbase_wfm_text_47
    db 5
    dq __dbase_wfm_text_18
    db 17
    dq __dbase_wfm_text_48
    db 1
    dq __dbase_wfm_text_20
    db 16
    dq __dbase_wfm_text_49
    db 7
    dq __dbase_wfm_text_22
    db 17
    dq __dbase_wfm_text_50
    db 3
    dq __dbase_wfm_text_52
    db 9
    dq __dbase_wfm_text_51
    db 7
    dq __dbase_wfm_text_54
    db 14
    dq __dbase_wfm_text_53
    db 7
    dq __dbase_wfm_text_56
    db 14
    dq __dbase_wfm_text_55
__dbase_wfm_property_table_1:
    db 11
    dq __dbase_wfm_text_60
    db 4
    dq __dbase_wfm_text_4
    db 7
    dq __dbase_wfm_text_61
    db 9
    dq __dbase_wfm_text_5
    db 7
    dq __dbase_wfm_text_62
    db 9
    dq __dbase_wfm_text_7
    db 4
    dq __dbase_wfm_text_63
    db 13
    dq __dbase_wfm_text_9
    db 1
    dq __dbase_wfm_text_64
    db 10
    dq __dbase_wfm_text_11
    db 2
    dq __dbase_wfm_text_65
    db 13
    dq __dbase_wfm_text_13
    db 2
    dq __dbase_wfm_text_66
    db 14
    dq __dbase_wfm_text_15
    db 6
    dq __dbase_wfm_text_67
    db 11
    dq __dbase_wfm_text_17
    db 1
    dq __dbase_wfm_text_31
    db 11
    dq __dbase_wfm_text_19
    db 7
    dq __dbase_wfm_text_68
    db 11
    dq __dbase_wfm_text_21
    db 7
    dq __dbase_wfm_text_69
    db 11
    dq __dbase_wfm_text_23
    db 1
    dq __dbase_wfm_text_64
    db 15
    dq __dbase_wfm_text_25
    db 1
    dq __dbase_wfm_text_64
    db 15
    dq __dbase_wfm_text_27
    db 1
    dq __dbase_wfm_text_64
    db 15
    dq __dbase_wfm_text_28
    db 1
    dq __dbase_wfm_text_64
    db 15
    dq __dbase_wfm_text_30
    db 3
    dq __dbase_wfm_text_33
    db 10
    dq __dbase_wfm_text_32
    db 6
    dq __dbase_wfm_text_67
    db 15
    dq __dbase_wfm_text_34
    db 1
    dq __dbase_wfm_text_31
    db 14
    dq __dbase_wfm_text_36
    db 7
    dq __dbase_wfm_text_68
    db 15
    dq __dbase_wfm_text_37
    db 3
    dq __dbase_wfm_text_33
    db 9
    dq __dbase_wfm_text_39
    db 6
    dq __dbase_wfm_text_67
    db 14
    dq __dbase_wfm_text_40
    db 1
    dq __dbase_wfm_text_31
    db 13
    dq __dbase_wfm_text_41
    db 7
    dq __dbase_wfm_text_68
    db 14
    dq __dbase_wfm_text_42
    db 3
    dq __dbase_wfm_text_70
    db 11
    dq __dbase_wfm_text_43
    db 6
    dq __dbase_wfm_text_71
    db 16
    dq __dbase_wfm_text_44
    db 1
    dq __dbase_wfm_text_31
    db 15
    dq __dbase_wfm_text_45
    db 7
    dq __dbase_wfm_text_68
    db 16
    dq __dbase_wfm_text_46
    db 3
    dq __dbase_wfm_text_33
    db 12
    dq __dbase_wfm_text_47
    db 6
    dq __dbase_wfm_text_67
    db 17
    dq __dbase_wfm_text_48
    db 1
    dq __dbase_wfm_text_31
    db 16
    dq __dbase_wfm_text_49
    db 7
    dq __dbase_wfm_text_68
    db 17
    dq __dbase_wfm_text_50
    db 3
    dq __dbase_wfm_text_72
    db 9
    dq __dbase_wfm_text_51
    db 7
    dq __dbase_wfm_text_73
    db 14
    dq __dbase_wfm_text_53
    db 7
    dq __dbase_wfm_text_56
    db 14
    dq __dbase_wfm_text_55

; Stage 192: WFM numeric STORE constants
__dbase_wfm_numconst_0:
    dd 1202590843, 1079597793
__dbase_wfm_numconst_1:
    dd 1202590843, 1079597793
__dbase_wfm_numconst_2:
    dd 0, 1075838976
__dbase_wfm_numconst_3:
    dd 0, 1075314688
__dbase_wfm_numconst_4:
    dd 0, 1072693248
__dbase_wfm_numconst_5:
    dd 0, 1072693248
__dbase_wfm_numconst_6:
    dd 0, 1072693248
__dbase_wfm_numconst_7:
    dd 0, 0
__dbase_wfm_numconst_8:
    dd 0, 1076101120
__dbase_wfm_numconst_9:
    dd 0, 0
__dbase_wfm_numconst_10:
    dd 0, 1076101120
__dbase_wfm_numconst_11:
    dd 0, 0
__dbase_wfm_numconst_12:
    dd 0, 0
__dbase_wfm_numconst_13:
    dd 0, 0

; Stage 223 WFM zero-initialized storage
.section .bss
__dbase_wfm_form:
    resq 1
__dbase_wfm_obj_THIS_PushButton1:
    resq 1

; Stage 223: WFM runtime parameter slots (.bss)
__dbase_wfm_param___init___p1:
    resq 1
__dbase_wfm_param___init___p2:
    resq 1
__dbase_wfm_param_PushButton1_onClick_Sender:
    resq 1

; Stage 223: typed dBase WFM memory variables (.bss)
__dbase_wfm_mem_Ausdruck_type:
    resd 1
__dbase_wfm_mem_Ausdruck_num:
    resq 1
__dbase_wfm_mem_Ausdruck_ptr:
    resq 1
__dbase_wfm_mem_Ausdruck_len:
    resd 1
__dbase_wfm_mem_SpeicherVar_type:
    resd 1
__dbase_wfm_mem_SpeicherVar_num:
    resq 1
__dbase_wfm_mem_SpeicherVar_ptr:
    resq 1
__dbase_wfm_mem_SpeicherVar_len:
    resd 1
__dbase_wfm_mem_HatMaus_type:
    resd 1
__dbase_wfm_mem_HatMaus_num:
    resq 1
__dbase_wfm_mem_HatMaus_ptr:
    resq 1
__dbase_wfm_mem_HatMaus_len:
    resd 1
__dbase_wfm_mem_HatTastatur_type:
    resd 1
__dbase_wfm_mem_HatTastatur_num:
    resq 1
__dbase_wfm_mem_HatTastatur_ptr:
    resq 1
__dbase_wfm_mem_HatTastatur_len:
    resd 1
__dbase_wfm_mem_p1_type:
    resd 1
__dbase_wfm_mem_p1_num:
    resq 1
__dbase_wfm_mem_p1_ptr:
    resq 1
__dbase_wfm_mem_p1_len:
    resd 1
__dbase_wfm_mem_p2_type:
    resd 1
__dbase_wfm_mem_p2_num:
    resq 1
__dbase_wfm_mem_p2_ptr:
    resq 1
__dbase_wfm_mem_p2_len:
    resd 1
__dbase_wfm_mem___string_arg_7_type:
    resd 1
__dbase_wfm_mem___string_arg_7_num:
    resq 1
__dbase_wfm_mem___string_arg_7_ptr:
    resq 1
__dbase_wfm_mem___string_arg_7_len:
    resd 1
__dbase_wfm_mem___string_arg_8_type:
    resd 1
__dbase_wfm_mem___string_arg_8_num:
    resq 1
__dbase_wfm_mem___string_arg_8_ptr:
    resq 1
__dbase_wfm_mem___string_arg_8_len:
    resd 1
__dbase_wfm_mem___string_arg_9_type:
    resd 1
__dbase_wfm_mem___string_arg_9_num:
    resq 1
__dbase_wfm_mem___string_arg_9_ptr:
    resq 1
__dbase_wfm_mem___string_arg_9_len:
    resd 1
__dbase_wfm_mem___string_arg_10_type:
    resd 1
__dbase_wfm_mem___string_arg_10_num:
    resq 1
__dbase_wfm_mem___string_arg_10_ptr:
    resq 1
__dbase_wfm_mem___string_arg_10_len:
    resd 1
__dbase_wfm_mem___string_arg_11_type:
    resd 1
__dbase_wfm_mem___string_arg_11_num:
    resq 1
__dbase_wfm_mem___string_arg_11_ptr:
    resq 1
__dbase_wfm_mem___string_arg_11_len:
    resd 1
__dbase_wfm_mem___wfm_ismouse_print_type:
    resd 1
__dbase_wfm_mem___wfm_ismouse_print_num:
    resq 1
__dbase_wfm_mem___wfm_ismouse_print_ptr:
    resq 1
__dbase_wfm_mem___wfm_ismouse_print_len:
    resd 1
__dbase_wfm_mem___wfm_iskeyboard_print_type:
    resd 1
__dbase_wfm_mem___wfm_iskeyboard_print_num:
    resq 1
__dbase_wfm_mem___wfm_iskeyboard_print_ptr:
    resq 1
__dbase_wfm_mem___wfm_iskeyboard_print_len:
    resd 1
__dbase_wfm_mem_A_type:
    resd 1
__dbase_wfm_mem_A_num:
    resq 1
__dbase_wfm_mem_A_ptr:
    resq 1
__dbase_wfm_mem_A_len:
    resd 1
__dbase_wfm_mem_C_type:
    resd 1
__dbase_wfm_mem_C_num:
    resq 1
__dbase_wfm_mem_C_ptr:
    resq 1
__dbase_wfm_mem_C_len:
    resd 1
