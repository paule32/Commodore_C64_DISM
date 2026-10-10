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
import SpeechInitialize, "retro_speech.dll", "SpeechInitialize"
import SpeechSetMix, "retro_speech.dll", "SpeechSetMix"
import SpeechSetPitch, "retro_speech.dll", "SpeechSetPitch"
import SpeechSetSpeed, "retro_speech.dll", "SpeechSetSpeed"
import SpeechSetExpression, "retro_speech.dll", "SpeechSetExpression"
import SpeechSetArticulation, "retro_speech.dll", "SpeechSetArticulation"
import SpeechSpeak, "retro_speech.dll", "SpeechSpeak"
import SpeechSpeakCP1252, "retro_speech.dll", "SpeechSpeakCP1252"
import SpeechShutdown, "retro_speech.dll", "SpeechShutdown"
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
import GetSystemMetrics, "user32.dll", "#1963"
import ShowWindow, "user32.dll", "#2413"
import SetWindowPos, "user32.dll", "#2394"
import SetForegroundWindow, "user32.dll", "#2326"
import WriteFile, "kernel32.dll", "#1622"
global _start
entry _start

section .text

_start:
    push 1
    call DBaseQtSetWorkstationMode
    add esp, 4
    push 0
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
    mov dword ptr [__dbase_output_debug_override], 1
    mov dword ptr [__dbase_output_debug_visible], 1
    push 1
    call DBaseQtSetDebugVisible
    add esp, 4
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push 19
    call GetSystemMetrics
    test eax, eax
    setne al
    movzx eax, al
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fstp qword ptr [__dbase_temp_number]
    push dword ptr [__dbase_format_buffer]
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, dword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_strlen_loop_4:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_strlen_done_5
    inc ecx
    inc edx
    jmp __dbase_strlen_loop_4
__dbase_strlen_done_5:
    mov dword ptr [__dbase_console_number_len], edx
    cmp dword ptr [__dbase_output_debug_override], -1
    jne __dbase_output_override_ready_6
    cmp dword ptr [__dbase_output_format_screen], 0
    je __dbase_output_console_7
    jmp __dbase_output_show_done_8
__dbase_output_override_ready_6:
    cmp dword ptr [__dbase_output_debug_override], 0
    je __dbase_output_console_7
__dbase_output_show_done_8:
    cmp dword ptr [__dbase_output_debug_visible], 0
    jne __dbase_output_already_visible_10
    mov dword ptr [__dbase_output_debug_visible], 1
    push 1
    call DBaseQtSetDebugVisible
    add esp, 4
__dbase_output_already_visible_10:
    push dword ptr [__dbase_console_number_len]
    push dword ptr [__dbase_format_buffer]
    call DBaseQtAppendDebug
    add esp, 8
    jmp __dbase_output_done_9
__dbase_output_console_7:
    push dword ptr [__dbase_console_number_len]
    push dword ptr [__dbase_format_buffer]
    call __dbase_console_write
    add esp, 8
__dbase_output_done_9:
    cmp dword ptr [__dbase_output_debug_override], -1
    jne __dbase_output_override_ready_11
    cmp dword ptr [__dbase_output_format_screen], 0
    je __dbase_output_console_12
    jmp __dbase_output_show_done_13
__dbase_output_override_ready_11:
    cmp dword ptr [__dbase_output_debug_override], 0
    je __dbase_output_console_12
__dbase_output_show_done_13:
    cmp dword ptr [__dbase_output_debug_visible], 0
    jne __dbase_output_already_visible_15
    mov dword ptr [__dbase_output_debug_visible], 1
    push 1
    call DBaseQtSetDebugVisible
    add esp, 4
__dbase_output_already_visible_15:
    push 2
    push __dbase_text_2
    call DBaseQtAppendDebug
    add esp, 8
    jmp __dbase_output_done_14
__dbase_output_console_12:
    push 2
    push __dbase_text_2
    call __dbase_console_write
    add esp, 8
__dbase_output_done_14:
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    cmp dword ptr [__dbase_output_debug_override], -1
    jne __dbase_output_override_ready_16
    cmp dword ptr [__dbase_output_format_screen], 0
    je __dbase_output_console_17
    jmp __dbase_output_show_done_18
__dbase_output_override_ready_16:
    cmp dword ptr [__dbase_output_debug_override], 0
    je __dbase_output_console_17
__dbase_output_show_done_18:
    cmp dword ptr [__dbase_output_debug_visible], 0
    jne __dbase_output_already_visible_20
    mov dword ptr [__dbase_output_debug_visible], 1
    push 1
    call DBaseQtSetDebugVisible
    add esp, 4
__dbase_output_already_visible_20:
    push 3
    push __dbase_text_3
    call DBaseQtAppendDebug
    add esp, 8
    jmp __dbase_output_done_19
__dbase_output_console_17:
    push 3
    push __dbase_text_3
    call __dbase_console_write
    add esp, 8
__dbase_output_done_19:
    cmp dword ptr [__dbase_output_debug_override], -1
    jne __dbase_output_override_ready_21
    cmp dword ptr [__dbase_output_format_screen], 0
    je __dbase_output_console_22
    jmp __dbase_output_show_done_23
__dbase_output_override_ready_21:
    cmp dword ptr [__dbase_output_debug_override], 0
    je __dbase_output_console_22
__dbase_output_show_done_23:
    cmp dword ptr [__dbase_output_debug_visible], 0
    jne __dbase_output_already_visible_25
    mov dword ptr [__dbase_output_debug_visible], 1
    push 1
    call DBaseQtSetDebugVisible
    add esp, 4
__dbase_output_already_visible_25:
    push 2
    push __dbase_text_2
    call DBaseQtAppendDebug
    add esp, 8
    jmp __dbase_output_done_24
__dbase_output_console_22:
    push 2
    push __dbase_text_2
    call __dbase_console_write
    add esp, 8
__dbase_output_done_24:
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    cmp dword ptr [__dbase_speech_ready], 0
    jne __dbase_speech_on_done_26
    push 22050
    call SpeechInitialize
    mov dword ptr [__dbase_speech_ready], eax
    test eax, eax
    je __dbase_speech_on_done_26
    push dword ptr [__dbase_speech_mix]
    call SpeechSetMix
    push dword ptr [__dbase_speech_pitch]
    call SpeechSetPitch
    push dword ptr [__dbase_speech_speed]
    call SpeechSetSpeed
    push dword ptr [__dbase_speech_expression]
    call SpeechSetExpression
    push dword ptr [__dbase_speech_articulation]
    call SpeechSetArticulation
__dbase_speech_on_done_26:
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov dword ptr [__dbase_speech_mix], 55
    cmp dword ptr [__dbase_speech_ready], 0
    je __dbase_speech_setting_skip_27
    push 55
    call SpeechSetMix
__dbase_speech_setting_skip_27:
    mov dword ptr [__dbase_speech_pitch], 125
    cmp dword ptr [__dbase_speech_ready], 0
    je __dbase_speech_setting_skip_28
    push 125
    call SpeechSetPitch
__dbase_speech_setting_skip_28:
    mov dword ptr [__dbase_speech_speed], 100
    cmp dword ptr [__dbase_speech_ready], 0
    je __dbase_speech_setting_skip_29
    push 100
    call SpeechSetSpeed
__dbase_speech_setting_skip_29:
    mov dword ptr [__dbase_speech_expression], 65
    cmp dword ptr [__dbase_speech_ready], 0
    je __dbase_speech_setting_skip_30
    push 65
    call SpeechSetExpression
__dbase_speech_setting_skip_30:
    mov dword ptr [__dbase_speech_articulation], 65
    cmp dword ptr [__dbase_speech_ready], 0
    je __dbase_speech_setting_skip_31
    push 65
    call SpeechSetArticulation
__dbase_speech_setting_skip_31:
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov dword ptr [__dbase_speech_mix], 55
    cmp dword ptr [__dbase_speech_ready], 0
    je __dbase_speech_setting_skip_32
    push 55
    call SpeechSetMix
__dbase_speech_setting_skip_32:
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov dword ptr [__dbase_speech_pitch], 125
    cmp dword ptr [__dbase_speech_ready], 0
    je __dbase_speech_setting_skip_33
    push 125
    call SpeechSetPitch
__dbase_speech_setting_skip_33:
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov dword ptr [__dbase_speech_speed], 100
    cmp dword ptr [__dbase_speech_ready], 0
    je __dbase_speech_setting_skip_34
    push 100
    call SpeechSetSpeed
__dbase_speech_setting_skip_34:
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    cmp dword ptr [__dbase_speech_ready], 0
    je __dbase_speech_say_done_35
    push __dbase_speech_utf8_36
    call SpeechSpeak
__dbase_speech_say_done_35:
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    call DBaseQtMarkProgramFinished
    call DBaseQtExec
    mov dword ptr [__dbase_exit_code], eax
__dbase_program_cleanup_1:
    cmp dword ptr [__dbase_speech_ready], 0
    je __dbase_speech_shutdown_done_37
    call SpeechShutdown
    mov dword ptr [__dbase_speech_ready], 0
__dbase_speech_shutdown_done_37:
    call DBaseQtShutdown
    call __dbase_console_shutdown
    mov eax, dword ptr [__dbase_format_buffer]
    test eax, eax
    je __dbase_format_buffer_free_done_38
    push 32768
    push 0
    push eax
    call VirtualFree
__dbase_format_buffer_free_done_38:
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

__dbase_speech_utf8_36:
    db 72, 97, 108, 108, 111, 44, 32, 105, 99, 104, 32, 98, 105, 110, 32, 100, 101, 105, 110, 32, 83, 112, 114, 97
    db 99, 104, 99, 111, 109, 112, 117, 116, 101, 114, 46, 0
__dbase_speech_mix:
    dd 55
__dbase_speech_pitch:
    dd 125
__dbase_speech_speed:
    dd 100
__dbase_speech_expression:
    dd 60
__dbase_speech_articulation:
    dd 65
__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_text_1:
    db 100, 66, 97, 115, 101, 32, 67, 111, 110, 115, 111, 108, 101, 32, 91, 77, 79, 68, 65, 76, 32, 84, 69, 83
    db 84, 93, 0
__dbase_text_2:
    db 13, 10
__dbase_text_3:
    db 115, 115, 115
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
    resd 1
__dbase_exit_code:
    resd 1
__dbase_output_format_screen:
    resd 1
__dbase_output_debug_visible:
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
__dbase_speech_ready:
    resd 1
