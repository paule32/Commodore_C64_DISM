bits 32

import GetStdHandle, "kernel32.dll", "GetStdHandle"
import WriteFile, "kernel32.dll", "WriteFile"
import __dbase_gcvt, "msvcrt.dll", "_gcvt"
import ExitProcess, "kernel32.dll", "ExitProcess"
global _start
entry _start

section .text

_start:
    push -11
    call GetStdHandle
    mov dword ptr [__dbase_stdout], eax
    push -12
    call GetStdHandle
    mov dword ptr [__dbase_stderr], eax
    fld qword ptr [__dbase_num_0]
    fld qword ptr [__dbase_num_1]
    fld qword ptr [__dbase_num_2]
    fmulp
    faddp
    fld qword ptr [__dbase_num_3]
    fmulp
    fstp qword ptr [__dbase_var_x_num]
    mov dword ptr [__dbase_var_x_type], 1
    push 0
    push __dbase_written
    push 13
    push __dbase_text_0
    push dword ptr [__dbase_stdout]
    call WriteFile
    fld qword ptr [__dbase_var_x_num]
    fstp qword ptr [__dbase_temp_number]
    push __dbase_format_buffer
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, __dbase_format_buffer
    xor edx, edx
__dbase_strlen_loop_1:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_strlen_done_2
    inc ecx
    inc edx
    jmp __dbase_strlen_loop_1
__dbase_strlen_done_2:
    push 0
    push __dbase_written
    push edx
    push __dbase_format_buffer
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 2
    push __dbase_text_1
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 22
    push __dbase_text_2
    push dword ptr [__dbase_stdout]
    call WriteFile
    fld qword ptr [__dbase_var_x_num]
    fstp qword ptr [__dbase_temp_number]
    push __dbase_format_buffer
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, __dbase_format_buffer
    xor edx, edx
__dbase_strlen_loop_3:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_strlen_done_4
    inc ecx
    inc edx
    jmp __dbase_strlen_loop_3
__dbase_strlen_done_4:
    push 0
    push __dbase_written
    push edx
    push __dbase_format_buffer
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 2
    push __dbase_text_1
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 11
    push __dbase_text_3
    push dword ptr [__dbase_stderr]
    call WriteFile
    fld qword ptr [__dbase_var_x_num]
    fstp qword ptr [__dbase_temp_number]
    push __dbase_format_buffer
    push 15
    push dword ptr [__dbase_temp_number_hi]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, __dbase_format_buffer
    xor edx, edx
__dbase_strlen_loop_5:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_strlen_done_6
    inc ecx
    inc edx
    jmp __dbase_strlen_loop_5
__dbase_strlen_done_6:
    push 0
    push __dbase_written
    push edx
    push __dbase_format_buffer
    push dword ptr [__dbase_stderr]
    call WriteFile
    push 0
    push __dbase_written
    push 2
    push __dbase_text_1
    push dword ptr [__dbase_stderr]
    call WriteFile
    push 0
    push __dbase_written
    push 18
    push __dbase_text_4
    push dword ptr [__dbase_stderr]
    call WriteFile
    push 0
    push __dbase_written
    push 11
    push __dbase_text_5
    push dword ptr [__dbase_stderr]
    call WriteFile
    push 0
    push __dbase_written
    push 2
    push __dbase_text_1
    push dword ptr [__dbase_stderr]
    call WriteFile
    push 0
    push __dbase_written
    push 21
    push __dbase_text_6
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 2
    push __dbase_text_1
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    call ExitProcess

section .data

__dbase_num_0:
    dd 0, 1073741824
__dbase_num_1:
    dd 0, 1074266112
__dbase_num_2:
    dd 0, 1074790400
__dbase_num_3:
    dd 0, 1071644672
__dbase_text_0:
    db 87, 101, 114, 116, 32, 118, 111, 110, 32, 88, 32, 61, 32
__dbase_text_1:
    db 13, 10
__dbase_text_2:
    db 75, 111, 110, 115, 111, 108, 101, 32, 111, 104, 110, 101, 32, 78, 101, 119, 76, 105, 110, 101, 58, 32
__dbase_text_3:
    db 68, 69, 66, 85, 71, 58, 32, 88, 32, 61, 32
__dbase_text_4:
    db 68, 69, 66, 85, 71, 32, 111, 104, 110, 101, 32, 78, 101, 119, 76, 105, 110, 101
__dbase_text_5:
    db 32, 46, 46, 46, 32, 102, 101, 114, 116, 105, 103
__dbase_text_6:
    db 87, 105, 101, 100, 101, 114, 32, 105, 110, 32, 100, 101, 114, 32, 75, 111, 110, 115, 111, 108, 101
__dbase_stdout:
    dd 0
__dbase_stderr:
    dd 0
__dbase_written:
    dd 0
__dbase_temp_number:
    dd 0
__dbase_temp_number_hi:
    dd 0
__dbase_call_number:
    dd 0, 0
__dbase_format_buffer:
    db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
__dbase_var_x_type:
    dd 0
__dbase_var_x_num:
    dd 0, 0
__dbase_var_x_ptr:
    dd 0
__dbase_var_x_len:
    dd 0
