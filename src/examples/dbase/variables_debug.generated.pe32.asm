bits 32

import AllocConsole, "kernel32.dll", "AllocConsole"
import GetStdHandle, "kernel32.dll", "GetStdHandle"
import WriteFile, "kernel32.dll", "WriteFile"
import __dbase_gcvt, "msvcrt.dll", "_gcvt"
import CreateNamedPipeA, "kernel32.dll", "CreateNamedPipeA"
import ConnectNamedPipe, "kernel32.dll", "ConnectNamedPipe"
import CreateProcessA, "kernel32.dll", "CreateProcessA"
import CloseHandle, "kernel32.dll", "CloseHandle"
import ExitProcess, "kernel32.dll", "ExitProcess"
global _start
entry _start

section .text

__dbase_open_debug_console:
    cmp dword ptr [__dbase_debug_ready], 0
    jne __dbase_open_debug_done
    push 0
    push 0
    push 4096
    push 4096
    push 255
    push 0
    push 2
    push __dbase_debug_pipe_name
    call CreateNamedPipeA
    cmp eax, -1
    je __dbase_open_debug_done
    mov dword ptr [__dbase_debug_pipe], eax
    mov dword ptr [__dbase_startupinfo], 68
    push __dbase_processinfo
    push __dbase_startupinfo
    push 0
    push 0
    push 16
    push 0
    push 0
    push 0
    push __dbase_debug_command
    push 0
    call CreateProcessA
    test eax, eax
    je __dbase_open_debug_failed
    push 0
    push dword ptr [__dbase_debug_pipe]
    call ConnectNamedPipe
    mov dword ptr [__dbase_debug_ready], 1
    jmp __dbase_open_debug_done
__dbase_open_debug_failed:
    push dword ptr [__dbase_debug_pipe]
    call CloseHandle
    mov dword ptr [__dbase_debug_pipe], 0
__dbase_open_debug_done:
    ret

__dbase_get_debug_handle:
    cmp dword ptr [__dbase_debug_ready], 0
    je __dbase_get_debug_fallback
    mov eax, dword ptr [__dbase_debug_pipe]
    ret
__dbase_get_debug_fallback:
    mov eax, dword ptr [__dbase_stdout]
    ret

_start:
    call AllocConsole
    push -11
    call GetStdHandle
    mov dword ptr [__dbase_stdout], eax
    fld qword ptr [__dbase_num_0]
    fstp qword ptr [__dbase_var_x_num]
    mov dword ptr [__dbase_var_x_type], 1
    fld qword ptr [__dbase_num_1]
    fld qword ptr [__dbase_num_2]
    fld qword ptr [__dbase_num_3]
    fmulp
    faddp
    fstp qword ptr [__dbase_var_y_num]
    mov dword ptr [__dbase_var_y_type], 1
    fld qword ptr [__dbase_num_4]
    fld qword ptr [__dbase_num_4]
    faddp
    fld qword ptr [__dbase_num_4]
    faddp
    fstp qword ptr [__dbase_var_hexvalue_num]
    mov dword ptr [__dbase_var_hexvalue_type], 1
    mov eax, __dbase_text_0
    mov dword ptr [__dbase_var_letter_ptr], eax
    mov dword ptr [__dbase_var_letter_len], 1
    mov dword ptr [__dbase_var_letter_type], 3
    mov eax, __dbase_text_1
    mov dword ptr [__dbase_var_text_ptr], eax
    mov dword ptr [__dbase_var_text_len], 12
    mov dword ptr [__dbase_var_text_type], 2
    push 0
    push __dbase_written
    push 13
    push __dbase_text_2
    push dword ptr [__dbase_stdout]
    call WriteFile
    fld qword ptr [__dbase_var_x_num]
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
    push __dbase_text_3
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 4
    push __dbase_text_4
    push dword ptr [__dbase_stdout]
    call WriteFile
    fld qword ptr [__dbase_var_y_num]
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
    push __dbase_text_3
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 11
    push __dbase_text_5
    push dword ptr [__dbase_stdout]
    call WriteFile
    fld qword ptr [__dbase_var_hexvalue_num]
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
    push __dbase_text_3
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 7
    push __dbase_text_6
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push dword ptr [__dbase_var_text_len]
    push dword ptr [__dbase_var_text_ptr]
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 12
    push __dbase_text_7
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push dword ptr [__dbase_var_letter_len]
    push dword ptr [__dbase_var_letter_ptr]
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 2
    push __dbase_text_3
    push dword ptr [__dbase_stdout]
    call WriteFile
    call __dbase_open_debug_console
    push 0
    push __dbase_written
    push 11
    push __dbase_text_8
    call __dbase_get_debug_handle
    push eax
    call WriteFile
    fld qword ptr [__dbase_var_x_num]
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
    call __dbase_get_debug_handle
    push eax
    call WriteFile
    push 0
    push __dbase_written
    push 2
    push __dbase_text_3
    call __dbase_get_debug_handle
    push eax
    call WriteFile
    push 0
    push __dbase_written
    push 11
    push __dbase_text_9
    call __dbase_get_debug_handle
    push eax
    call WriteFile
    fld qword ptr [__dbase_var_y_num]
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
    call __dbase_get_debug_handle
    push eax
    call WriteFile
    push 0
    push __dbase_written
    push 2
    push __dbase_text_3
    call __dbase_get_debug_handle
    push eax
    call WriteFile
    push 0
    push __dbase_written
    push 21
    push __dbase_text_10
    push dword ptr [__dbase_stdout]
    call WriteFile
    push 0
    push __dbase_written
    push 2
    push __dbase_text_3
    push dword ptr [__dbase_stdout]
    call WriteFile
    cmp dword ptr [__dbase_debug_ready], 0
    je __dbase_exit
    push dword ptr [__dbase_debug_pipe]
    call CloseHandle
__dbase_exit:
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
    dd 0, 1074790400
__dbase_num_4:
    dd 0, 1076887552
__dbase_text_0:
    db 65
__dbase_text_1:
    db 116, 101, 120, 116, 32, 49, 116, 101, 120, 116, 32, 50
__dbase_text_2:
    db 87, 101, 114, 116, 32, 118, 111, 110, 32, 88, 32, 61, 32
__dbase_text_3:
    db 13, 10
__dbase_text_4:
    db 89, 32, 61, 32
__dbase_text_5:
    db 72, 101, 120, 86, 97, 108, 117, 101, 32, 61, 32
__dbase_text_6:
    db 84, 101, 120, 116, 32, 61, 32
__dbase_text_7:
    db 32, 47, 32, 76, 101, 116, 116, 101, 114, 32, 61, 32
__dbase_text_8:
    db 68, 101, 98, 117, 103, 58, 32, 88, 32, 61, 32
__dbase_text_9:
    db 68, 101, 98, 117, 103, 58, 32, 89, 32, 61, 32
__dbase_text_10:
    db 68, 101, 98, 117, 103, 45, 65, 117, 115, 103, 97, 98, 101, 32, 98, 101, 101, 110, 100, 101, 116
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
__dbase_debug_pipe_name:
    db 92, 92, 46, 92, 112, 105, 112, 101, 92, 100, 66, 97, 115, 101, 68, 101, 98, 117, 103, 79, 117, 116, 112, 117
    db 116, 0
__dbase_debug_command:
    db 99, 109, 100, 46, 101, 120, 101, 32, 47, 81, 32, 47, 75, 32, 34, 116, 105, 116, 108, 101, 32, 100, 66, 97
    db 115, 101, 32, 68, 101, 98, 117, 103, 32, 79, 117, 116, 112, 117, 116, 32, 38, 32, 109, 111, 114, 101, 46, 99
    db 111, 109, 32, 60, 32, 92, 92, 46, 92, 112, 105, 112, 101, 92, 100, 66, 97, 115, 101, 68, 101, 98, 117, 103
    db 79, 117, 116, 112, 117, 116, 34, 0
__dbase_debug_pipe:
    dd 0
__dbase_debug_ready:
    dd 0
__dbase_startupinfo:
    db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
__dbase_processinfo:
    db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
__dbase_var_x_type:
    dd 0
__dbase_var_x_num:
    dd 0, 0
__dbase_var_x_ptr:
    dd 0
__dbase_var_x_len:
    dd 0
__dbase_var_y_type:
    dd 0
__dbase_var_y_num:
    dd 0, 0
__dbase_var_y_ptr:
    dd 0
__dbase_var_y_len:
    dd 0
__dbase_var_hexvalue_type:
    dd 0
__dbase_var_hexvalue_num:
    dd 0, 0
__dbase_var_hexvalue_ptr:
    dd 0
__dbase_var_hexvalue_len:
    dd 0
__dbase_var_letter_type:
    dd 0
__dbase_var_letter_num:
    dd 0, 0
__dbase_var_letter_ptr:
    dd 0
__dbase_var_letter_len:
    dd 0
__dbase_var_text_type:
    dd 0
__dbase_var_text_num:
    dd 0, 0
__dbase_var_text_ptr:
    dd 0
__dbase_var_text_len:
    dd 0
