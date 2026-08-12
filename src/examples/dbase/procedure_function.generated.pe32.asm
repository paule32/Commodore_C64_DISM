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
    call DBaseQtAppendConsole
    add esp, 8
    fld qword ptr [__dbase_num_0]
    fstp qword ptr [__dbase_call_1_arg_0_num]
    mov dword ptr [__dbase_call_1_arg_0_type], 1
    fld qword ptr [__dbase_num_1]
    fstp qword ptr [__dbase_call_1_arg_1_num]
    mov dword ptr [__dbase_call_1_arg_1_type], 1
    mov eax, dword ptr [__dbase_call_1_arg_0_type]
    mov dword ptr [__dbase_function_add__number_number_param_0_a_type], eax
    mov eax, dword ptr [__dbase_call_1_arg_0_num]
    mov dword ptr [__dbase_function_add__number_number_param_0_a_num], eax
    mov eax, dword ptr [__dbase_call_1_arg_0_num+4]
    mov dword ptr [__dbase_function_add__number_number_param_0_a_num+4], eax
    mov eax, dword ptr [__dbase_call_1_arg_0_ptr]
    mov dword ptr [__dbase_function_add__number_number_param_0_a_ptr], eax
    mov eax, dword ptr [__dbase_call_1_arg_0_len]
    mov dword ptr [__dbase_function_add__number_number_param_0_a_len], eax
    mov eax, dword ptr [__dbase_call_1_arg_1_type]
    mov dword ptr [__dbase_function_add__number_number_param_1_b_type], eax
    mov eax, dword ptr [__dbase_call_1_arg_1_num]
    mov dword ptr [__dbase_function_add__number_number_param_1_b_num], eax
    mov eax, dword ptr [__dbase_call_1_arg_1_num+4]
    mov dword ptr [__dbase_function_add__number_number_param_1_b_num+4], eax
    mov eax, dword ptr [__dbase_call_1_arg_1_ptr]
    mov dword ptr [__dbase_function_add__number_number_param_1_b_ptr], eax
    mov eax, dword ptr [__dbase_call_1_arg_1_len]
    mov dword ptr [__dbase_function_add__number_number_param_1_b_len], eax
    call __dbase_function_add__number_number
    fld qword ptr [__dbase_function_add__number_number_result_num]
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
    push edx
    push dword ptr [__dbase_format_buffer]
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_2
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    fld qword ptr [__dbase_num_2]
    fstp qword ptr [__dbase_call_2_arg_0_num]
    mov dword ptr [__dbase_call_2_arg_0_type], 1
    mov eax, dword ptr [__dbase_call_2_arg_0_type]
    mov dword ptr [__dbase_function_label__number_param_0_value_type], eax
    mov eax, dword ptr [__dbase_call_2_arg_0_num]
    mov dword ptr [__dbase_function_label__number_param_0_value_num], eax
    mov eax, dword ptr [__dbase_call_2_arg_0_num+4]
    mov dword ptr [__dbase_function_label__number_param_0_value_num+4], eax
    mov eax, dword ptr [__dbase_call_2_arg_0_ptr]
    mov dword ptr [__dbase_function_label__number_param_0_value_ptr], eax
    mov eax, dword ptr [__dbase_call_2_arg_0_len]
    mov dword ptr [__dbase_function_label__number_param_0_value_len], eax
    call __dbase_function_label__number
    push dword ptr [__dbase_function_label__number_result_len]
    push dword ptr [__dbase_function_label__number_result_ptr]
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_2
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov eax, __dbase_text_3
    mov dword ptr [__dbase_call_3_arg_0_ptr], eax
    mov dword ptr [__dbase_call_3_arg_0_len], 13
    mov dword ptr [__dbase_call_3_arg_0_type], 2
    mov eax, dword ptr [__dbase_call_3_arg_0_type]
    mov dword ptr [__dbase_function_identity__string_param_0_value_type], eax
    mov eax, dword ptr [__dbase_call_3_arg_0_num]
    mov dword ptr [__dbase_function_identity__string_param_0_value_num], eax
    mov eax, dword ptr [__dbase_call_3_arg_0_num+4]
    mov dword ptr [__dbase_function_identity__string_param_0_value_num+4], eax
    mov eax, dword ptr [__dbase_call_3_arg_0_ptr]
    mov dword ptr [__dbase_function_identity__string_param_0_value_ptr], eax
    mov eax, dword ptr [__dbase_call_3_arg_0_len]
    mov dword ptr [__dbase_function_identity__string_param_0_value_len], eax
    call __dbase_function_identity__string
    push dword ptr [__dbase_function_identity__string_result_len]
    push dword ptr [__dbase_function_identity__string_result_ptr]
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_2
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov eax, __dbase_text_4
    mov dword ptr [__dbase_call_4_arg_0_ptr], eax
    mov dword ptr [__dbase_call_4_arg_0_len], 1
    mov dword ptr [__dbase_call_4_arg_0_type], 3
    mov eax, dword ptr [__dbase_call_4_arg_0_type]
    mov dword ptr [__dbase_function_identity__char_param_0_value_type], eax
    mov eax, dword ptr [__dbase_call_4_arg_0_num]
    mov dword ptr [__dbase_function_identity__char_param_0_value_num], eax
    mov eax, dword ptr [__dbase_call_4_arg_0_num+4]
    mov dword ptr [__dbase_function_identity__char_param_0_value_num+4], eax
    mov eax, dword ptr [__dbase_call_4_arg_0_ptr]
    mov dword ptr [__dbase_function_identity__char_param_0_value_ptr], eax
    mov eax, dword ptr [__dbase_call_4_arg_0_len]
    mov dword ptr [__dbase_function_identity__char_param_0_value_len], eax
    call __dbase_function_identity__char
    push dword ptr [__dbase_function_identity__char_result_len]
    push dword ptr [__dbase_function_identity__char_result_ptr]
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_2
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    fld qword ptr [__dbase_num_3]
    fstp qword ptr [__dbase_call_5_arg_0_num]
    mov dword ptr [__dbase_call_5_arg_0_type], 1
    fld qword ptr [__dbase_num_4]
    fstp qword ptr [__dbase_call_5_arg_1_num]
    mov dword ptr [__dbase_call_5_arg_1_type], 1
    mov eax, dword ptr [__dbase_call_5_arg_0_type]
    mov dword ptr [__dbase_procedure_show__number_number_param_0_a_type], eax
    mov eax, dword ptr [__dbase_call_5_arg_0_num]
    mov dword ptr [__dbase_procedure_show__number_number_param_0_a_num], eax
    mov eax, dword ptr [__dbase_call_5_arg_0_num+4]
    mov dword ptr [__dbase_procedure_show__number_number_param_0_a_num+4], eax
    mov eax, dword ptr [__dbase_call_5_arg_0_ptr]
    mov dword ptr [__dbase_procedure_show__number_number_param_0_a_ptr], eax
    mov eax, dword ptr [__dbase_call_5_arg_0_len]
    mov dword ptr [__dbase_procedure_show__number_number_param_0_a_len], eax
    mov eax, dword ptr [__dbase_call_5_arg_1_type]
    mov dword ptr [__dbase_procedure_show__number_number_param_1_b_type], eax
    mov eax, dword ptr [__dbase_call_5_arg_1_num]
    mov dword ptr [__dbase_procedure_show__number_number_param_1_b_num], eax
    mov eax, dword ptr [__dbase_call_5_arg_1_num+4]
    mov dword ptr [__dbase_procedure_show__number_number_param_1_b_num+4], eax
    mov eax, dword ptr [__dbase_call_5_arg_1_ptr]
    mov dword ptr [__dbase_procedure_show__number_number_param_1_b_ptr], eax
    mov eax, dword ptr [__dbase_call_5_arg_1_len]
    mov dword ptr [__dbase_procedure_show__number_number_param_1_b_len], eax
    call __dbase_procedure_show__number_number
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
    je __dbase_format_buffer_free_done_6
    push 32768
    push 0
    push eax
    call VirtualFree
__dbase_format_buffer_free_done_6:
    mov dword ptr [__dbase_format_buffer], 0
    push dword ptr [__dbase_exit_code]
    call ExitProcess

__dbase_function_add__number_number:
    fld qword ptr [__dbase_function_add__number_number_param_0_a_num]
    fld qword ptr [__dbase_function_add__number_number_param_1_b_num]
    faddp
    fstp qword ptr [__dbase_function_add__number_number_result_num]
    mov dword ptr [__dbase_function_add__number_number_result_type], 1
    jmp __dbase_function_add__number_number_end
__dbase_function_add__number_number_end:
    ret

__dbase_function_label__number:
    mov eax, __dbase_text_5
    mov dword ptr [__dbase_concat_left_7_ptr], eax
    mov dword ptr [__dbase_concat_left_7_len], 7
    mov dword ptr [__dbase_concat_left_7_type], 2
    fld qword ptr [__dbase_function_label__number_param_0_value_num]
    fstp qword ptr [__dbase_temp_number]
    push dword ptr [__dbase_format_buffer]
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, dword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_strlen_loop_9:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_strlen_done_10
    inc ecx
    inc edx
    jmp __dbase_strlen_loop_9
__dbase_strlen_done_10:
    mov dword ptr [__dbase_concat_right_8_len], edx
    mov eax, edx
    inc eax
    push eax
    call __dbase_malloc
    add esp, 4
    mov dword ptr [__dbase_concat_right_8_ptr], eax
    push dword ptr [__dbase_concat_right_8_len]
    push dword ptr [__dbase_format_buffer]
    push dword ptr [__dbase_concat_right_8_ptr]
    call __dbase_memcpy
    add esp, 12
    mov eax, dword ptr [__dbase_concat_right_8_ptr]
    add eax, dword ptr [__dbase_concat_right_8_len]
    mov byte ptr [eax], 0
    mov dword ptr [__dbase_concat_right_8_type], 2
    mov eax, dword ptr [__dbase_concat_left_7_len]
    add eax, dword ptr [__dbase_concat_right_8_len]
    mov dword ptr [__dbase_function_label__number_result_len], eax
    inc eax
    push eax
    call __dbase_malloc
    add esp, 4
    mov dword ptr [__dbase_function_label__number_result_ptr], eax
    push dword ptr [__dbase_concat_left_7_len]
    push dword ptr [__dbase_concat_left_7_ptr]
    push dword ptr [__dbase_function_label__number_result_ptr]
    call __dbase_memcpy
    add esp, 12
    mov eax, dword ptr [__dbase_function_label__number_result_ptr]
    add eax, dword ptr [__dbase_concat_left_7_len]
    push dword ptr [__dbase_concat_right_8_len]
    push dword ptr [__dbase_concat_right_8_ptr]
    push eax
    call __dbase_memcpy
    add esp, 12
    mov eax, dword ptr [__dbase_function_label__number_result_ptr]
    add eax, dword ptr [__dbase_function_label__number_result_len]
    mov byte ptr [eax], 0
    mov dword ptr [__dbase_function_label__number_result_type], 2
    jmp __dbase_function_label__number_end
__dbase_function_label__number_end:
    ret

__dbase_function_identity__string:
    mov eax, dword ptr [__dbase_function_identity__string_param_0_value_type]
    mov dword ptr [__dbase_function_identity__string_result_type], eax
    mov eax, dword ptr [__dbase_function_identity__string_param_0_value_num]
    mov dword ptr [__dbase_function_identity__string_result_num], eax
    mov eax, dword ptr [__dbase_function_identity__string_param_0_value_num+4]
    mov dword ptr [__dbase_function_identity__string_result_num+4], eax
    mov eax, dword ptr [__dbase_function_identity__string_param_0_value_ptr]
    mov dword ptr [__dbase_function_identity__string_result_ptr], eax
    mov eax, dword ptr [__dbase_function_identity__string_param_0_value_len]
    mov dword ptr [__dbase_function_identity__string_result_len], eax
    jmp __dbase_function_identity__string_end
__dbase_function_identity__string_end:
    ret

__dbase_function_identity__char:
    mov eax, dword ptr [__dbase_function_identity__char_param_0_value_type]
    mov dword ptr [__dbase_function_identity__char_result_type], eax
    mov eax, dword ptr [__dbase_function_identity__char_param_0_value_num]
    mov dword ptr [__dbase_function_identity__char_result_num], eax
    mov eax, dword ptr [__dbase_function_identity__char_param_0_value_num+4]
    mov dword ptr [__dbase_function_identity__char_result_num+4], eax
    mov eax, dword ptr [__dbase_function_identity__char_param_0_value_ptr]
    mov dword ptr [__dbase_function_identity__char_result_ptr], eax
    mov eax, dword ptr [__dbase_function_identity__char_param_0_value_len]
    mov dword ptr [__dbase_function_identity__char_result_len], eax
    jmp __dbase_function_identity__char_end
__dbase_function_identity__char_end:
    ret

__dbase_procedure_show__number_number:
    push 11
    push __dbase_text_6
    call DBaseQtAppendConsole
    add esp, 8
    fld qword ptr [__dbase_procedure_show__number_number_param_0_a_num]
    fld qword ptr [__dbase_procedure_show__number_number_param_1_b_num]
    faddp
    fstp qword ptr [__dbase_temp_number]
    push dword ptr [__dbase_format_buffer]
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, dword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_strlen_loop_11:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_strlen_done_12
    inc ecx
    inc edx
    jmp __dbase_strlen_loop_11
__dbase_strlen_done_12:
    push edx
    push dword ptr [__dbase_format_buffer]
    call DBaseQtAppendConsole
    add esp, 8
    push 2
    push __dbase_text_2
    call DBaseQtAppendConsole
    add esp, 8
    call DBaseQtProcessEvents
    jmp __dbase_procedure_show__number_number_end
__dbase_procedure_show__number_number_end:
    ret

section .data

__dbase_num_0:
    dd 0, 1073741824
__dbase_num_1:
    dd 0, 1074266112
__dbase_num_2:
    dd 0, 1076625408
__dbase_num_3:
    dd 0, 1076101120
__dbase_num_4:
    dd 0, 1077149696
__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_text_1:
    db 97, 100, 100, 40, 50, 44, 32, 51, 41, 32, 61, 32
__dbase_text_2:
    db 13, 10
__dbase_text_3:
    db 83, 116, 114, 105, 110, 103, 32, 82, 101, 116, 117, 114, 110
__dbase_text_4:
    db 65
__dbase_text_5:
    db 87, 101, 114, 116, 32, 61, 32
__dbase_text_6:
    db 80, 114, 111, 99, 101, 100, 117, 114, 101, 58, 32
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
__dbase_function_add__number_number_param_0_a_type:
    dd 0
__dbase_function_add__number_number_param_0_a_num:
    dd 0, 0
__dbase_function_add__number_number_param_0_a_ptr:
    dd 0
__dbase_function_add__number_number_param_0_a_len:
    dd 0
__dbase_function_add__number_number_param_1_b_type:
    dd 0
__dbase_function_add__number_number_param_1_b_num:
    dd 0, 0
__dbase_function_add__number_number_param_1_b_ptr:
    dd 0
__dbase_function_add__number_number_param_1_b_len:
    dd 0
__dbase_function_add__number_number_result_type:
    dd 0
__dbase_function_add__number_number_result_num:
    dd 0, 0
__dbase_function_add__number_number_result_ptr:
    dd 0
__dbase_function_add__number_number_result_len:
    dd 0
__dbase_call_1_arg_0_type:
    dd 0
__dbase_call_1_arg_0_num:
    dd 0, 0
__dbase_call_1_arg_0_ptr:
    dd 0
__dbase_call_1_arg_0_len:
    dd 0
__dbase_call_1_arg_1_type:
    dd 0
__dbase_call_1_arg_1_num:
    dd 0, 0
__dbase_call_1_arg_1_ptr:
    dd 0
__dbase_call_1_arg_1_len:
    dd 0
__dbase_function_label__number_param_0_value_type:
    dd 0
__dbase_function_label__number_param_0_value_num:
    dd 0, 0
__dbase_function_label__number_param_0_value_ptr:
    dd 0
__dbase_function_label__number_param_0_value_len:
    dd 0
__dbase_function_label__number_result_type:
    dd 0
__dbase_function_label__number_result_num:
    dd 0, 0
__dbase_function_label__number_result_ptr:
    dd 0
__dbase_function_label__number_result_len:
    dd 0
__dbase_call_2_arg_0_type:
    dd 0
__dbase_call_2_arg_0_num:
    dd 0, 0
__dbase_call_2_arg_0_ptr:
    dd 0
__dbase_call_2_arg_0_len:
    dd 0
__dbase_function_identity__string_param_0_value_type:
    dd 0
__dbase_function_identity__string_param_0_value_num:
    dd 0, 0
__dbase_function_identity__string_param_0_value_ptr:
    dd 0
__dbase_function_identity__string_param_0_value_len:
    dd 0
__dbase_function_identity__string_result_type:
    dd 0
__dbase_function_identity__string_result_num:
    dd 0, 0
__dbase_function_identity__string_result_ptr:
    dd 0
__dbase_function_identity__string_result_len:
    dd 0
__dbase_call_3_arg_0_type:
    dd 0
__dbase_call_3_arg_0_num:
    dd 0, 0
__dbase_call_3_arg_0_ptr:
    dd 0
__dbase_call_3_arg_0_len:
    dd 0
__dbase_function_identity__char_param_0_value_type:
    dd 0
__dbase_function_identity__char_param_0_value_num:
    dd 0, 0
__dbase_function_identity__char_param_0_value_ptr:
    dd 0
__dbase_function_identity__char_param_0_value_len:
    dd 0
__dbase_function_identity__char_result_type:
    dd 0
__dbase_function_identity__char_result_num:
    dd 0, 0
__dbase_function_identity__char_result_ptr:
    dd 0
__dbase_function_identity__char_result_len:
    dd 0
__dbase_call_4_arg_0_type:
    dd 0
__dbase_call_4_arg_0_num:
    dd 0, 0
__dbase_call_4_arg_0_ptr:
    dd 0
__dbase_call_4_arg_0_len:
    dd 0
__dbase_procedure_show__number_number_param_0_a_type:
    dd 0
__dbase_procedure_show__number_number_param_0_a_num:
    dd 0, 0
__dbase_procedure_show__number_number_param_0_a_ptr:
    dd 0
__dbase_procedure_show__number_number_param_0_a_len:
    dd 0
__dbase_procedure_show__number_number_param_1_b_type:
    dd 0
__dbase_procedure_show__number_number_param_1_b_num:
    dd 0, 0
__dbase_procedure_show__number_number_param_1_b_ptr:
    dd 0
__dbase_procedure_show__number_number_param_1_b_len:
    dd 0
__dbase_call_5_arg_0_type:
    dd 0
__dbase_call_5_arg_0_num:
    dd 0, 0
__dbase_call_5_arg_0_ptr:
    dd 0
__dbase_call_5_arg_0_len:
    dd 0
__dbase_call_5_arg_1_type:
    dd 0
__dbase_call_5_arg_1_num:
    dd 0, 0
__dbase_call_5_arg_1_ptr:
    dd 0
__dbase_call_5_arg_1_len:
    dd 0
__dbase_concat_left_7_type:
    dd 0
__dbase_concat_left_7_num:
    dd 0, 0
__dbase_concat_left_7_ptr:
    dd 0
__dbase_concat_left_7_len:
    dd 0
__dbase_concat_right_8_type:
    dd 0
__dbase_concat_right_8_num:
    dd 0, 0
__dbase_concat_right_8_ptr:
    dd 0
__dbase_concat_right_8_len:
    dd 0
