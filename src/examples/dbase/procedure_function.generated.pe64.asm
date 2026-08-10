bits 64

import DBaseQtInitialize, "d64qt5.dll", "DBaseQtInitialize"
import DBaseQtShowWindow, "d64qt5.dll", "DBaseQtShowWindow"
import DBaseQtProcessEvents, "d64qt5.dll", "DBaseQtProcessEvents"
import DBaseQtSetDebugVisible, "d64qt5.dll", "DBaseQtSetDebugVisible"
import DBaseQtAppendConsole, "d64qt5.dll", "DBaseQtAppendConsole"
import DBaseQtAppendDebug, "d64qt5.dll", "DBaseQtAppendDebug"
import DBaseQtMarkProgramFinished, "d64qt5.dll", "DBaseQtMarkProgramFinished"
import DBaseQtExec, "d64qt5.dll", "DBaseQtExec"
import DBaseQtShutdown, "d64qt5.dll", "DBaseQtShutdown"
import __dbase_gcvt, "msvcrt.dll", "_gcvt"
import __dbase_malloc, "msvcrt.dll", "malloc"
import __dbase_memcpy, "msvcrt.dll", "memcpy"
import ExitProcess, "kernel32.dll", "ExitProcess"
global _start
entry _start

section .text

_start:
    mov rcx, __dbase_text_0
    sub rsp, 40
    call DBaseQtInitialize
    add rsp, 40
    test eax, eax
    jne __dbase_qt_init_ok_1
    mov ecx, 1
    sub rsp, 40
    call ExitProcess
__dbase_qt_init_ok_1:
    sub rsp, 40
    call DBaseQtShowWindow
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    mov ecx, 0
    sub rsp, 40
    call DBaseQtSetDebugVisible
    add rsp, 40
    mov rcx, __dbase_text_1
    mov edx, 12
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
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
    mov rax, qword ptr [__dbase_call_1_arg_0_ptr]
    mov qword ptr [__dbase_function_add__number_number_param_0_a_ptr], rax
    mov eax, dword ptr [__dbase_call_1_arg_0_len]
    mov dword ptr [__dbase_function_add__number_number_param_0_a_len], eax
    mov eax, dword ptr [__dbase_call_1_arg_1_type]
    mov dword ptr [__dbase_function_add__number_number_param_1_b_type], eax
    mov eax, dword ptr [__dbase_call_1_arg_1_num]
    mov dword ptr [__dbase_function_add__number_number_param_1_b_num], eax
    mov eax, dword ptr [__dbase_call_1_arg_1_num+4]
    mov dword ptr [__dbase_function_add__number_number_param_1_b_num+4], eax
    mov rax, qword ptr [__dbase_call_1_arg_1_ptr]
    mov qword ptr [__dbase_function_add__number_number_param_1_b_ptr], rax
    mov eax, dword ptr [__dbase_call_1_arg_1_len]
    mov dword ptr [__dbase_function_add__number_number_param_1_b_len], eax
    sub rsp, 8
    call __dbase_function_add__number_number
    add rsp, 8
    fld qword ptr [__dbase_function_add__number_number_result_num]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, __dbase_format_buffer
    sub rsp, 40
    call __dbase_gcvt
    add rsp, 40
    mov rcx, __dbase_format_buffer
    xor edx, edx
__dbase_strlen_loop_2:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_strlen_done_3
    inc rcx
    inc edx
    jmp __dbase_strlen_loop_2
__dbase_strlen_done_3:
    mov rcx, __dbase_format_buffer
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_2
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    fld qword ptr [__dbase_num_2]
    fstp qword ptr [__dbase_call_2_arg_0_num]
    mov dword ptr [__dbase_call_2_arg_0_type], 1
    mov eax, dword ptr [__dbase_call_2_arg_0_type]
    mov dword ptr [__dbase_function_label__number_param_0_value_type], eax
    mov eax, dword ptr [__dbase_call_2_arg_0_num]
    mov dword ptr [__dbase_function_label__number_param_0_value_num], eax
    mov eax, dword ptr [__dbase_call_2_arg_0_num+4]
    mov dword ptr [__dbase_function_label__number_param_0_value_num+4], eax
    mov rax, qword ptr [__dbase_call_2_arg_0_ptr]
    mov qword ptr [__dbase_function_label__number_param_0_value_ptr], rax
    mov eax, dword ptr [__dbase_call_2_arg_0_len]
    mov dword ptr [__dbase_function_label__number_param_0_value_len], eax
    sub rsp, 8
    call __dbase_function_label__number
    add rsp, 8
    mov rcx, qword ptr [__dbase_function_label__number_result_ptr]
    mov edx, dword ptr [__dbase_function_label__number_result_len]
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_2
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    mov rax, __dbase_text_3
    mov qword ptr [__dbase_call_3_arg_0_ptr], rax
    mov dword ptr [__dbase_call_3_arg_0_len], 13
    mov dword ptr [__dbase_call_3_arg_0_type], 2
    mov eax, dword ptr [__dbase_call_3_arg_0_type]
    mov dword ptr [__dbase_function_identity__string_param_0_value_type], eax
    mov eax, dword ptr [__dbase_call_3_arg_0_num]
    mov dword ptr [__dbase_function_identity__string_param_0_value_num], eax
    mov eax, dword ptr [__dbase_call_3_arg_0_num+4]
    mov dword ptr [__dbase_function_identity__string_param_0_value_num+4], eax
    mov rax, qword ptr [__dbase_call_3_arg_0_ptr]
    mov qword ptr [__dbase_function_identity__string_param_0_value_ptr], rax
    mov eax, dword ptr [__dbase_call_3_arg_0_len]
    mov dword ptr [__dbase_function_identity__string_param_0_value_len], eax
    sub rsp, 8
    call __dbase_function_identity__string
    add rsp, 8
    mov rcx, qword ptr [__dbase_function_identity__string_result_ptr]
    mov edx, dword ptr [__dbase_function_identity__string_result_len]
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_2
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
    mov rax, __dbase_text_4
    mov qword ptr [__dbase_call_4_arg_0_ptr], rax
    mov dword ptr [__dbase_call_4_arg_0_len], 1
    mov dword ptr [__dbase_call_4_arg_0_type], 3
    mov eax, dword ptr [__dbase_call_4_arg_0_type]
    mov dword ptr [__dbase_function_identity__char_param_0_value_type], eax
    mov eax, dword ptr [__dbase_call_4_arg_0_num]
    mov dword ptr [__dbase_function_identity__char_param_0_value_num], eax
    mov eax, dword ptr [__dbase_call_4_arg_0_num+4]
    mov dword ptr [__dbase_function_identity__char_param_0_value_num+4], eax
    mov rax, qword ptr [__dbase_call_4_arg_0_ptr]
    mov qword ptr [__dbase_function_identity__char_param_0_value_ptr], rax
    mov eax, dword ptr [__dbase_call_4_arg_0_len]
    mov dword ptr [__dbase_function_identity__char_param_0_value_len], eax
    sub rsp, 8
    call __dbase_function_identity__char
    add rsp, 8
    mov rcx, qword ptr [__dbase_function_identity__char_result_ptr]
    mov edx, dword ptr [__dbase_function_identity__char_result_len]
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_2
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
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
    mov rax, qword ptr [__dbase_call_5_arg_0_ptr]
    mov qword ptr [__dbase_procedure_show__number_number_param_0_a_ptr], rax
    mov eax, dword ptr [__dbase_call_5_arg_0_len]
    mov dword ptr [__dbase_procedure_show__number_number_param_0_a_len], eax
    mov eax, dword ptr [__dbase_call_5_arg_1_type]
    mov dword ptr [__dbase_procedure_show__number_number_param_1_b_type], eax
    mov eax, dword ptr [__dbase_call_5_arg_1_num]
    mov dword ptr [__dbase_procedure_show__number_number_param_1_b_num], eax
    mov eax, dword ptr [__dbase_call_5_arg_1_num+4]
    mov dword ptr [__dbase_procedure_show__number_number_param_1_b_num+4], eax
    mov rax, qword ptr [__dbase_call_5_arg_1_ptr]
    mov qword ptr [__dbase_procedure_show__number_number_param_1_b_ptr], rax
    mov eax, dword ptr [__dbase_call_5_arg_1_len]
    mov dword ptr [__dbase_procedure_show__number_number_param_1_b_len], eax
    sub rsp, 8
    call __dbase_procedure_show__number_number
    add rsp, 8
    sub rsp, 40
    call DBaseQtMarkProgramFinished
    add rsp, 40
    sub rsp, 40
    call DBaseQtExec
    add rsp, 40
    mov dword ptr [__dbase_exit_code], eax
    sub rsp, 40
    call DBaseQtShutdown
    add rsp, 40
    mov ecx, dword ptr [__dbase_exit_code]
    sub rsp, 40
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
    mov rax, __dbase_text_5
    mov qword ptr [__dbase_concat_left_4_ptr], rax
    mov dword ptr [__dbase_concat_left_4_len], 7
    mov dword ptr [__dbase_concat_left_4_type], 2
    fld qword ptr [__dbase_function_label__number_param_0_value_num]
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, __dbase_format_buffer
    sub rsp, 40
    call __dbase_gcvt
    add rsp, 40
    mov rcx, __dbase_format_buffer
    xor edx, edx
__dbase_strlen_loop_6:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_strlen_done_7
    inc rcx
    inc edx
    jmp __dbase_strlen_loop_6
__dbase_strlen_done_7:
    mov dword ptr [__dbase_concat_right_5_len], edx
    mov eax, edx
    inc eax
    mov ecx, eax
    sub rsp, 40
    call __dbase_malloc
    add rsp, 40
    mov qword ptr [__dbase_concat_right_5_ptr], rax
    mov rcx, rax
    mov rdx, __dbase_format_buffer
    mov r8d, dword ptr [__dbase_concat_right_5_len]
    sub rsp, 40
    call __dbase_memcpy
    add rsp, 40
    mov rax, qword ptr [__dbase_concat_right_5_ptr]
    mov edx, dword ptr [__dbase_concat_right_5_len]
    add rax, rdx
    mov byte ptr [rax], 0
    mov dword ptr [__dbase_concat_right_5_type], 2
    mov eax, dword ptr [__dbase_concat_left_4_len]
    add eax, dword ptr [__dbase_concat_right_5_len]
    mov dword ptr [__dbase_function_label__number_result_len], eax
    inc eax
    mov ecx, eax
    sub rsp, 40
    call __dbase_malloc
    add rsp, 40
    mov qword ptr [__dbase_function_label__number_result_ptr], rax
    mov rcx, rax
    mov rdx, qword ptr [__dbase_concat_left_4_ptr]
    mov r8d, dword ptr [__dbase_concat_left_4_len]
    sub rsp, 40
    call __dbase_memcpy
    add rsp, 40
    mov rcx, qword ptr [__dbase_function_label__number_result_ptr]
    mov eax, dword ptr [__dbase_concat_left_4_len]
    add rcx, rax
    mov rdx, qword ptr [__dbase_concat_right_5_ptr]
    mov r8d, dword ptr [__dbase_concat_right_5_len]
    sub rsp, 40
    call __dbase_memcpy
    add rsp, 40
    mov rax, qword ptr [__dbase_function_label__number_result_ptr]
    mov edx, dword ptr [__dbase_function_label__number_result_len]
    add rax, rdx
    mov byte ptr [rax], 0
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
    mov rax, qword ptr [__dbase_function_identity__string_param_0_value_ptr]
    mov qword ptr [__dbase_function_identity__string_result_ptr], rax
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
    mov rax, qword ptr [__dbase_function_identity__char_param_0_value_ptr]
    mov qword ptr [__dbase_function_identity__char_result_ptr], rax
    mov eax, dword ptr [__dbase_function_identity__char_param_0_value_len]
    mov dword ptr [__dbase_function_identity__char_result_len], eax
    jmp __dbase_function_identity__char_end
__dbase_function_identity__char_end:
    ret

__dbase_procedure_show__number_number:
    mov rcx, __dbase_text_6
    mov edx, 11
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    fld qword ptr [__dbase_procedure_show__number_number_param_0_a_num]
    fld qword ptr [__dbase_procedure_show__number_number_param_1_b_num]
    faddp
    fstp qword ptr [__dbase_temp_number]
    movsd xmm0, qword ptr [__dbase_temp_number]
    mov edx, 15
    mov r8, __dbase_format_buffer
    sub rsp, 40
    call __dbase_gcvt
    add rsp, 40
    mov rcx, __dbase_format_buffer
    xor edx, edx
__dbase_strlen_loop_8:
    movzx eax, byte ptr [rcx]
    test eax, eax
    je __dbase_strlen_done_9
    inc rcx
    inc edx
    jmp __dbase_strlen_loop_8
__dbase_strlen_done_9:
    mov rcx, __dbase_format_buffer
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    mov rcx, __dbase_text_2
    mov edx, 2
    sub rsp, 40
    call DBaseQtAppendConsole
    add rsp, 40
    sub rsp, 40
    call DBaseQtProcessEvents
    add rsp, 40
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
    db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
__dbase_exit_code:
    dd 0
__dbase_function_add__number_number_param_0_a_type:
    dd 0
__dbase_function_add__number_number_param_0_a_num:
    dd 0, 0
__dbase_function_add__number_number_param_0_a_ptr:
    dd 0, 0
__dbase_function_add__number_number_param_0_a_len:
    dd 0
__dbase_function_add__number_number_param_1_b_type:
    dd 0
__dbase_function_add__number_number_param_1_b_num:
    dd 0, 0
__dbase_function_add__number_number_param_1_b_ptr:
    dd 0, 0
__dbase_function_add__number_number_param_1_b_len:
    dd 0
__dbase_function_add__number_number_result_type:
    dd 0
__dbase_function_add__number_number_result_num:
    dd 0, 0
__dbase_function_add__number_number_result_ptr:
    dd 0, 0
__dbase_function_add__number_number_result_len:
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
__dbase_function_label__number_param_0_value_type:
    dd 0
__dbase_function_label__number_param_0_value_num:
    dd 0, 0
__dbase_function_label__number_param_0_value_ptr:
    dd 0, 0
__dbase_function_label__number_param_0_value_len:
    dd 0
__dbase_function_label__number_result_type:
    dd 0
__dbase_function_label__number_result_num:
    dd 0, 0
__dbase_function_label__number_result_ptr:
    dd 0, 0
__dbase_function_label__number_result_len:
    dd 0
__dbase_call_2_arg_0_type:
    dd 0
__dbase_call_2_arg_0_num:
    dd 0, 0
__dbase_call_2_arg_0_ptr:
    dd 0, 0
__dbase_call_2_arg_0_len:
    dd 0
__dbase_function_identity__string_param_0_value_type:
    dd 0
__dbase_function_identity__string_param_0_value_num:
    dd 0, 0
__dbase_function_identity__string_param_0_value_ptr:
    dd 0, 0
__dbase_function_identity__string_param_0_value_len:
    dd 0
__dbase_function_identity__string_result_type:
    dd 0
__dbase_function_identity__string_result_num:
    dd 0, 0
__dbase_function_identity__string_result_ptr:
    dd 0, 0
__dbase_function_identity__string_result_len:
    dd 0
__dbase_call_3_arg_0_type:
    dd 0
__dbase_call_3_arg_0_num:
    dd 0, 0
__dbase_call_3_arg_0_ptr:
    dd 0, 0
__dbase_call_3_arg_0_len:
    dd 0
__dbase_function_identity__char_param_0_value_type:
    dd 0
__dbase_function_identity__char_param_0_value_num:
    dd 0, 0
__dbase_function_identity__char_param_0_value_ptr:
    dd 0, 0
__dbase_function_identity__char_param_0_value_len:
    dd 0
__dbase_function_identity__char_result_type:
    dd 0
__dbase_function_identity__char_result_num:
    dd 0, 0
__dbase_function_identity__char_result_ptr:
    dd 0, 0
__dbase_function_identity__char_result_len:
    dd 0
__dbase_call_4_arg_0_type:
    dd 0
__dbase_call_4_arg_0_num:
    dd 0, 0
__dbase_call_4_arg_0_ptr:
    dd 0, 0
__dbase_call_4_arg_0_len:
    dd 0
__dbase_procedure_show__number_number_param_0_a_type:
    dd 0
__dbase_procedure_show__number_number_param_0_a_num:
    dd 0, 0
__dbase_procedure_show__number_number_param_0_a_ptr:
    dd 0, 0
__dbase_procedure_show__number_number_param_0_a_len:
    dd 0
__dbase_procedure_show__number_number_param_1_b_type:
    dd 0
__dbase_procedure_show__number_number_param_1_b_num:
    dd 0, 0
__dbase_procedure_show__number_number_param_1_b_ptr:
    dd 0, 0
__dbase_procedure_show__number_number_param_1_b_len:
    dd 0
__dbase_call_5_arg_0_type:
    dd 0
__dbase_call_5_arg_0_num:
    dd 0, 0
__dbase_call_5_arg_0_ptr:
    dd 0, 0
__dbase_call_5_arg_0_len:
    dd 0
__dbase_call_5_arg_1_type:
    dd 0
__dbase_call_5_arg_1_num:
    dd 0, 0
__dbase_call_5_arg_1_ptr:
    dd 0, 0
__dbase_call_5_arg_1_len:
    dd 0
__dbase_concat_left_4_type:
    dd 0
__dbase_concat_left_4_num:
    dd 0, 0
__dbase_concat_left_4_ptr:
    dd 0, 0
__dbase_concat_left_4_len:
    dd 0
__dbase_concat_right_5_type:
    dd 0
__dbase_concat_right_5_num:
    dd 0, 0
__dbase_concat_right_5_ptr:
    dd 0, 0
__dbase_concat_right_5_len:
    dd 0
