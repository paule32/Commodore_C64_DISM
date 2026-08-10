bits 32

import AllocConsole, "kernel32.dll", "AllocConsole"
import GetStdHandle, "kernel32.dll", "GetStdHandle"
import WriteFile, "kernel32.dll", "WriteFile"
import __dbase_gcvt, "msvcrt.dll", "_gcvt"
import ExitProcess, "kernel32.dll", "ExitProcess"
global _start
entry _start

section .text

_start:
    call AllocConsole
    push -11
    call GetStdHandle
    mov dword ptr [__dbase_stdout], eax
    push 0
    push __dbase_written
    push 7
    push __dbase_text_0
    push dword ptr [__dbase_stdout]
    call WriteFile
    fld qword ptr [__dbase_num_0]
    fld qword ptr [__dbase_num_1]
    faddp
    fld qword ptr [__dbase_num_2]
    faddp
    fstp qword ptr [__dbase_temp_number]
    push __dbase_format_buffer
    push 15
    push dword ptr [__dbase_temp_number+4]
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
    push 11
    push __dbase_text_2
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 2
    push __dbase_text_1
    push dword ptr [__dbase_stdout]
    call WriteFile
    fld qword ptr [__dbase_num_0]
    fld qword ptr [__dbase_num_1]
    fld qword ptr [__dbase_num_2]
    fmulp
    faddp
    fstp qword ptr [__dbase_temp_number]
    push __dbase_format_buffer
    push 15
    push dword ptr [__dbase_temp_number+4]
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
    fld qword ptr [__dbase_num_0]
    fld qword ptr [__dbase_num_1]
    faddp
    fld qword ptr [__dbase_num_2]
    fmulp
    fstp qword ptr [__dbase_temp_number]
    push __dbase_format_buffer
    push 15
    push dword ptr [__dbase_temp_number+4]
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
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 2
    push __dbase_text_1
    push dword ptr [__dbase_stdout]
    call WriteFile
    fld qword ptr [__dbase_num_3]
    fld qword ptr [__dbase_num_4]
    fdivp
    fstp qword ptr [__dbase_temp_number]
    push __dbase_format_buffer
    push 15
    push dword ptr [__dbase_temp_number+4]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, __dbase_format_buffer
    xor edx, edx
__dbase_strlen_loop_7:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_strlen_done_8
    inc ecx
    inc edx
    jmp __dbase_strlen_loop_7
__dbase_strlen_done_8:
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
    push __dbase_text_3
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 6
    push __dbase_text_4
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 5
    push __dbase_text_5
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 2
    push __dbase_text_1
    push dword ptr [__dbase_stdout]
    call WriteFile
    fld qword ptr [__dbase_num_1]
    fld qword ptr [__dbase_num_2]
    faddp
    fstp qword ptr [__dbase_temp_number]
    push __dbase_format_buffer
    push 15
    push dword ptr [__dbase_temp_number+4]
    push dword ptr [__dbase_temp_number]
    call __dbase_gcvt
    add esp, 16
    mov ecx, __dbase_format_buffer
    xor edx, edx
__dbase_strlen_loop_9:
    movzx eax, byte ptr [ecx]
    test eax, eax
    je __dbase_strlen_done_10
    inc ecx
    inc edx
    jmp __dbase_strlen_loop_9
__dbase_strlen_done_10:
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
    push 5
    push __dbase_text_6
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 8
    push __dbase_text_7
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 8
    push __dbase_text_8
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
    dd 0, 1072693248
__dbase_num_1:
    dd 0, 1073741824
__dbase_num_2:
    dd 0, 1074266112
__dbase_num_3:
    dd 0, 1076101120
__dbase_num_4:
    dd 0, 1074790400
__dbase_text_0:
    db 83, 117, 109, 109, 101, 58, 32
__dbase_text_1:
    db 13, 10
__dbase_text_2:
    db 80, 114, 105, 111, 114, 105, 116, 97, 101, 116, 58
__dbase_text_3:
    db 83, 116, 114, 105, 110, 103, 45, 75, 111, 110, 107, 97, 116, 101, 110, 97, 116, 105, 111, 110, 58, 32
__dbase_text_4:
    db 72, 97, 108, 108, 111, 32
__dbase_text_5:
    db 100, 66, 97, 115, 101
__dbase_text_6:
    db 111, 104, 110, 101, 32
__dbase_text_7:
    db 78, 101, 119, 76, 105, 110, 101, 32
__dbase_text_8:
    db 98, 105, 115, 32, 104, 105, 101, 114
__dbase_stdout:
    dd 0
__dbase_written:
    dd 0
__dbase_temp_number:
    dd 0, 0
__dbase_call_number:
    dd 0, 0
__dbase_format_buffer:
    db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
