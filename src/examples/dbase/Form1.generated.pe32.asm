bits 32

import DBaseQtSetWorkstationMode, "libd64_qt5.dll", "#6"
import DBaseQtSetDebugTheme, "libd64_qt5.dll", "#62"
import DBaseQtInitialize, "libd64_qt5.dll", "#7"
import DBaseQtShowWindow, "libd64_qt5.dll", "#9"
import DBaseQtProcessEvents, "libd64_qt5.dll", "#10"
import DBaseQtSetDebugVisible, "libd64_qt5.dll", "#11"
import DBaseQtAppendConsole, "libd64_qt5.dll", "#12"
import DBaseQtAppendDebug, "libd64_qt5.dll", "#13"
import DBaseQtSetOutputColor, "libd64_qt5.dll", "#15"
import DBaseQtClearScreen, "libd64_qt5.dll", "#16"
import DBaseQtClearScreenChar, "libd64_qt5.dll", "#17"
import DBaseQtClearScreenColor, "libd64_qt5.dll", "#18"
import DBaseQtSetBorderColor, "libd64_qt5.dll", "#19"
import DBaseQtMarkProgramFinished, "libd64_qt5.dll", "#58"
import DBaseQtExec, "libd64_qt5.dll", "#59"
import DBaseQtShutdownRequested, "libd64_qt5.dll", "#60"
import DBaseQtShutdown, "libd64_qt5.dll", "#61"
import DBaseQtMenuCreate, "libd64_qt5.dll", "#35"
import DBaseQtMenuSetText, "libd64_qt5.dll", "#36"
import DBaseQtMenuSetSeparator, "libd64_qt5.dll", "#37"
import DBaseQtMenuSetShortcut, "libd64_qt5.dll", "#38"
import DBaseQtMenuSetOnClick, "libd64_qt5.dll", "#39"
import DBaseQtEnsureDefaultMenu, "libd64_qt5.dll", "#34"
import DBaseQtSetColorNormal, "libd64_qt5.dll", "#14"
import DBaseQtSessionCreate, "libd64_qt5.dll", "#20"
import DBaseQtGetLoginSession, "libd64_qt5.dll", "#21"
import DBaseQtSessionLogin, "libd64_qt5.dll", "#22"
import DBaseQtDatabaseCreate, "libd64_qt5.dll", "#23"
import DBaseQtDatabaseSetPath, "libd64_qt5.dll", "#24"
import DBaseQtDatabaseSetDatabaseName, "libd64_qt5.dll", "#25"
import DBaseQtDatabaseSetUserName, "libd64_qt5.dll", "#26"
import DBaseQtDatabaseSetPassword, "libd64_qt5.dll", "#27"
import DBaseQtDatabaseSetAlias, "libd64_qt5.dll", "#28"
import DBaseQtDatabaseSetSession, "libd64_qt5.dll", "#29"
import DBaseQtDatabaseSetActive, "libd64_qt5.dll", "#30"
import DBaseQtDatabaseOpen, "libd64_qt5.dll", "#31"
import DBaseQtDatabaseClose, "libd64_qt5.dll", "#32"
import DBaseQtDatabaseCommit, "libd64_qt5.dll", "#33"
import __dbase_gcvt, "msvcrt.dll", "#448"
import __dbase_malloc, "msvcrt.dll", "#1291"
import __dbase_memcpy, "msvcrt.dll", "#1303"
import __dbase_memcmp, "msvcrt.dll", "#1302"
import ExitProcess, "kernel32.dll", "#392"
import VirtualAlloc, "kernel32.dll", "#1546"
import VirtualFree, "kernel32.dll", "#1549"
import AllocConsole, "kernel32.dll", "#26"
import FreeConsole, "kernel32.dll", "#467"
import GetStdHandle, "kernel32.dll", "#772"
import CreateFileA, "kernel32.dll", "#230"
import GetConsoleScreenBufferInfo, "kernel32.dll", "#557"
import SetConsoleScreenBufferSize, "kernel32.dll", "#1342"
import SetConsoleOutputCP, "kernel32.dll", "#1339"
import SetConsoleTitleA, "kernel32.dll", "#1344"
import GetConsoleWindow, "kernel32.dll", "#562"
import ShowWindow, "user32.dll", "#2413"
import SetWindowPos, "user32.dll", "#2394"
import SetForegroundWindow, "user32.dll", "#2326"
import WriteFile, "kernel32.dll", "#1622"
import DBaseQtInitializeGui, "libd64_qt5.dll", "#8"
import DBaseQtFormCreate, "libd64_qt5.dll", "#40"
import DBaseQtControlCreateEx, "libd64_qt5.dll", "#42"
import DBaseQtWidgetSetGeometry, "libd64_qt5.dll", "#49"
import DBaseQtWidgetSetProperty, "libd64_qt5.dll", "#51"
import DBaseQtWidgetSetFont, "libd64_qt5.dll", "#56"
import DBaseQtObjectBindEvent, "libd64_qt5.dll", "#43"
import DBaseQtTimerCreate, "libd64_qt5.dll", "#45"
import DBaseQtFormOpen, "libd64_qt5.dll", "#57"
import DBaseQtConsoleWrite, "libd64_qt5.dll", "#48"
import __dbase_upper_buffer, "libd64_qt5.dll", "#4"
global _start
entry _start

section .text

_start:
    push 0
    call DBaseQtSetWorkstationMode
    add esp, 4
    push 2
    call DBaseQtSetDebugTheme
    add esp, 4
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
    push 0
    push __dbase_text_2
    call __dbase_console_write
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
    call __dbase_console_shutdown
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

; Stage 109: lazy Win32 console for dBase ? / ??
__dbase_console_ensure:
    cmp dword ptr [__dbase_console_ready], 0
    jne __dbase_console_ensure_done
    call AllocConsole
    push 0
    push 0
    push 3
    push 0
    push 3
    push 3221225472
    push __dbase_console_out_name
    call CreateFileA
    test eax, eax
    je __dbase_console_handle_fallback
    cmp eax, -1
    je __dbase_console_handle_fallback
    mov dword ptr [__dbase_console_handle], eax
    jmp __dbase_console_handle_ready
__dbase_console_handle_fallback:
    push -11
    call GetStdHandle
    test eax, eax
    je __dbase_console_ensure_done
    cmp eax, -1
    je __dbase_console_ensure_done
    mov dword ptr [__dbase_console_handle], eax
__dbase_console_handle_ready:
    push 1252
    call SetConsoleOutputCP
    push __dbase_console_info
    push dword ptr [__dbase_console_handle]
    call GetConsoleScreenBufferInfo
    test eax, eax
    je __dbase_console_buffer_fallback
    mov edx, dword ptr [__dbase_console_info]
    and edx, 65535
    or edx, 32768000
    jmp __dbase_console_buffer_ready
__dbase_console_buffer_fallback:
    mov edx, 32768080
__dbase_console_buffer_ready:
    push edx
    push dword ptr [__dbase_console_handle]
    call SetConsoleScreenBufferSize
    push __dbase_text_1
    call SetConsoleTitleA
    call GetConsoleWindow
    test eax, eax
    je __dbase_console_window_ready
    mov dword ptr [__dbase_console_window], eax
    push 5
    push eax
    call ShowWindow
    push 67
    push 0
    push 0
    push 0
    push 0
    push -1
    push dword ptr [__dbase_console_window]
    call SetWindowPos
    push dword ptr [__dbase_console_window]
    call SetForegroundWindow
__dbase_console_window_ready:
    mov dword ptr [__dbase_console_ready], 1
__dbase_console_ensure_done:
    ret

__dbase_console_write:
    push ebp
    mov ebp, esp
    call __dbase_console_ensure
    cmp dword ptr [__dbase_console_ready], 0
    je __dbase_console_write_done
    cmp dword ptr [ebp+12], 0
    je __dbase_console_write_done
    push 0
    push __dbase_console_written
    push dword ptr [ebp+12]
    push dword ptr [ebp+8]
    push dword ptr [__dbase_console_handle]
    call WriteFile
__dbase_console_write_done:
    mov esp, ebp
    pop ebp
    ret

__dbase_console_shutdown:
    cmp dword ptr [__dbase_console_ready], 0
    je __dbase_console_shutdown_done
    call FreeConsole
    mov dword ptr [__dbase_console_handle], 0
    mov dword ptr [__dbase_console_window], 0
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
    resd 1
__dbase_exit_code:
    resd 1
__dbase_console_ready:
    resd 1
__dbase_console_handle:
    resd 1
__dbase_console_window:
    resd 1
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
    mov eax, __dbase_wfm_qt_output_marker
    push 0
    call DBaseQtSetWorkstationMode
    add esp, 4
    push 2
    call DBaseQtSetDebugTheme
    add esp, 4
    push __dbase_wfm_text_0
    call DBaseQtInitializeGui
    add esp, 4
    push 4
    push 12288
    push 96
    push 0
    call VirtualAlloc
    test eax, eax
    jne __dbase_wfm_format_buffer_ok
    push 1
    call ExitProcess
__dbase_wfm_format_buffer_ok:
    mov dword ptr [__dbase_format_buffer], eax
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
    push 35
    push __dbase_wfm_property_table_0
    push dword ptr [__dbase_wfm_form]
    call __dbase_wfm_set_properties_packed
    add esp, 12
    push 7
    push __dbase_wfm_text_58
    push dword ptr [__dbase_wfm_form]
    push 10
    push __dbase_wfm_text_57
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
    push __dbase_wfm_text_59
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtWidgetSetFont
    add esp, 32
    push 34
    push __dbase_wfm_property_table_1
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call __dbase_wfm_set_properties_packed
    add esp, 12
    push __dbase_wfm_proc_PushButton1_onClick
    push 7
    push __dbase_wfm_text_74
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtObjectBindEvent
    add esp, 16
    push 4
    push 51
    call __dbase_wfm_proc___init__
    add esp, 8
    push dword ptr [__dbase_wfm_form]
    call DBaseQtFormOpen
    add esp, 4
    call __dbase_wfm_proc___main__
    call DBaseQtExec
    call __dbase_wfm_proc___del__
    call DBaseQtShutdown
    mov eax, dword ptr [__dbase_format_buffer]
    test eax, eax
    je __dbase_wfm_format_buffer_free_done
    push 32768
    push 0
    push eax
    call VirtualFree
    mov dword ptr [__dbase_format_buffer], 0
__dbase_wfm_format_buffer_free_done:
    push 0
    call ExitProcess

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
    mov eax, dword ptr [esp+4]
    mov dword ptr [__dbase_wfm_param___init___p1], eax
    mov eax, dword ptr [esp+8]
    mov dword ptr [__dbase_wfm_param___init___p2], eax
    ; ? "p1 = " + p1
    push 0
    push 5
    push __dbase_wfm_output_text_75
    call DBaseQtConsoleWrite
    add esp, 12
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
    push dword ptr [__dbase_format_buffer]
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, dword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_wfm_strlen_0:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_wfm_strlen_done_0
    inc ecx
    inc edx
    jmp __dbase_wfm_strlen_0
__dbase_wfm_strlen_done_0:
    push 1
    push edx
    push dword ptr [__dbase_format_buffer]
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_0
__dbase_wfm_print_string_0:
    mov eax, dword ptr [__dbase_wfm_mem_p1_ptr]
    test eax, eax
    je __dbase_wfm_print_null_0
    push 1
    push dword ptr [__dbase_wfm_mem_p1_len]
    push eax
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_0
__dbase_wfm_print_object_0:
    mov eax, dword ptr [__dbase_wfm_mem_p1_ptr]
    test eax, eax
    je __dbase_wfm_print_null_0
    push 1
    push 8
    push __dbase_wfm_output_text_77
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_0
__dbase_wfm_print_null_0:
    push 1
    push 6
    push __dbase_wfm_output_text_76
    call DBaseQtConsoleWrite
    add esp, 12
__dbase_wfm_print_done_0:
    ; ? "p2 = " + p2
    push 0
    push 5
    push __dbase_wfm_output_text_78
    call DBaseQtConsoleWrite
    add esp, 12
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
    push dword ptr [__dbase_format_buffer]
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, dword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_wfm_strlen_1:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_wfm_strlen_done_1
    inc ecx
    inc edx
    jmp __dbase_wfm_strlen_1
__dbase_wfm_strlen_done_1:
    push 1
    push edx
    push dword ptr [__dbase_format_buffer]
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_1
__dbase_wfm_print_string_1:
    mov eax, dword ptr [__dbase_wfm_mem_p2_ptr]
    test eax, eax
    je __dbase_wfm_print_null_1
    push 1
    push dword ptr [__dbase_wfm_mem_p2_len]
    push eax
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_1
__dbase_wfm_print_object_1:
    mov eax, dword ptr [__dbase_wfm_mem_p2_ptr]
    test eax, eax
    je __dbase_wfm_print_null_1
    push 1
    push 8
    push __dbase_wfm_output_text_80
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_1
__dbase_wfm_print_null_1:
    push 1
    push 6
    push __dbase_wfm_output_text_79
    call DBaseQtConsoleWrite
    add esp, 12
__dbase_wfm_print_done_1:
    ret
; END WFM PROCEDURE/FUNCTION: __init__


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: __main__
; ------------------------------------------------------------
__dbase_wfm_proc___main__:
    mov eax, 7
    ret
; END WFM PROCEDURE/FUNCTION: __main__


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: PushButton1_onClick
; ------------------------------------------------------------
__dbase_wfm_proc_PushButton1_onClick:
    mov eax, dword ptr [esp+4]
    mov dword ptr [__dbase_wfm_param_PushButton1_onClick_Sender], eax
    ; STORE 101.42 TO Ausdruck
    fld qword ptr [__dbase_wfm_numconst_0]
    fstp qword ptr [__dbase_wfm_mem_Ausdruck_num]
    mov dword ptr [__dbase_wfm_mem_Ausdruck_type], 2
    mov dword ptr [__dbase_wfm_mem_Ausdruck_len], 0
    mov dword ptr [__dbase_wfm_mem_Ausdruck_ptr], 0
    ; Ausdruck = 101.42
    fld qword ptr [__dbase_wfm_numconst_1]
    fstp qword ptr [__dbase_wfm_mem_Ausdruck_num]
    mov dword ptr [__dbase_wfm_mem_Ausdruck_type], 2
    mov dword ptr [__dbase_wfm_mem_Ausdruck_len], 0
    mov dword ptr [__dbase_wfm_mem_Ausdruck_ptr], 0
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
    push dword ptr [__dbase_format_buffer]
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, dword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_wfm_strlen_2:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_wfm_strlen_done_2
    inc ecx
    inc edx
    jmp __dbase_wfm_strlen_2
__dbase_wfm_strlen_done_2:
    push 1
    push edx
    push dword ptr [__dbase_format_buffer]
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_2
__dbase_wfm_print_string_2:
    mov eax, dword ptr [__dbase_wfm_mem_Ausdruck_ptr]
    test eax, eax
    je __dbase_wfm_print_null_2
    push 1
    push dword ptr [__dbase_wfm_mem_Ausdruck_len]
    push eax
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_2
__dbase_wfm_print_object_2:
    mov eax, dword ptr [__dbase_wfm_mem_Ausdruck_ptr]
    test eax, eax
    je __dbase_wfm_print_null_2
    push 1
    push 8
    push __dbase_wfm_output_text_82
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_2
__dbase_wfm_print_null_2:
    push 1
    push 6
    push __dbase_wfm_output_text_81
    call DBaseQtConsoleWrite
    add esp, 12
__dbase_wfm_print_done_2:
    ; STORE INT(Ausdruck) TO Ausdruck
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 1
    je __dbase_wfm_int_numeric_3
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 2
    je __dbase_wfm_int_numeric_3
    mov dword ptr [__dbase_wfm_mem_Ausdruck_type], 0
    mov dword ptr [__dbase_wfm_mem_Ausdruck_len], 0
    mov dword ptr [__dbase_wfm_mem_Ausdruck_ptr], 0
    jmp __dbase_wfm_int_done_3
__dbase_wfm_int_numeric_3:
    fld qword ptr [__dbase_wfm_mem_Ausdruck_num]
    sub esp, 8
    fnstcw word ptr [esp]
    mov eax, dword ptr [esp]
    or eax, 0x0C00
    mov dword ptr [esp+4], eax
    fldcw word ptr [esp+4]
    frndint
    fldcw word ptr [esp]
    add esp, 8
    fstp qword ptr [__dbase_wfm_mem_Ausdruck_num]
    mov dword ptr [__dbase_wfm_mem_Ausdruck_type], 1
    mov dword ptr [__dbase_wfm_mem_Ausdruck_len], 0
    mov dword ptr [__dbase_wfm_mem_Ausdruck_ptr], 0
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
    push dword ptr [__dbase_format_buffer]
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, dword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_wfm_strlen_3:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_wfm_strlen_done_3
    inc ecx
    inc edx
    jmp __dbase_wfm_strlen_3
__dbase_wfm_strlen_done_3:
    push 1
    push edx
    push dword ptr [__dbase_format_buffer]
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_4
__dbase_wfm_print_string_4:
    mov eax, dword ptr [__dbase_wfm_mem_Ausdruck_ptr]
    test eax, eax
    je __dbase_wfm_print_null_4
    push 1
    push dword ptr [__dbase_wfm_mem_Ausdruck_len]
    push eax
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_4
__dbase_wfm_print_object_4:
    mov eax, dword ptr [__dbase_wfm_mem_Ausdruck_ptr]
    test eax, eax
    je __dbase_wfm_print_null_4
    push 1
    push 8
    push __dbase_wfm_output_text_84
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_4
__dbase_wfm_print_null_4:
    push 1
    push 6
    push __dbase_wfm_output_text_83
    call DBaseQtConsoleWrite
    add esp, 12
__dbase_wfm_print_done_4:
    ; ? "1: " + 101.42
    push 0
    push 3
    push __dbase_wfm_output_text_85
    call DBaseQtConsoleWrite
    add esp, 12
    push 1
    push 6
    push __dbase_wfm_output_text_86
    call DBaseQtConsoleWrite
    add esp, 12
    ; ? "2: " + INT(101.42)
    push 0
    push 3
    push __dbase_wfm_output_text_87
    call DBaseQtConsoleWrite
    add esp, 12
    push 1
    push 3
    push __dbase_wfm_output_text_88
    call DBaseQtConsoleWrite
    add esp, 12
    ; ? "3: " + Ausdruck
    push 0
    push 3
    push __dbase_wfm_output_text_89
    call DBaseQtConsoleWrite
    add esp, 12
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
    push dword ptr [__dbase_format_buffer]
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, dword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_wfm_strlen_4:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_wfm_strlen_done_4
    inc ecx
    inc edx
    jmp __dbase_wfm_strlen_4
__dbase_wfm_strlen_done_4:
    push 1
    push edx
    push dword ptr [__dbase_format_buffer]
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_5
__dbase_wfm_print_string_5:
    mov eax, dword ptr [__dbase_wfm_mem_Ausdruck_ptr]
    test eax, eax
    je __dbase_wfm_print_null_5
    push 1
    push dword ptr [__dbase_wfm_mem_Ausdruck_len]
    push eax
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_5
__dbase_wfm_print_object_5:
    mov eax, dword ptr [__dbase_wfm_mem_Ausdruck_ptr]
    test eax, eax
    je __dbase_wfm_print_null_5
    push 1
    push 8
    push __dbase_wfm_output_text_91
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_5
__dbase_wfm_print_null_5:
    push 1
    push 6
    push __dbase_wfm_output_text_90
    call DBaseQtConsoleWrite
    add esp, 12
__dbase_wfm_print_done_5:
    mov dword ptr [__dbase_wfm_mem___string_arg_6_ptr], __dbase_wfm_output_text_92
    mov dword ptr [__dbase_wfm_mem___string_arg_6_len], 11
    mov dword ptr [__dbase_wfm_mem___string_arg_6_type], 3
    mov eax, dword ptr [__dbase_wfm_mem___string_arg_6_len]
    mov ecx, eax
    add eax, ecx
    add eax, ecx
    add eax, 1
    push eax
    call __dbase_malloc
    add esp, 4
    test eax, eax
    jne __wfm_upper_7_allocated
    push 8
    call ExitProcess
__wfm_upper_7_allocated:
    mov dword ptr [__dbase_wfm_mem___string_arg_7_ptr], eax
    mov ecx, dword ptr [__dbase_wfm_mem___string_arg_6_len]
    mov edx, ecx
    add edx, ecx
    add edx, ecx
    add edx, 1
    push ecx
    push dword ptr [__dbase_wfm_mem___string_arg_6_ptr]
    push edx
    push dword ptr [__dbase_wfm_mem___string_arg_7_ptr]
    call __dbase_upper_buffer
    add esp, 16
    cmp eax, -1
    jne __wfm_upper_7_converted
    push 13
    call ExitProcess
__wfm_upper_7_converted:
    mov dword ptr [__dbase_wfm_mem___string_arg_7_len], eax
    mov dword ptr [__dbase_wfm_mem___string_arg_7_type], 3
    ; ? !("Das ist Gut")
    cmp dword ptr [__dbase_wfm_mem___string_arg_7_type], 0
    je __dbase_wfm_print_null_8
    cmp dword ptr [__dbase_wfm_mem___string_arg_7_type], 3
    je __dbase_wfm_print_string_8
    cmp dword ptr [__dbase_wfm_mem___string_arg_7_type], 4
    je __dbase_wfm_print_object_8
    cmp dword ptr [__dbase_wfm_mem___string_arg_7_type], 1
    je __dbase_wfm_print_number_8
    cmp dword ptr [__dbase_wfm_mem___string_arg_7_type], 2
    je __dbase_wfm_print_number_8
    jmp __dbase_wfm_print_null_8
__dbase_wfm_print_number_8:
    fld qword ptr [__dbase_wfm_mem___string_arg_7_num]
    fstp qword ptr [__dbase_temp_number]
    push dword ptr [__dbase_format_buffer]
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, dword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_wfm_strlen_5:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_wfm_strlen_done_5
    inc ecx
    inc edx
    jmp __dbase_wfm_strlen_5
__dbase_wfm_strlen_done_5:
    push 1
    push edx
    push dword ptr [__dbase_format_buffer]
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_8
__dbase_wfm_print_string_8:
    mov eax, dword ptr [__dbase_wfm_mem___string_arg_7_ptr]
    test eax, eax
    je __dbase_wfm_print_null_8
    push 1
    push dword ptr [__dbase_wfm_mem___string_arg_7_len]
    push eax
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_8
__dbase_wfm_print_object_8:
    mov eax, dword ptr [__dbase_wfm_mem___string_arg_7_ptr]
    test eax, eax
    je __dbase_wfm_print_null_8
    push 1
    push 8
    push __dbase_wfm_output_text_94
    call DBaseQtConsoleWrite
    add esp, 12
    jmp __dbase_wfm_print_done_8
__dbase_wfm_print_null_8:
    push 1
    push 6
    push __dbase_wfm_output_text_93
    call DBaseQtConsoleWrite
    add esp, 12
__dbase_wfm_print_done_8:
    ret
; END WFM PROCEDURE/FUNCTION: PushButton1_onClick

; Stage 224: local packed WFM property decoder (PE32)
.section .text
__dbase_wfm_set_properties_packed:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [ebp+8]
    mov esi, dword ptr [ebp+12]
    mov edi, dword ptr [ebp+16]
__dbase_wfm_set_properties_packed_loop:
    test edi, edi
    jle __dbase_wfm_set_properties_packed_done
    movzx eax, byte ptr [esi]
    push eax
    push dword ptr [esi+1]
    movzx eax, byte ptr [esi+5]
    push eax
    push dword ptr [esi+6]
    push ebx
    call DBaseQtWidgetSetProperty
    add esp, 20
    add esi, 10
    dec edi
    jmp __dbase_wfm_set_properties_packed_loop
__dbase_wfm_set_properties_packed_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
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
    db 68, 97, 115, 32, 105, 115, 116, 32, 71, 117, 116
__dbase_wfm_output_text_93:
    db 60, 110, 117, 108, 108, 62
__dbase_wfm_output_text_94:
    db 60, 111, 98, 106, 101, 99, 116, 62

; Stage 223: compact WFM property blocks
; record = db valueLength, ptr valuePtr, db nameLength, ptr namePtr
__dbase_wfm_property_table_0:
    db 4
    dd __dbase_wfm_text_3
    db 4
    dd __dbase_wfm_text_2
    db 5
    dd __dbase_wfm_text_0
    db 4
    dd __dbase_wfm_text_4
    db 9
    dd __dbase_wfm_text_6
    db 9
    dd __dbase_wfm_text_5
    db 7
    dd __dbase_wfm_text_8
    db 9
    dd __dbase_wfm_text_7
    db 17
    dd __dbase_wfm_text_10
    db 13
    dd __dbase_wfm_text_9
    db 1
    dd __dbase_wfm_text_12
    db 10
    dd __dbase_wfm_text_11
    db 2
    dd __dbase_wfm_text_14
    db 13
    dd __dbase_wfm_text_13
    db 2
    dd __dbase_wfm_text_16
    db 14
    dd __dbase_wfm_text_15
    db 5
    dd __dbase_wfm_text_18
    db 11
    dd __dbase_wfm_text_17
    db 1
    dd __dbase_wfm_text_20
    db 11
    dd __dbase_wfm_text_19
    db 7
    dd __dbase_wfm_text_22
    db 11
    dd __dbase_wfm_text_21
    db 7
    dd __dbase_wfm_text_24
    db 11
    dd __dbase_wfm_text_23
    db 1
    dd __dbase_wfm_text_26
    db 15
    dd __dbase_wfm_text_25
    db 1
    dd __dbase_wfm_text_20
    db 15
    dd __dbase_wfm_text_27
    db 1
    dd __dbase_wfm_text_29
    db 15
    dd __dbase_wfm_text_28
    db 1
    dd __dbase_wfm_text_31
    db 15
    dd __dbase_wfm_text_30
    db 3
    dd __dbase_wfm_text_33
    db 10
    dd __dbase_wfm_text_32
    db 6
    dd __dbase_wfm_text_35
    db 15
    dd __dbase_wfm_text_34
    db 1
    dd __dbase_wfm_text_29
    db 14
    dd __dbase_wfm_text_36
    db 7
    dd __dbase_wfm_text_38
    db 15
    dd __dbase_wfm_text_37
    db 3
    dd __dbase_wfm_text_33
    db 9
    dd __dbase_wfm_text_39
    db 5
    dd __dbase_wfm_text_18
    db 14
    dd __dbase_wfm_text_40
    db 1
    dd __dbase_wfm_text_20
    db 13
    dd __dbase_wfm_text_41
    db 7
    dd __dbase_wfm_text_22
    db 14
    dd __dbase_wfm_text_42
    db 3
    dd __dbase_wfm_text_33
    db 11
    dd __dbase_wfm_text_43
    db 5
    dd __dbase_wfm_text_18
    db 16
    dd __dbase_wfm_text_44
    db 1
    dd __dbase_wfm_text_20
    db 15
    dd __dbase_wfm_text_45
    db 7
    dd __dbase_wfm_text_22
    db 16
    dd __dbase_wfm_text_46
    db 3
    dd __dbase_wfm_text_33
    db 12
    dd __dbase_wfm_text_47
    db 5
    dd __dbase_wfm_text_18
    db 17
    dd __dbase_wfm_text_48
    db 1
    dd __dbase_wfm_text_20
    db 16
    dd __dbase_wfm_text_49
    db 7
    dd __dbase_wfm_text_22
    db 17
    dd __dbase_wfm_text_50
    db 3
    dd __dbase_wfm_text_52
    db 9
    dd __dbase_wfm_text_51
    db 7
    dd __dbase_wfm_text_54
    db 14
    dd __dbase_wfm_text_53
    db 7
    dd __dbase_wfm_text_56
    db 14
    dd __dbase_wfm_text_55
__dbase_wfm_property_table_1:
    db 11
    dd __dbase_wfm_text_60
    db 4
    dd __dbase_wfm_text_4
    db 7
    dd __dbase_wfm_text_61
    db 9
    dd __dbase_wfm_text_5
    db 7
    dd __dbase_wfm_text_62
    db 9
    dd __dbase_wfm_text_7
    db 4
    dd __dbase_wfm_text_63
    db 13
    dd __dbase_wfm_text_9
    db 1
    dd __dbase_wfm_text_64
    db 10
    dd __dbase_wfm_text_11
    db 2
    dd __dbase_wfm_text_65
    db 13
    dd __dbase_wfm_text_13
    db 2
    dd __dbase_wfm_text_66
    db 14
    dd __dbase_wfm_text_15
    db 6
    dd __dbase_wfm_text_67
    db 11
    dd __dbase_wfm_text_17
    db 1
    dd __dbase_wfm_text_31
    db 11
    dd __dbase_wfm_text_19
    db 7
    dd __dbase_wfm_text_68
    db 11
    dd __dbase_wfm_text_21
    db 7
    dd __dbase_wfm_text_69
    db 11
    dd __dbase_wfm_text_23
    db 1
    dd __dbase_wfm_text_64
    db 15
    dd __dbase_wfm_text_25
    db 1
    dd __dbase_wfm_text_64
    db 15
    dd __dbase_wfm_text_27
    db 1
    dd __dbase_wfm_text_64
    db 15
    dd __dbase_wfm_text_28
    db 1
    dd __dbase_wfm_text_64
    db 15
    dd __dbase_wfm_text_30
    db 3
    dd __dbase_wfm_text_33
    db 10
    dd __dbase_wfm_text_32
    db 6
    dd __dbase_wfm_text_67
    db 15
    dd __dbase_wfm_text_34
    db 1
    dd __dbase_wfm_text_31
    db 14
    dd __dbase_wfm_text_36
    db 7
    dd __dbase_wfm_text_68
    db 15
    dd __dbase_wfm_text_37
    db 3
    dd __dbase_wfm_text_33
    db 9
    dd __dbase_wfm_text_39
    db 6
    dd __dbase_wfm_text_67
    db 14
    dd __dbase_wfm_text_40
    db 1
    dd __dbase_wfm_text_31
    db 13
    dd __dbase_wfm_text_41
    db 7
    dd __dbase_wfm_text_68
    db 14
    dd __dbase_wfm_text_42
    db 3
    dd __dbase_wfm_text_70
    db 11
    dd __dbase_wfm_text_43
    db 6
    dd __dbase_wfm_text_71
    db 16
    dd __dbase_wfm_text_44
    db 1
    dd __dbase_wfm_text_31
    db 15
    dd __dbase_wfm_text_45
    db 7
    dd __dbase_wfm_text_68
    db 16
    dd __dbase_wfm_text_46
    db 3
    dd __dbase_wfm_text_33
    db 12
    dd __dbase_wfm_text_47
    db 6
    dd __dbase_wfm_text_67
    db 17
    dd __dbase_wfm_text_48
    db 1
    dd __dbase_wfm_text_31
    db 16
    dd __dbase_wfm_text_49
    db 7
    dd __dbase_wfm_text_68
    db 17
    dd __dbase_wfm_text_50
    db 3
    dd __dbase_wfm_text_72
    db 9
    dd __dbase_wfm_text_51
    db 7
    dd __dbase_wfm_text_73
    db 14
    dd __dbase_wfm_text_53
    db 7
    dd __dbase_wfm_text_56
    db 14
    dd __dbase_wfm_text_55

; Stage 192: WFM numeric STORE constants
__dbase_wfm_numconst_0:
    dd 1202590843, 1079597793
__dbase_wfm_numconst_1:
    dd 1202590843, 1079597793

; Stage 223 WFM zero-initialized storage
.section .bss
__dbase_wfm_form:
    resd 1
__dbase_wfm_obj_THIS_PushButton1:
    resd 1

; Stage 223: WFM runtime parameter slots (.bss)
__dbase_wfm_param___init___p1:
    resd 1
__dbase_wfm_param___init___p2:
    resd 1
__dbase_wfm_param_PushButton1_onClick_Sender:
    resd 1

; Stage 223: typed dBase WFM memory variables (.bss)
__dbase_wfm_mem_Ausdruck_type:
    resd 1
__dbase_wfm_mem_Ausdruck_num:
    resq 1
__dbase_wfm_mem_Ausdruck_ptr:
    resd 1
__dbase_wfm_mem_Ausdruck_len:
    resd 1
__dbase_wfm_mem_p1_type:
    resd 1
__dbase_wfm_mem_p1_num:
    resq 1
__dbase_wfm_mem_p1_ptr:
    resd 1
__dbase_wfm_mem_p1_len:
    resd 1
__dbase_wfm_mem_p2_type:
    resd 1
__dbase_wfm_mem_p2_num:
    resq 1
__dbase_wfm_mem_p2_ptr:
    resd 1
__dbase_wfm_mem_p2_len:
    resd 1
__dbase_wfm_mem___string_arg_6_type:
    resd 1
__dbase_wfm_mem___string_arg_6_num:
    resq 1
__dbase_wfm_mem___string_arg_6_ptr:
    resd 1
__dbase_wfm_mem___string_arg_6_len:
    resd 1
__dbase_wfm_mem___string_arg_7_type:
    resd 1
__dbase_wfm_mem___string_arg_7_num:
    resq 1
__dbase_wfm_mem___string_arg_7_ptr:
    resd 1
__dbase_wfm_mem___string_arg_7_len:
    resd 1
