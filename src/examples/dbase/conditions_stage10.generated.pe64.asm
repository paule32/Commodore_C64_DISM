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
    fld qword ptr [__dbase_num_0]
    fstp qword ptr [__dbase_var_x_num]
    mov dword ptr [__dbase_var_x_type], 1
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rax, __dbase_text_1
    mov qword ptr [__dbase_var_s_ptr], rax
    mov dword ptr [__dbase_var_s_len], 3
    mov dword ptr [__dbase_var_s_type], 2
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    fld qword ptr [__dbase_var_x_num]
    fld qword ptr [__dbase_num_1]
    fucomip st0, st1
    fstp st0
    jbe __dbase_if_next_5
    mov rcx, __dbase_text_2
    mov edx, 13
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_3
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    jmp __dbase_if_end_4
__dbase_if_next_5:
    fld qword ptr [__dbase_var_x_num]
    fld qword ptr [__dbase_num_0]
    fucomip st0, st1
    fstp st0
    jne __dbase_if_next_6
    mov rcx, __dbase_text_4
    mov edx, 8
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_3
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov eax, dword ptr [__dbase_var_s_type]
    mov dword ptr [__dbase_if_left_text_9_type], eax
    mov eax, dword ptr [__dbase_var_s_num]
    mov dword ptr [__dbase_if_left_text_9_num], eax
    mov eax, dword ptr [__dbase_var_s_num+4]
    mov dword ptr [__dbase_if_left_text_9_num+4], eax
    mov rax, qword ptr [__dbase_var_s_ptr]
    mov qword ptr [__dbase_if_left_text_9_ptr], rax
    mov eax, dword ptr [__dbase_var_s_len]
    mov dword ptr [__dbase_if_left_text_9_len], eax
    mov rax, __dbase_text_5
    mov qword ptr [__dbase_if_right_text_10_ptr], rax
    mov dword ptr [__dbase_if_right_text_10_len], 3
    mov dword ptr [__dbase_if_right_text_10_type], 2
    mov eax, dword ptr [__dbase_if_left_text_9_len]
    mov ecx, dword ptr [__dbase_if_right_text_10_len]
    cmp eax, ecx
    jbe __dbase_if_text_min_ready_11
    mov eax, ecx
__dbase_if_text_min_ready_11:
    mov r8d, eax
    mov rcx, qword ptr [__dbase_if_left_text_9_ptr]
    mov rdx, qword ptr [__dbase_if_right_text_10_ptr]
    sub rsp, 40
    call __dbase_memcmp
    add rsp, 40
    cmp eax, 0
    jne __dbase_if_text_result_ready_12
    mov eax, dword ptr [__dbase_if_left_text_9_len]
    sub eax, dword ptr [__dbase_if_right_text_10_len]
__dbase_if_text_result_ready_12:
    cmp eax, 0
    jge __dbase_if_next_8
    mov rcx, __dbase_text_6
    mov edx, 31
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_3
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    jmp __dbase_if_end_7
__dbase_if_next_8:
__dbase_if_end_7:
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    jmp __dbase_if_end_4
__dbase_if_next_6:
    mov rcx, __dbase_text_7
    mov edx, 12
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_3
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    jmp __dbase_if_end_4
__dbase_if_end_4:
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    fld qword ptr [__dbase_num_2]
    fld qword ptr [__dbase_num_2]
    fucomip st0, st1
    fstp st0
    ja __dbase_if_next_14
    mov rcx, __dbase_text_8
    mov edx, 16
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_3
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    jmp __dbase_if_end_13
__dbase_if_next_14:
__dbase_if_end_13:
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    fld qword ptr [__dbase_num_3]
    fld qword ptr [__dbase_num_4]
    fucomip st0, st1
    fstp st0
    jbe __dbase_if_next_16
    mov rcx, __dbase_text_9
    mov edx, 18
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_3
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    jmp __dbase_if_end_15
__dbase_if_next_16:
__dbase_if_end_15:
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rax, __dbase_text_10
    mov qword ptr [__dbase_if_left_text_19_ptr], rax
    mov dword ptr [__dbase_if_left_text_19_len], 1
    mov dword ptr [__dbase_if_left_text_19_type], 3
    mov rax, __dbase_text_11
    mov qword ptr [__dbase_if_right_text_20_ptr], rax
    mov dword ptr [__dbase_if_right_text_20_len], 1
    mov dword ptr [__dbase_if_right_text_20_type], 3
    mov eax, dword ptr [__dbase_if_left_text_19_len]
    mov ecx, dword ptr [__dbase_if_right_text_20_len]
    cmp eax, ecx
    jbe __dbase_if_text_min_ready_21
    mov eax, ecx
__dbase_if_text_min_ready_21:
    mov r8d, eax
    mov rcx, qword ptr [__dbase_if_left_text_19_ptr]
    mov rdx, qword ptr [__dbase_if_right_text_20_ptr]
    sub rsp, 40
    call __dbase_memcmp
    add rsp, 40
    cmp eax, 0
    jne __dbase_if_text_result_ready_22
    mov eax, dword ptr [__dbase_if_left_text_19_len]
    sub eax, dword ptr [__dbase_if_right_text_20_len]
__dbase_if_text_result_ready_22:
    cmp eax, 0
    je __dbase_if_next_18
    mov rcx, __dbase_text_12
    mov edx, 19
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_3
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    jmp __dbase_if_end_17
__dbase_if_next_18:
__dbase_if_end_17:
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    mov rcx, __dbase_text_13
    mov edx, 4
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    fld qword ptr [__dbase_num_5]
    fstp qword ptr [__dbase_call_1_arg_0_num]
    mov dword ptr [__dbase_call_1_arg_0_type], 1
    fld qword ptr [__dbase_num_4]
    fstp qword ptr [__dbase_call_1_arg_1_num]
    mov dword ptr [__dbase_call_1_arg_1_type], 1
    mov eax, dword ptr [__dbase_call_1_arg_0_type]
    mov dword ptr [__dbase_function_max2__number_number_param_0_a_type], eax
    mov eax, dword ptr [__dbase_call_1_arg_0_num]
    mov dword ptr [__dbase_function_max2__number_number_param_0_a_num], eax
    mov eax, dword ptr [__dbase_call_1_arg_0_num+4]
    mov dword ptr [__dbase_function_max2__number_number_param_0_a_num+4], eax
    mov rax, qword ptr [__dbase_call_1_arg_0_ptr]
    mov qword ptr [__dbase_function_max2__number_number_param_0_a_ptr], rax
    mov eax, dword ptr [__dbase_call_1_arg_0_len]
    mov dword ptr [__dbase_function_max2__number_number_param_0_a_len], eax
    mov eax, dword ptr [__dbase_call_1_arg_1_type]
    mov dword ptr [__dbase_function_max2__number_number_param_1_b_type], eax
    mov eax, dword ptr [__dbase_call_1_arg_1_num]
    mov dword ptr [__dbase_function_max2__number_number_param_1_b_num], eax
    mov eax, dword ptr [__dbase_call_1_arg_1_num+4]
    mov dword ptr [__dbase_function_max2__number_number_param_1_b_num+4], eax
    mov rax, qword ptr [__dbase_call_1_arg_1_ptr]
    mov qword ptr [__dbase_function_max2__number_number_param_1_b_ptr], rax
    mov eax, dword ptr [__dbase_call_1_arg_1_len]
    mov dword ptr [__dbase_function_max2__number_number_param_1_b_len], eax
    sub rsp, 8
    call __dbase_function_max2__number_number
    add rsp, 8
    fld qword ptr [__dbase_function_max2__number_number_result_num]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, qword ptr [__dbase_format_buffer]
    sub rsp, 40
    call __dbase_gcvt
    add rsp, 40
    mov rcx, qword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_strlen_loop_23:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_strlen_done_24
    inc rcx
    inc edx
    jmp __dbase_strlen_loop_23
__dbase_strlen_done_24:
    mov rcx, qword ptr [__dbase_format_buffer]
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_3
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    sub rsp, 40
    call DBaseQtShutdownRequested
    add rsp, 40
    test eax, eax
    jne __dbase_program_cleanup_1
    fld qword ptr [__dbase_num_6]
    fstp qword ptr [__dbase_call_2_arg_0_num]
    mov dword ptr [__dbase_call_2_arg_0_type], 1
    mov eax, dword ptr [__dbase_call_2_arg_0_type]
    mov dword ptr [__dbase_procedure_show__number_param_0_value_type], eax
    mov eax, dword ptr [__dbase_call_2_arg_0_num]
    mov dword ptr [__dbase_procedure_show__number_param_0_value_num], eax
    mov eax, dword ptr [__dbase_call_2_arg_0_num+4]
    mov dword ptr [__dbase_procedure_show__number_param_0_value_num+4], eax
    mov rax, qword ptr [__dbase_call_2_arg_0_ptr]
    mov qword ptr [__dbase_procedure_show__number_param_0_value_ptr], rax
    mov eax, dword ptr [__dbase_call_2_arg_0_len]
    mov dword ptr [__dbase_procedure_show__number_param_0_value_len], eax
    sub rsp, 8
    call __dbase_procedure_show__number
    add rsp, 8
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
    je __dbase_format_buffer_free_done_25
    xor edx, edx
    mov r8d, 32768
    sub rsp, 40
    call VirtualFree
    add rsp, 40
__dbase_format_buffer_free_done_25:
    mov qword ptr [__dbase_format_buffer], 0
    mov ecx, dword ptr [__dbase_exit_code]
    sub rsp, 40
    call ExitProcess

__dbase_function_max2__number_number:
    fld qword ptr [__dbase_function_max2__number_number_param_0_a_num]
    fld qword ptr [__dbase_function_max2__number_number_param_1_b_num]
    fucomip st0, st1
    fstp st0
    ja __dbase_if_next_27
    fld qword ptr [__dbase_function_max2__number_number_param_0_a_num]
    fstp qword ptr [__dbase_function_max2__number_number_result_num]
    mov dword ptr [__dbase_function_max2__number_number_result_type], 1
    jmp __dbase_function_max2__number_number_end
    jmp __dbase_if_end_26
__dbase_if_next_27:
__dbase_if_end_26:
    fld qword ptr [__dbase_function_max2__number_number_param_1_b_num]
    fstp qword ptr [__dbase_function_max2__number_number_result_num]
    mov dword ptr [__dbase_function_max2__number_number_result_type], 1
    jmp __dbase_function_max2__number_number_end
__dbase_function_max2__number_number_end:
    ret

__dbase_procedure_show__number:
    mov rcx, __dbase_text_14
    mov edx, 6
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    fld qword ptr [__dbase_procedure_show__number_param_0_value_num]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, qword ptr [__dbase_format_buffer]
    sub rsp, 40
    call __dbase_gcvt
    add rsp, 40
    mov rcx, qword ptr [__dbase_format_buffer]
    xor edx, edx
__dbase_strlen_loop_28:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_strlen_done_29
    inc rcx
    inc edx
    jmp __dbase_strlen_loop_28
__dbase_strlen_done_29:
    mov rcx, qword ptr [__dbase_format_buffer]
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_3
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    jmp __dbase_procedure_show__number_end
__dbase_procedure_show__number_end:
    ret

section .data

__dbase_num_0:
    dd 0, 1076625408
__dbase_num_1:
    dd 0, 0
__dbase_num_2:
    dd 0, 1076887552
__dbase_num_3:
    dd 0, 1074003968
__dbase_num_4:
    dd 0, 1074266112
__dbase_num_5:
    dd 0, 1075576832
__dbase_num_6:
    dd 0, 1075970048
__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_text_1:
    db 97, 98, 99
__dbase_text_2:
    db 88, 32, 105, 115, 116, 32, 110, 101, 103, 97, 116, 105, 118
__dbase_text_3:
    db 13, 10
__dbase_text_4:
    db 88, 32, 105, 115, 116, 32, 49, 52
__dbase_text_5:
    db 97, 98, 100
__dbase_text_6:
    db 83, 32, 108, 105, 101, 103, 116, 32, 108, 101, 120, 105, 107, 111, 103, 114, 97, 112, 104, 105, 115, 99, 104, 32
    db 118, 111, 114, 32, 97, 98, 100
__dbase_text_7:
    db 97, 110, 100, 101, 114, 101, 114, 32, 87, 101, 114, 116
__dbase_text_8:
    db 72, 101, 120, 45, 86, 101, 114, 103, 108, 101, 105, 99, 104, 32, 79, 75
__dbase_text_9:
    db 70, 108, 111, 97, 116, 45, 86, 101, 114, 103, 108, 101, 105, 99, 104, 32, 79, 75
__dbase_text_10:
    db 65
__dbase_text_11:
    db 66
__dbase_text_12:
    db 35, 32, 98, 101, 100, 101, 117, 116, 101, 116, 32, 117, 110, 103, 108, 101, 105, 99, 104
__dbase_text_13:
    db 109, 97, 120, 61
__dbase_text_14:
    db 118, 97, 108, 117, 101, 61
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
__dbase_var_x_type:
    dd 0
__dbase_var_x_num:
    dd 0, 0
__dbase_var_x_ptr:
    dd 0, 0
__dbase_var_x_len:
    dd 0
__dbase_var_s_type:
    dd 0
__dbase_var_s_num:
    dd 0, 0
__dbase_var_s_ptr:
    dd 0, 0
__dbase_var_s_len:
    dd 0
__dbase_function_max2__number_number_param_0_a_type:
    dd 0
__dbase_function_max2__number_number_param_0_a_num:
    dd 0, 0
__dbase_function_max2__number_number_param_0_a_ptr:
    dd 0, 0
__dbase_function_max2__number_number_param_0_a_len:
    dd 0
__dbase_function_max2__number_number_param_1_b_type:
    dd 0
__dbase_function_max2__number_number_param_1_b_num:
    dd 0, 0
__dbase_function_max2__number_number_param_1_b_ptr:
    dd 0, 0
__dbase_function_max2__number_number_param_1_b_len:
    dd 0
__dbase_function_max2__number_number_result_type:
    dd 0
__dbase_function_max2__number_number_result_num:
    dd 0, 0
__dbase_function_max2__number_number_result_ptr:
    dd 0, 0
__dbase_function_max2__number_number_result_len:
    dd 0
__dbase_call_1_arg_0_type:
    dd 0
__dbase_call_1_arg_0_num:
    dd 0, 0
__dbase_call_1_arg_0_ptr:
    dd 0, 0
__dbase_call_1_arg_0_len:
    dd 0
__dbase_call_1_arg_1_type:
    dd 0
__dbase_call_1_arg_1_num:
    dd 0, 0
__dbase_call_1_arg_1_ptr:
    dd 0, 0
__dbase_call_1_arg_1_len:
    dd 0
__dbase_procedure_show__number_param_0_value_type:
    dd 0
__dbase_procedure_show__number_param_0_value_num:
    dd 0, 0
__dbase_procedure_show__number_param_0_value_ptr:
    dd 0, 0
__dbase_procedure_show__number_param_0_value_len:
    dd 0
__dbase_call_2_arg_0_type:
    dd 0
__dbase_call_2_arg_0_num:
    dd 0, 0
__dbase_call_2_arg_0_ptr:
    dd 0, 0
__dbase_call_2_arg_0_len:
    dd 0
__dbase_if_left_text_9_type:
    dd 0
__dbase_if_left_text_9_num:
    dd 0, 0
__dbase_if_left_text_9_ptr:
    dd 0, 0
__dbase_if_left_text_9_len:
    dd 0
__dbase_if_right_text_10_type:
    dd 0
__dbase_if_right_text_10_num:
    dd 0, 0
__dbase_if_right_text_10_ptr:
    dd 0, 0
__dbase_if_right_text_10_len:
    dd 0
__dbase_if_left_text_19_type:
    dd 0
__dbase_if_left_text_19_num:
    dd 0, 0
__dbase_if_left_text_19_ptr:
    dd 0, 0
__dbase_if_left_text_19_len:
    dd 0
__dbase_if_right_text_20_type:
    dd 0
__dbase_if_right_text_20_num:
    dd 0, 0
__dbase_if_right_text_20_ptr:
    dd 0, 0
__dbase_if_right_text_20_len:
    dd 0
