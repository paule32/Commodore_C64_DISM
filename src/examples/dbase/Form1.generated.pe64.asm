%include "Form1.generated.pe64.extern.inc"
bits 64

global _start
entry _start

section .text

_start:
    mov rcx, __dbase_text_0
    mov edx, 0
    mov r8d, 0
    xor r9d, r9d
    mov rax, __dbase_format_buffer
    sub rsp, 40
    mov qword ptr [rsp+32], rax
    call DBaseQtRuntimeStartup
    add rsp, 40
    test eax, eax
    jne __dbase_qt_init_ok_2
    mov ecx, 1
    sub rsp, 40
    call ExitProcess
__dbase_qt_init_ok_2:
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
    jne __dbase_output_override_ready_3
    cmp dword ptr [__dbase_output_format_screen], 0
    je __dbase_output_console_4
    jmp __dbase_output_show_done_5
__dbase_output_override_ready_3:
    cmp dword ptr [__dbase_output_debug_override], 0
    je __dbase_output_console_4
__dbase_output_show_done_5:
    cmp dword ptr [__dbase_output_debug_visible], 0
    jne __dbase_output_already_visible_7
    mov dword ptr [__dbase_output_debug_visible], 1
    mov ecx, 1
    sub rsp, 40
    call DBaseQtSetDebugVisible
    add rsp, 40
__dbase_output_already_visible_7:
    jmp __dbase_output_done_6
__dbase_output_console_4:
    mov rcx, __dbase_text_1
    mov edx, 0
    sub rsp, 40
    call DBaseConsoleWrite
    add rsp, 40
__dbase_output_done_6:
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
    call DBaseConsoleShutdown
    add rsp, 40
    mov rcx, __dbase_format_buffer
    sub rsp, 40
    call DBaseQtRuntimeShutdown
    add rsp, 40
    mov ecx, dword ptr [__dbase_exit_code]
    sub rsp, 40
    call ExitProcess

section .data

__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_output_debug_override:
    dd -1
__dbase_workstation_lazy_console_marker:
    db 68, 54, 52, 68, 66, 65, 83, 69, 95, 76, 65, 90, 89, 95, 67, 79, 78, 83, 79, 76, 69, 95, 86, 49, 0

section .bss

__dbase_ffi_return:
    resq 1
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
__dbase_console_number_len:
    resd 1
__dbase_text_1:
    resb 1

; Stage 462: WFM DLL-Runtime-Startup/Shutdown fuer PE32+
.section .text
.entry __d64_wfm_entry
__d64_wfm_entry:
    mov rax, __dbase_wfm_qt_output_marker
    mov rcx, __dbase_wfm_text_0
    mov edx, 0
    mov r8d, 0
    mov r9d, 1
    mov rax, __dbase_format_buffer
    sub rsp, 40
    mov qword ptr [rsp+32], rax
    call DBaseQtRuntimeStartup
    add rsp, 40
    test eax, eax
    jne __dbase_wfm_runtime_ready
    mov ecx, 1
    sub rsp, 40
    call ExitProcess
__dbase_wfm_runtime_ready:
    sub rsp, 40
    call __dbase_wfm_proc___dbase_top_level__
    add rsp, 40
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
    mov edx, 23
    mov r8d, 28
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
    call DBaseQtWfmModalParameter
    add rsp, 40
    mov edx, eax
    mov rcx, qword ptr [__dbase_wfm_form]
    sub rsp, 40
    call DBaseQtFormRun
    add rsp, 40
    sub rsp, 40
    call __dbase_wfm_proc___del__
    add rsp, 40
    mov rcx, __dbase_format_buffer
    sub rsp, 40
    call DBaseQtRuntimeShutdown
    add rsp, 40
    xor ecx, ecx
    sub rsp, 40
    call ExitProcess

; Stage 133: WFM Event-/Methoden-Code
.section .text

; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: __dbase_top_level__
; ------------------------------------------------------------
__dbase_wfm_proc___dbase_top_level__:
    sub rsp, 40
    mov dword ptr [__dbase_wfm_local___dbase_top_level___a_type], 0
    mov dword ptr [__dbase_wfm_local___dbase_top_level___a_len], 0
    fldz
    fstp qword ptr [__dbase_wfm_local___dbase_top_level___a_num]
    xor eax, eax
    mov qword ptr [__dbase_wfm_local___dbase_top_level___a_ptr], rax
    mov dword ptr [__dbase_wfm_local___dbase_top_level___c_type], 0
    mov dword ptr [__dbase_wfm_local___dbase_top_level___c_len], 0
    fldz
    fstp qword ptr [__dbase_wfm_local___dbase_top_level___c_num]
    xor eax, eax
    mov qword ptr [__dbase_wfm_local___dbase_top_level___c_ptr], rax
    ; Quellcode Zeile: 37
    ; ? "shell32.dll"
    mov rcx, __dbase_wfm_output_text_75
    mov edx, 11
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 39
    fld qword ptr [__dbase_wfm_numconst_0]
    fstp qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_num]
    mov rax, __dbase_wfm_flow_ffi_ansi_4
    mov qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_ptr], rax
    mov rax, __dbase_wfm_flow_ffi_ansi_6
    mov qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_ptr], rax
    mov qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_ptr], 0
    mov qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_ptr], 0
    fld qword ptr [__dbase_wfm_numconst_1]
    fstp qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_num]
    sub rsp, 48
    cmp dword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_type], 4
    jne __dbase_wfm_flow_ffi_numeric_10
    mov rcx, qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_ptr]
    jmp __dbase_wfm_flow_ffi_loaded_11
__dbase_wfm_flow_ffi_numeric_10:
    fld qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_num]
    fistp qword ptr [__dbase_ffi_return]
    mov rcx, qword ptr [__dbase_ffi_return]
__dbase_wfm_flow_ffi_loaded_11:
    mov rdx, qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_ptr]
    mov r8, qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_ptr]
    mov r9, qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_ptr]
    mov rax, qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_ptr]
    mov qword ptr [rsp+32], rax
    cmp dword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_type], 4
    jne __dbase_wfm_flow_ffi_numeric_12
    mov rax, qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_ptr]
    jmp __dbase_wfm_flow_ffi_loaded_13
__dbase_wfm_flow_ffi_numeric_12:
    fld qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_num]
    fistp qword ptr [__dbase_ffi_return]
    mov rax, qword ptr [__dbase_ffi_return]
__dbase_wfm_flow_ffi_loaded_13:
    mov qword ptr [rsp+40], rax
    call __dbase_ffi_shellexecute
    add rsp, 48
    mov qword ptr [__dbase_ffi_return], rax
    fild qword ptr [__dbase_ffi_return]
    fstp qword ptr [__dbase_wfm_mem_result_num]
    mov dword ptr [__dbase_wfm_mem_result_type], 1
    mov dword ptr [__dbase_wfm_mem_result_len], 0
    mov qword ptr [__dbase_wfm_mem_result_ptr], 0
    ; Quellcode Zeile: 41
    ; ? result
    mov rcx, __dbase_wfm_mem_result_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 43
    ; local A = 9
    fld qword ptr [__dbase_wfm_numconst_2]
    fstp qword ptr [__dbase_wfm_local___dbase_top_level___a_num]
    mov dword ptr [__dbase_wfm_local___dbase_top_level___a_type], 1
    mov dword ptr [__dbase_wfm_local___dbase_top_level___a_len], 0
    mov qword ptr [__dbase_wfm_local___dbase_top_level___a_ptr], 0
    ; Quellcode Zeile: 44
    ; local C = 4
    fld qword ptr [__dbase_wfm_numconst_3]
    fstp qword ptr [__dbase_wfm_local___dbase_top_level___c_num]
    mov dword ptr [__dbase_wfm_local___dbase_top_level___c_type], 1
    mov dword ptr [__dbase_wfm_local___dbase_top_level___c_len], 0
    mov qword ptr [__dbase_wfm_local___dbase_top_level___c_ptr], 0
    ; Quellcode Zeile: 47
    ; STORE 123.45 TO xyz
    fld qword ptr [__dbase_wfm_numconst_4]
    fstp qword ptr [__dbase_wfm_mem_xyz_num]
    mov dword ptr [__dbase_wfm_mem_xyz_type], 2
    mov dword ptr [__dbase_wfm_mem_xyz_len], 0
    mov qword ptr [__dbase_wfm_mem_xyz_ptr], 0
    ; Quellcode Zeile: 49
    mov edx, dword ptr [__dbase_wfm_mem_xyz_type]
    cmp edx, 1
    je __dbase_wfm_flow_type_numeric_15
    cmp edx, 2
    je __dbase_wfm_flow_type_numeric_15
    cmp edx, 3
    je __dbase_wfm_flow_type_string_16
    cmp edx, 4
    je __dbase_wfm_flow_type_object_17
    cmp edx, 5
    je __dbase_wfm_flow_type_logical_18
    cmp edx, 6
    je __dbase_wfm_flow_type_date_19
    mov eax, 85
    jmp __dbase_wfm_flow_type_ready_20
__dbase_wfm_flow_type_numeric_15:
    mov eax, 78
    jmp __dbase_wfm_flow_type_ready_20
__dbase_wfm_flow_type_string_16:
    mov eax, 67
    jmp __dbase_wfm_flow_type_ready_20
__dbase_wfm_flow_type_object_17:
    mov eax, 79
    jmp __dbase_wfm_flow_type_ready_20
__dbase_wfm_flow_type_logical_18:
    mov eax, 76
    jmp __dbase_wfm_flow_type_ready_20
__dbase_wfm_flow_type_date_19:
    mov eax, 68
__dbase_wfm_flow_type_ready_20:
    cmp eax, 78
    jne __dbase_wfm_flow_type_slot_next_22
    mov rax, __dbase_wfm_output_text_76
    jmp __dbase_wfm_flow_type_slot_done_21
__dbase_wfm_flow_type_slot_next_22:
    cmp eax, 67
    jne __dbase_wfm_flow_type_slot_next_23
    mov rax, __dbase_wfm_output_text_77
    jmp __dbase_wfm_flow_type_slot_done_21
__dbase_wfm_flow_type_slot_next_23:
    cmp eax, 79
    jne __dbase_wfm_flow_type_slot_next_24
    mov rax, __dbase_wfm_output_text_78
    jmp __dbase_wfm_flow_type_slot_done_21
__dbase_wfm_flow_type_slot_next_24:
    cmp eax, 76
    jne __dbase_wfm_flow_type_slot_next_25
    mov rax, __dbase_wfm_output_text_79
    jmp __dbase_wfm_flow_type_slot_done_21
__dbase_wfm_flow_type_slot_next_25:
    cmp eax, 68
    jne __dbase_wfm_flow_type_slot_next_26
    mov rax, __dbase_wfm_output_text_80
    jmp __dbase_wfm_flow_type_slot_done_21
__dbase_wfm_flow_type_slot_next_26:
    mov rax, __dbase_wfm_output_text_81
__dbase_wfm_flow_type_slot_done_21:
    mov qword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_14_ptr], rax
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_14_len], 1
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_14_type], 3
    ; ? TYPE("xyz")
    mov rcx, __dbase_wfm_mem___dbase_wfm_flow_type_print_14_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 50
    mov edx, dword ptr [__dbase_wfm_mem_xyz_type]
    cmp edx, 1
    je __dbase_wfm_flow_type_numeric_28
    cmp edx, 2
    je __dbase_wfm_flow_type_numeric_28
    cmp edx, 3
    je __dbase_wfm_flow_type_string_29
    cmp edx, 4
    je __dbase_wfm_flow_type_object_30
    cmp edx, 5
    je __dbase_wfm_flow_type_logical_31
    cmp edx, 6
    je __dbase_wfm_flow_type_date_32
    mov eax, 85
    jmp __dbase_wfm_flow_type_ready_33
__dbase_wfm_flow_type_numeric_28:
    mov eax, 78
    jmp __dbase_wfm_flow_type_ready_33
__dbase_wfm_flow_type_string_29:
    mov eax, 67
    jmp __dbase_wfm_flow_type_ready_33
__dbase_wfm_flow_type_object_30:
    mov eax, 79
    jmp __dbase_wfm_flow_type_ready_33
__dbase_wfm_flow_type_logical_31:
    mov eax, 76
    jmp __dbase_wfm_flow_type_ready_33
__dbase_wfm_flow_type_date_32:
    mov eax, 68
__dbase_wfm_flow_type_ready_33:
    cmp eax, 78
    jne __dbase_wfm_flow_type_slot_next_35
    mov rax, __dbase_wfm_output_text_82
    jmp __dbase_wfm_flow_type_slot_done_34
__dbase_wfm_flow_type_slot_next_35:
    cmp eax, 67
    jne __dbase_wfm_flow_type_slot_next_36
    mov rax, __dbase_wfm_output_text_83
    jmp __dbase_wfm_flow_type_slot_done_34
__dbase_wfm_flow_type_slot_next_36:
    cmp eax, 79
    jne __dbase_wfm_flow_type_slot_next_37
    mov rax, __dbase_wfm_output_text_84
    jmp __dbase_wfm_flow_type_slot_done_34
__dbase_wfm_flow_type_slot_next_37:
    cmp eax, 76
    jne __dbase_wfm_flow_type_slot_next_38
    mov rax, __dbase_wfm_output_text_85
    jmp __dbase_wfm_flow_type_slot_done_34
__dbase_wfm_flow_type_slot_next_38:
    cmp eax, 68
    jne __dbase_wfm_flow_type_slot_next_39
    mov rax, __dbase_wfm_output_text_86
    jmp __dbase_wfm_flow_type_slot_done_34
__dbase_wfm_flow_type_slot_next_39:
    mov rax, __dbase_wfm_output_text_87
__dbase_wfm_flow_type_slot_done_34:
    mov qword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_27_ptr], rax
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_27_len], 1
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_27_type], 3
    ; ? VARTYPE(xyz)
    mov rcx, __dbase_wfm_mem___dbase_wfm_flow_type_print_27_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 52
    ; IF TYPE("xyz") == "N"
    mov edx, dword ptr [__dbase_wfm_mem_xyz_type]
    cmp edx, 1
    je __dbase_wfm_flow_type_numeric_42
    cmp edx, 2
    je __dbase_wfm_flow_type_numeric_42
    cmp edx, 3
    je __dbase_wfm_flow_type_string_43
    cmp edx, 4
    je __dbase_wfm_flow_type_object_44
    cmp edx, 5
    je __dbase_wfm_flow_type_logical_45
    cmp edx, 6
    je __dbase_wfm_flow_type_date_46
    mov eax, 85
    jmp __dbase_wfm_flow_type_ready_47
__dbase_wfm_flow_type_numeric_42:
    mov eax, 78
    jmp __dbase_wfm_flow_type_ready_47
__dbase_wfm_flow_type_string_43:
    mov eax, 67
    jmp __dbase_wfm_flow_type_ready_47
__dbase_wfm_flow_type_object_44:
    mov eax, 79
    jmp __dbase_wfm_flow_type_ready_47
__dbase_wfm_flow_type_logical_45:
    mov eax, 76
    jmp __dbase_wfm_flow_type_ready_47
__dbase_wfm_flow_type_date_46:
    mov eax, 68
__dbase_wfm_flow_type_ready_47:
    push rax
    mov eax, 78
    pop rcx
    cmp ecx, eax
    jne __dbase_wfm_flow_if_false_40
    ; Quellcode Zeile: 53
    ; ? "xyz ist numerisch"
    mov rcx, __dbase_wfm_output_text_88
    mov edx, 17
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 54
__dbase_wfm_flow_if_false_40:
__dbase_wfm_flow_if_end_41:
    ; Quellcode Zeile: 56
    ; STORE "Hallo" TO xyz
    mov rax, __dbase_wfm_output_text_89
    mov qword ptr [__dbase_wfm_mem_xyz_ptr], rax
    mov dword ptr [__dbase_wfm_mem_xyz_len], 5
    mov dword ptr [__dbase_wfm_mem_xyz_type], 3
    ; Quellcode Zeile: 58
    mov edx, dword ptr [__dbase_wfm_mem_xyz_type]
    cmp edx, 1
    je __dbase_wfm_flow_type_numeric_49
    cmp edx, 2
    je __dbase_wfm_flow_type_numeric_49
    cmp edx, 3
    je __dbase_wfm_flow_type_string_50
    cmp edx, 4
    je __dbase_wfm_flow_type_object_51
    cmp edx, 5
    je __dbase_wfm_flow_type_logical_52
    cmp edx, 6
    je __dbase_wfm_flow_type_date_53
    mov eax, 85
    jmp __dbase_wfm_flow_type_ready_54
__dbase_wfm_flow_type_numeric_49:
    mov eax, 78
    jmp __dbase_wfm_flow_type_ready_54
__dbase_wfm_flow_type_string_50:
    mov eax, 67
    jmp __dbase_wfm_flow_type_ready_54
__dbase_wfm_flow_type_object_51:
    mov eax, 79
    jmp __dbase_wfm_flow_type_ready_54
__dbase_wfm_flow_type_logical_52:
    mov eax, 76
    jmp __dbase_wfm_flow_type_ready_54
__dbase_wfm_flow_type_date_53:
    mov eax, 68
__dbase_wfm_flow_type_ready_54:
    cmp eax, 78
    jne __dbase_wfm_flow_type_slot_next_56
    mov rax, __dbase_wfm_output_text_90
    jmp __dbase_wfm_flow_type_slot_done_55
__dbase_wfm_flow_type_slot_next_56:
    cmp eax, 67
    jne __dbase_wfm_flow_type_slot_next_57
    mov rax, __dbase_wfm_output_text_91
    jmp __dbase_wfm_flow_type_slot_done_55
__dbase_wfm_flow_type_slot_next_57:
    cmp eax, 79
    jne __dbase_wfm_flow_type_slot_next_58
    mov rax, __dbase_wfm_output_text_92
    jmp __dbase_wfm_flow_type_slot_done_55
__dbase_wfm_flow_type_slot_next_58:
    cmp eax, 76
    jne __dbase_wfm_flow_type_slot_next_59
    mov rax, __dbase_wfm_output_text_93
    jmp __dbase_wfm_flow_type_slot_done_55
__dbase_wfm_flow_type_slot_next_59:
    cmp eax, 68
    jne __dbase_wfm_flow_type_slot_next_60
    mov rax, __dbase_wfm_output_text_94
    jmp __dbase_wfm_flow_type_slot_done_55
__dbase_wfm_flow_type_slot_next_60:
    mov rax, __dbase_wfm_output_text_95
__dbase_wfm_flow_type_slot_done_55:
    mov qword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_48_ptr], rax
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_48_len], 1
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_48_type], 3
    ; ? TYPE("xyz")
    mov rcx, __dbase_wfm_mem___dbase_wfm_flow_type_print_48_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 59
    mov edx, dword ptr [__dbase_wfm_mem_xyz_type]
    cmp edx, 1
    je __dbase_wfm_flow_type_numeric_62
    cmp edx, 2
    je __dbase_wfm_flow_type_numeric_62
    cmp edx, 3
    je __dbase_wfm_flow_type_string_63
    cmp edx, 4
    je __dbase_wfm_flow_type_object_64
    cmp edx, 5
    je __dbase_wfm_flow_type_logical_65
    cmp edx, 6
    je __dbase_wfm_flow_type_date_66
    mov eax, 85
    jmp __dbase_wfm_flow_type_ready_67
__dbase_wfm_flow_type_numeric_62:
    mov eax, 78
    jmp __dbase_wfm_flow_type_ready_67
__dbase_wfm_flow_type_string_63:
    mov eax, 67
    jmp __dbase_wfm_flow_type_ready_67
__dbase_wfm_flow_type_object_64:
    mov eax, 79
    jmp __dbase_wfm_flow_type_ready_67
__dbase_wfm_flow_type_logical_65:
    mov eax, 76
    jmp __dbase_wfm_flow_type_ready_67
__dbase_wfm_flow_type_date_66:
    mov eax, 68
__dbase_wfm_flow_type_ready_67:
    cmp eax, 78
    jne __dbase_wfm_flow_type_slot_next_69
    mov rax, __dbase_wfm_output_text_96
    jmp __dbase_wfm_flow_type_slot_done_68
__dbase_wfm_flow_type_slot_next_69:
    cmp eax, 67
    jne __dbase_wfm_flow_type_slot_next_70
    mov rax, __dbase_wfm_output_text_97
    jmp __dbase_wfm_flow_type_slot_done_68
__dbase_wfm_flow_type_slot_next_70:
    cmp eax, 79
    jne __dbase_wfm_flow_type_slot_next_71
    mov rax, __dbase_wfm_output_text_98
    jmp __dbase_wfm_flow_type_slot_done_68
__dbase_wfm_flow_type_slot_next_71:
    cmp eax, 76
    jne __dbase_wfm_flow_type_slot_next_72
    mov rax, __dbase_wfm_output_text_99
    jmp __dbase_wfm_flow_type_slot_done_68
__dbase_wfm_flow_type_slot_next_72:
    cmp eax, 68
    jne __dbase_wfm_flow_type_slot_next_73
    mov rax, __dbase_wfm_output_text_100
    jmp __dbase_wfm_flow_type_slot_done_68
__dbase_wfm_flow_type_slot_next_73:
    mov rax, __dbase_wfm_output_text_101
__dbase_wfm_flow_type_slot_done_68:
    mov qword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_61_ptr], rax
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_61_len], 1
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_61_type], 3
    ; ? VARTYPE(xyz)
    mov rcx, __dbase_wfm_mem___dbase_wfm_flow_type_print_61_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 61
    mov eax, 85
    cmp eax, 78
    jne __dbase_wfm_flow_type_slot_next_76
    mov rax, __dbase_wfm_output_text_102
    jmp __dbase_wfm_flow_type_slot_done_75
__dbase_wfm_flow_type_slot_next_76:
    cmp eax, 67
    jne __dbase_wfm_flow_type_slot_next_77
    mov rax, __dbase_wfm_output_text_103
    jmp __dbase_wfm_flow_type_slot_done_75
__dbase_wfm_flow_type_slot_next_77:
    cmp eax, 79
    jne __dbase_wfm_flow_type_slot_next_78
    mov rax, __dbase_wfm_output_text_104
    jmp __dbase_wfm_flow_type_slot_done_75
__dbase_wfm_flow_type_slot_next_78:
    cmp eax, 76
    jne __dbase_wfm_flow_type_slot_next_79
    mov rax, __dbase_wfm_output_text_105
    jmp __dbase_wfm_flow_type_slot_done_75
__dbase_wfm_flow_type_slot_next_79:
    cmp eax, 68
    jne __dbase_wfm_flow_type_slot_next_80
    mov rax, __dbase_wfm_output_text_106
    jmp __dbase_wfm_flow_type_slot_done_75
__dbase_wfm_flow_type_slot_next_80:
    mov rax, __dbase_wfm_output_text_107
__dbase_wfm_flow_type_slot_done_75:
    mov qword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_74_ptr], rax
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_74_len], 1
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_74_type], 3
    ; ? TYPE("unbekannt")
    mov rcx, __dbase_wfm_mem___dbase_wfm_flow_type_print_74_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
__dbase_wfm_flow_method_exit_1:
    add rsp, 40
    ret
; END WFM PROCEDURE/FUNCTION: __dbase_top_level__


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: __del__
; ------------------------------------------------------------
__dbase_wfm_proc___del__:
    sub rsp, 40
    ; Quellcode Zeile: 255
__dbase_wfm_flow_method_exit_81:
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
    ; Quellcode Zeile: 246
    ; ? "p1 = " + int(p1)
    mov rcx, __dbase_wfm_output_text_108
    mov edx, 5
    mov r8d, 0
    call DBaseQtConsoleWrite
    mov rcx, __dbase_wfm_output_text_109
    mov edx, 2
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 247
    ; ? "p2 = " + int(p2)
    mov rcx, __dbase_wfm_output_text_110
    mov edx, 5
    mov r8d, 0
    call DBaseQtConsoleWrite
    mov rcx, __dbase_wfm_output_text_111
    mov edx, 1
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 249
    mov edx, dword ptr [__dbase_wfm_mem_xyz_type]
    cmp edx, 1
    je __dbase_wfm_flow_type_numeric_84
    cmp edx, 2
    je __dbase_wfm_flow_type_numeric_84
    cmp edx, 3
    je __dbase_wfm_flow_type_string_85
    cmp edx, 4
    je __dbase_wfm_flow_type_object_86
    cmp edx, 5
    je __dbase_wfm_flow_type_logical_87
    cmp edx, 6
    je __dbase_wfm_flow_type_date_88
    mov eax, 85
    jmp __dbase_wfm_flow_type_ready_89
__dbase_wfm_flow_type_numeric_84:
    mov eax, 78
    jmp __dbase_wfm_flow_type_ready_89
__dbase_wfm_flow_type_string_85:
    mov eax, 67
    jmp __dbase_wfm_flow_type_ready_89
__dbase_wfm_flow_type_object_86:
    mov eax, 79
    jmp __dbase_wfm_flow_type_ready_89
__dbase_wfm_flow_type_logical_87:
    mov eax, 76
    jmp __dbase_wfm_flow_type_ready_89
__dbase_wfm_flow_type_date_88:
    mov eax, 68
__dbase_wfm_flow_type_ready_89:
    cmp eax, 78
    jne __dbase_wfm_flow_type_slot_next_91
    mov rax, __dbase_wfm_output_text_112
    jmp __dbase_wfm_flow_type_slot_done_90
__dbase_wfm_flow_type_slot_next_91:
    cmp eax, 67
    jne __dbase_wfm_flow_type_slot_next_92
    mov rax, __dbase_wfm_output_text_113
    jmp __dbase_wfm_flow_type_slot_done_90
__dbase_wfm_flow_type_slot_next_92:
    cmp eax, 79
    jne __dbase_wfm_flow_type_slot_next_93
    mov rax, __dbase_wfm_output_text_114
    jmp __dbase_wfm_flow_type_slot_done_90
__dbase_wfm_flow_type_slot_next_93:
    cmp eax, 76
    jne __dbase_wfm_flow_type_slot_next_94
    mov rax, __dbase_wfm_output_text_115
    jmp __dbase_wfm_flow_type_slot_done_90
__dbase_wfm_flow_type_slot_next_94:
    cmp eax, 68
    jne __dbase_wfm_flow_type_slot_next_95
    mov rax, __dbase_wfm_output_text_116
    jmp __dbase_wfm_flow_type_slot_done_90
__dbase_wfm_flow_type_slot_next_95:
    mov rax, __dbase_wfm_output_text_117
__dbase_wfm_flow_type_slot_done_90:
    mov qword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_83_ptr], rax
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_83_len], 1
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_83_type], 3
    ; ? TYPE("xyz")
    mov rcx, __dbase_wfm_mem___dbase_wfm_flow_type_print_83_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 250
    mov edx, dword ptr [__dbase_wfm_mem_xyz_type]
    cmp edx, 1
    je __dbase_wfm_flow_type_numeric_97
    cmp edx, 2
    je __dbase_wfm_flow_type_numeric_97
    cmp edx, 3
    je __dbase_wfm_flow_type_string_98
    cmp edx, 4
    je __dbase_wfm_flow_type_object_99
    cmp edx, 5
    je __dbase_wfm_flow_type_logical_100
    cmp edx, 6
    je __dbase_wfm_flow_type_date_101
    mov eax, 85
    jmp __dbase_wfm_flow_type_ready_102
__dbase_wfm_flow_type_numeric_97:
    mov eax, 78
    jmp __dbase_wfm_flow_type_ready_102
__dbase_wfm_flow_type_string_98:
    mov eax, 67
    jmp __dbase_wfm_flow_type_ready_102
__dbase_wfm_flow_type_object_99:
    mov eax, 79
    jmp __dbase_wfm_flow_type_ready_102
__dbase_wfm_flow_type_logical_100:
    mov eax, 76
    jmp __dbase_wfm_flow_type_ready_102
__dbase_wfm_flow_type_date_101:
    mov eax, 68
__dbase_wfm_flow_type_ready_102:
    cmp eax, 78
    jne __dbase_wfm_flow_type_slot_next_104
    mov rax, __dbase_wfm_output_text_118
    jmp __dbase_wfm_flow_type_slot_done_103
__dbase_wfm_flow_type_slot_next_104:
    cmp eax, 67
    jne __dbase_wfm_flow_type_slot_next_105
    mov rax, __dbase_wfm_output_text_119
    jmp __dbase_wfm_flow_type_slot_done_103
__dbase_wfm_flow_type_slot_next_105:
    cmp eax, 79
    jne __dbase_wfm_flow_type_slot_next_106
    mov rax, __dbase_wfm_output_text_120
    jmp __dbase_wfm_flow_type_slot_done_103
__dbase_wfm_flow_type_slot_next_106:
    cmp eax, 76
    jne __dbase_wfm_flow_type_slot_next_107
    mov rax, __dbase_wfm_output_text_121
    jmp __dbase_wfm_flow_type_slot_done_103
__dbase_wfm_flow_type_slot_next_107:
    cmp eax, 68
    jne __dbase_wfm_flow_type_slot_next_108
    mov rax, __dbase_wfm_output_text_122
    jmp __dbase_wfm_flow_type_slot_done_103
__dbase_wfm_flow_type_slot_next_108:
    mov rax, __dbase_wfm_output_text_123
__dbase_wfm_flow_type_slot_done_103:
    mov qword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_96_ptr], rax
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_96_len], 1
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_96_type], 3
    ; ? VARTYPE(xyz)
    mov rcx, __dbase_wfm_mem___dbase_wfm_flow_type_print_96_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 252
__dbase_wfm_flow_method_exit_82:
    add rsp, 40
    ret
; END WFM PROCEDURE/FUNCTION: __init__


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: __main__
; ------------------------------------------------------------
__dbase_wfm_proc___main__:
    sub rsp, 40
    ; Quellcode Zeile: 258
    mov eax, 7
__dbase_wfm_flow_method_exit_109:
    add rsp, 40
    ret
; END WFM PROCEDURE/FUNCTION: __main__


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: CheckLower
; ------------------------------------------------------------
__dbase_wfm_proc_CheckLower:
    sub rsp, 40
    mov qword ptr [__dbase_wfm_param_CheckLower_c], rcx
    mov dword ptr [__dbase_wfm_mem___wfm_arg_CheckLower_c_type], 3
    mov rax, qword ptr [__dbase_wfm_param_CheckLower_c]
    mov qword ptr [__dbase_wfm_mem___wfm_arg_CheckLower_c_ptr], rax
    mov dword ptr [__dbase_wfm_mem___wfm_arg_CheckLower_c_len], edx
    ; Quellcode Zeile: 343
    cmp dword ptr [__dbase_wfm_mem___wfm_arg_CheckLower_c_type], 3
    je __dbase_wfm_flow_char_case_valid_111
    fldz
    jmp __dbase_wfm_flow_char_case_end_112
__dbase_wfm_flow_char_case_valid_111:
    mov rcx, qword ptr [__dbase_wfm_mem___wfm_arg_CheckLower_c_ptr]
    mov edx, dword ptr [__dbase_wfm_mem___wfm_arg_CheckLower_c_len]
    call DBaseCharIsLowerUtf8
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
__dbase_wfm_flow_char_case_end_112:
    fistp dword ptr [__dbase_temp_number]
    mov eax, dword ptr [__dbase_temp_number]
__dbase_wfm_flow_method_exit_110:
    add rsp, 40
    ret
; END WFM PROCEDURE/FUNCTION: CheckLower


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: PushButton1_onClick
; ------------------------------------------------------------
__dbase_wfm_proc_PushButton1_onClick:
    sub rsp, 40
    mov qword ptr [__dbase_wfm_param_PushButton1_onClick_Sender], rcx
    ; Quellcode Zeile: 275
    ; STORE 101.42 TO Ausdruck
    fld qword ptr [__dbase_wfm_numconst_5]
    fstp qword ptr [__dbase_wfm_mem_Ausdruck_num]
    mov dword ptr [__dbase_wfm_mem_Ausdruck_type], 2
    mov dword ptr [__dbase_wfm_mem_Ausdruck_len], 0
    mov qword ptr [__dbase_wfm_mem_Ausdruck_ptr], 0
    ; Quellcode Zeile: 276
    ; Ausdruck = 101.42
    fld qword ptr [__dbase_wfm_numconst_6]
    fstp qword ptr [__dbase_wfm_mem_Ausdruck_num]
    mov dword ptr [__dbase_wfm_mem_Ausdruck_type], 2
    mov dword ptr [__dbase_wfm_mem_Ausdruck_len], 0
    mov qword ptr [__dbase_wfm_mem_Ausdruck_ptr], 0
    ; Quellcode Zeile: 277
    ; ? Ausdruck
    mov rcx, __dbase_wfm_mem_Ausdruck_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 278
    ; STORE INT(Ausdruck) TO Ausdruck
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 1
    je __dbase_wfm_int_numeric_0
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 2
    je __dbase_wfm_int_numeric_0
    mov dword ptr [__dbase_wfm_mem_Ausdruck_type], 0
    mov dword ptr [__dbase_wfm_mem_Ausdruck_len], 0
    mov qword ptr [__dbase_wfm_mem_Ausdruck_ptr], 0
    jmp __dbase_wfm_int_done_0
__dbase_wfm_int_numeric_0:
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
__dbase_wfm_int_done_0:
    ; Quellcode Zeile: 279
    ; ? Ausdruck
    mov rcx, __dbase_wfm_mem_Ausdruck_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 280
    ; ? "1: " + 101.42
    mov rcx, __dbase_wfm_output_text_124
    mov edx, 3
    mov r8d, 0
    call DBaseQtConsoleWrite
    mov rcx, __dbase_wfm_output_text_125
    mov edx, 6
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 281
    ; ? "2: " + INT(101.42)
    mov rcx, __dbase_wfm_output_text_126
    mov edx, 3
    mov r8d, 0
    call DBaseQtConsoleWrite
    mov rcx, __dbase_wfm_output_text_127
    mov edx, 3
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 282
    ; ? "3: " + Ausdruck
    mov rcx, __dbase_wfm_output_text_128
    mov edx, 3
    mov r8d, 0
    call DBaseQtConsoleWrite
    mov rcx, __dbase_wfm_mem_Ausdruck_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 283
    ; STORE "Zeichenstring" TO SpeicherVar
    mov rax, __dbase_wfm_output_text_129
    mov qword ptr [__dbase_wfm_mem_SpeicherVar_ptr], rax
    mov dword ptr [__dbase_wfm_mem_SpeicherVar_len], 13
    mov dword ptr [__dbase_wfm_mem_SpeicherVar_type], 3
    ; Quellcode Zeile: 284
    ; ? "4: " + SpeicherVar
    mov rcx, __dbase_wfm_output_text_130
    mov edx, 3
    mov r8d, 0
    call DBaseQtConsoleWrite
    mov rcx, __dbase_wfm_mem_SpeicherVar_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 285
    cmp dword ptr [__dbase_wfm_mem_SpeicherVar_type], 3
    je __wfm_upper_1_valid
    mov ecx, 13
    call ExitProcess
__wfm_upper_1_valid:
    fld qword ptr [__dbase_wfm_numconst_7]
    fstp qword ptr [__dbase_wfm_mem___string_arg_2_num]
    mov dword ptr [__dbase_wfm_mem___string_arg_2_type], 2
    mov dword ptr [__dbase_wfm_mem___string_arg_2_len], 0
    mov qword ptr [__dbase_wfm_mem___string_arg_2_ptr], 0
    fld qword ptr [__dbase_wfm_numconst_8]
    fstp qword ptr [__dbase_wfm_mem___string_arg_3_num]
    mov dword ptr [__dbase_wfm_mem___string_arg_3_type], 2
    mov dword ptr [__dbase_wfm_mem___string_arg_3_len], 0
    mov qword ptr [__dbase_wfm_mem___string_arg_3_ptr], 0
    mov eax, dword ptr [__dbase_wfm_mem_SpeicherVar_len]
    mov ecx, eax
    add eax, ecx
    add eax, ecx
    add eax, 1
    mov ecx, eax
    call __dbase_malloc
    test rax, rax
    jne __wfm_upper_4_allocated
    mov ecx, 8
    call ExitProcess
__wfm_upper_4_allocated:
    mov qword ptr [__dbase_wfm_mem___string_arg_4_ptr], rax
    mov eax, dword ptr [__dbase_wfm_mem_SpeicherVar_len]
    mov ecx, eax
    add eax, ecx
    add eax, ecx
    add eax, 1
    mov rcx, qword ptr [__dbase_wfm_mem___string_arg_4_ptr]
    mov edx, eax
    mov r8, qword ptr [__dbase_wfm_mem_SpeicherVar_ptr]
    mov r9d, dword ptr [__dbase_wfm_mem_SpeicherVar_len]
    sub rsp, 64
    mov rax, __dbase_wfm_mem___string_arg_2_num
    mov qword ptr [rsp+32], rax
    mov rax, __dbase_wfm_mem___string_arg_3_num
    mov qword ptr [rsp+40], rax
    call DBaseUtf8SubstringUpper
    add rsp, 64
    cmp eax, -1
    jne __wfm_upper_4_converted
    mov ecx, 13
    call ExitProcess
__wfm_upper_4_converted:
    mov dword ptr [__dbase_wfm_mem___string_arg_4_len], eax
    mov dword ptr [__dbase_wfm_mem___string_arg_4_type], 3
    ; ? "5: " + !($(SpeicherVar, 8, 6))
    mov rcx, __dbase_wfm_output_text_131
    mov edx, 3
    mov r8d, 0
    call DBaseQtConsoleWrite
    mov rcx, __dbase_wfm_mem___string_arg_4_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 286
    ; TestAndNotXor()
    call __dbase_wfm_proc_TestAndNotXor
    ; Quellcode Zeile: 288
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
    ; Quellcode Zeile: 289
    ; IF HatMaus = 1
    fld qword ptr [__dbase_wfm_mem_HatMaus_num]
    fld qword ptr [__dbase_wfm_numconst_9]
    fucomip st0, st1
    fstp st0
    jne __dbase_wfm_flow_if_false_115
    ; Quellcode Zeile: 290
    ; ? "Eine Maus ist vorhanden."
    mov rcx, __dbase_wfm_output_text_132
    mov edx, 24
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 291
    jmp __dbase_wfm_flow_if_end_116
__dbase_wfm_flow_if_false_115:
    ; Quellcode Zeile: 292
    ; ? "Keine Maus erkannt."
    mov rcx, __dbase_wfm_output_text_133
    mov edx, 19
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 293
__dbase_wfm_flow_if_end_116:
    ; Quellcode Zeile: 294
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
    je __dbase_wfm_flow_if_false_117
    fld qword ptr [__dbase_wfm_mem_HatMaus_num]
    fld qword ptr [__dbase_wfm_numconst_10]
    fucomip st0, st1
    fstp st0
    jne __dbase_wfm_flow_if_false_117
    ; Quellcode Zeile: 295
    ; ? "Maus kann verwendet werden."
    mov rcx, __dbase_wfm_output_text_134
    mov edx, 27
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 296
__dbase_wfm_flow_if_false_117:
__dbase_wfm_flow_if_end_118:
    ; Quellcode Zeile: 297
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
    mov rcx, __dbase_wfm_mem___wfm_ismouse_print_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 300
    sub rsp, 64
    mov dword ptr [rsp+32], 0
    mov qword ptr [rsp+40], 0
    mov dword ptr [rsp+48], 0
    xor ecx, ecx
    lea rdx, [rsp+32]
    mov r8d, 16
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_119_done
    mov edx, dword ptr [rsp+32]
    test edx, edx
    jz __dbase_wfm_flow_iskeyboard_119_done
    cmp edx, 268435455
    ja __dbase_wfm_flow_iskeyboard_119_done
    shl rdx, 4
    xor ecx, ecx
    mov r8d, 12288
    mov r9d, 4
    call VirtualAlloc
    test rax, rax
    jz __dbase_wfm_flow_iskeyboard_119_done
    mov qword ptr [rsp+40], rax
    mov rcx, rax
    lea rdx, [rsp+32]
    mov r8d, 16
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_119_release
    test eax, eax
    jz __dbase_wfm_flow_iskeyboard_119_release
    mov r10d, eax
    mov r11, qword ptr [rsp+40]
__dbase_wfm_flow_iskeyboard_119_scan:
    cmp dword ptr [r11+8], 1
    je __dbase_wfm_flow_iskeyboard_119_present
    add r11, 16
    dec r10d
    jnz __dbase_wfm_flow_iskeyboard_119_scan
    jmp __dbase_wfm_flow_iskeyboard_119_release
__dbase_wfm_flow_iskeyboard_119_present:
    mov dword ptr [rsp+48], 1
__dbase_wfm_flow_iskeyboard_119_release:
    mov rcx, qword ptr [rsp+40]
    xor edx, edx
    mov r8d, 32768
    call VirtualFree
__dbase_wfm_flow_iskeyboard_119_done:
    mov eax, dword ptr [rsp+48]
    add rsp, 64
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fstp qword ptr [__dbase_wfm_mem_HatTastatur_num]
    mov dword ptr [__dbase_wfm_mem_HatTastatur_type], 1
    mov dword ptr [__dbase_wfm_mem_HatTastatur_len], 0
    mov qword ptr [__dbase_wfm_mem_HatTastatur_ptr], 0
    ; Quellcode Zeile: 301
    ; IF HatTastatur = 1
    fld qword ptr [__dbase_wfm_mem_HatTastatur_num]
    fld qword ptr [__dbase_wfm_numconst_11]
    fucomip st0, st1
    fstp st0
    jne __dbase_wfm_flow_if_false_120
    ; Quellcode Zeile: 302
    ; ? "Eine Tastatur ist vorhanden."
    mov rcx, __dbase_wfm_output_text_135
    mov edx, 28
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 303
    jmp __dbase_wfm_flow_if_end_121
__dbase_wfm_flow_if_false_120:
    ; Quellcode Zeile: 304
    ; ? "Keine Tastatur erkannt."
    mov rcx, __dbase_wfm_output_text_136
    mov edx, 23
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 305
__dbase_wfm_flow_if_end_121:
    ; Quellcode Zeile: 306
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
    je __dbase_wfm_flow_iskeyboard_124_done
    mov edx, dword ptr [rsp+32]
    test edx, edx
    jz __dbase_wfm_flow_iskeyboard_124_done
    cmp edx, 268435455
    ja __dbase_wfm_flow_iskeyboard_124_done
    shl rdx, 4
    xor ecx, ecx
    mov r8d, 12288
    mov r9d, 4
    call VirtualAlloc
    test rax, rax
    jz __dbase_wfm_flow_iskeyboard_124_done
    mov qword ptr [rsp+40], rax
    mov rcx, rax
    lea rdx, [rsp+32]
    mov r8d, 16
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_124_release
    test eax, eax
    jz __dbase_wfm_flow_iskeyboard_124_release
    mov r10d, eax
    mov r11, qword ptr [rsp+40]
__dbase_wfm_flow_iskeyboard_124_scan:
    cmp dword ptr [r11+8], 1
    je __dbase_wfm_flow_iskeyboard_124_present
    add r11, 16
    dec r10d
    jnz __dbase_wfm_flow_iskeyboard_124_scan
    jmp __dbase_wfm_flow_iskeyboard_124_release
__dbase_wfm_flow_iskeyboard_124_present:
    mov dword ptr [rsp+48], 1
__dbase_wfm_flow_iskeyboard_124_release:
    mov rcx, qword ptr [rsp+40]
    xor edx, edx
    mov r8d, 32768
    call VirtualFree
__dbase_wfm_flow_iskeyboard_124_done:
    mov eax, dword ptr [rsp+48]
    add rsp, 64
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fldz
    fucomip st0, st1
    fstp st0
    je __dbase_wfm_flow_if_false_122
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
    je __dbase_wfm_flow_if_false_122
    ; Quellcode Zeile: 307
    ; ? "Maus und Tastatur sind vorhanden."
    mov rcx, __dbase_wfm_output_text_137
    mov edx, 33
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 308
__dbase_wfm_flow_if_false_122:
__dbase_wfm_flow_if_end_123:
    ; Quellcode Zeile: 309
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
    je __dbase_wfm_flow_iskeyboard_128_done
    mov edx, dword ptr [rsp+32]
    test edx, edx
    jz __dbase_wfm_flow_iskeyboard_128_done
    cmp edx, 268435455
    ja __dbase_wfm_flow_iskeyboard_128_done
    shl rdx, 4
    xor ecx, ecx
    mov r8d, 12288
    mov r9d, 4
    call VirtualAlloc
    test rax, rax
    jz __dbase_wfm_flow_iskeyboard_128_done
    mov qword ptr [rsp+40], rax
    mov rcx, rax
    lea rdx, [rsp+32]
    mov r8d, 16
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_128_release
    test eax, eax
    jz __dbase_wfm_flow_iskeyboard_128_release
    mov r10d, eax
    mov r11, qword ptr [rsp+40]
__dbase_wfm_flow_iskeyboard_128_scan:
    cmp dword ptr [r11+8], 1
    je __dbase_wfm_flow_iskeyboard_128_present
    add r11, 16
    dec r10d
    jnz __dbase_wfm_flow_iskeyboard_128_scan
    jmp __dbase_wfm_flow_iskeyboard_128_release
__dbase_wfm_flow_iskeyboard_128_present:
    mov dword ptr [rsp+48], 1
__dbase_wfm_flow_iskeyboard_128_release:
    mov rcx, qword ptr [rsp+40]
    xor edx, edx
    mov r8d, 32768
    call VirtualFree
__dbase_wfm_flow_iskeyboard_128_done:
    mov eax, dword ptr [rsp+48]
    add rsp, 64
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fldz
    fucomip st0, st1
    fstp st0
    jne __dbase_wfm_flow_if_false_125
__dbase_wfm_flow_not_true_127:
    ; Quellcode Zeile: 310
    ; ? "Keine Tastatur gefunden."
    mov rcx, __dbase_wfm_output_text_138
    mov edx, 24
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 311
__dbase_wfm_flow_if_false_125:
__dbase_wfm_flow_if_end_126:
    ; Quellcode Zeile: 312
    sub rsp, 64
    mov dword ptr [rsp+32], 0
    mov qword ptr [rsp+40], 0
    mov dword ptr [rsp+48], 0
    xor ecx, ecx
    lea rdx, [rsp+32]
    mov r8d, 16
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_129_done
    mov edx, dword ptr [rsp+32]
    test edx, edx
    jz __dbase_wfm_flow_iskeyboard_129_done
    cmp edx, 268435455
    ja __dbase_wfm_flow_iskeyboard_129_done
    shl rdx, 4
    xor ecx, ecx
    mov r8d, 12288
    mov r9d, 4
    call VirtualAlloc
    test rax, rax
    jz __dbase_wfm_flow_iskeyboard_129_done
    mov qword ptr [rsp+40], rax
    mov rcx, rax
    lea rdx, [rsp+32]
    mov r8d, 16
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_129_release
    test eax, eax
    jz __dbase_wfm_flow_iskeyboard_129_release
    mov r10d, eax
    mov r11, qword ptr [rsp+40]
__dbase_wfm_flow_iskeyboard_129_scan:
    cmp dword ptr [r11+8], 1
    je __dbase_wfm_flow_iskeyboard_129_present
    add r11, 16
    dec r10d
    jnz __dbase_wfm_flow_iskeyboard_129_scan
    jmp __dbase_wfm_flow_iskeyboard_129_release
__dbase_wfm_flow_iskeyboard_129_present:
    mov dword ptr [rsp+48], 1
__dbase_wfm_flow_iskeyboard_129_release:
    mov rcx, qword ptr [rsp+40]
    xor edx, edx
    mov r8d, 32768
    call VirtualFree
__dbase_wfm_flow_iskeyboard_129_done:
    mov eax, dword ptr [rsp+48]
    add rsp, 64
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fstp qword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_num]
    mov dword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_type], 1
    mov dword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_len], 0
    mov qword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_ptr], 0
    ; ? iskeyboard()
    mov rcx, __dbase_wfm_mem___wfm_iskeyboard_print_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 315
    ; STORE 'A' TO Zeichen
    mov rax, __dbase_wfm_output_text_139
    mov qword ptr [__dbase_wfm_mem_Zeichen_ptr], rax
    mov dword ptr [__dbase_wfm_mem_Zeichen_len], 1
    mov dword ptr [__dbase_wfm_mem_Zeichen_type], 3
    ; Quellcode Zeile: 316
    ; IF ISUPPER(Zeichen)
    cmp dword ptr [__dbase_wfm_mem_Zeichen_type], 3
    je __dbase_wfm_flow_char_case_valid_132
    fldz
    jmp __dbase_wfm_flow_char_case_end_133
__dbase_wfm_flow_char_case_valid_132:
    mov rcx, qword ptr [__dbase_wfm_mem_Zeichen_ptr]
    mov edx, dword ptr [__dbase_wfm_mem_Zeichen_len]
    call DBaseCharIsUpperUtf8
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
__dbase_wfm_flow_char_case_end_133:
    fldz
    fucomip st0, st1
    fstp st0
    je __dbase_wfm_flow_if_false_130
    ; Quellcode Zeile: 317
    ; ? "Grossbuchstabe erkannt"
    mov rcx, __dbase_wfm_output_text_140
    mov edx, 22
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 318
__dbase_wfm_flow_if_false_130:
__dbase_wfm_flow_if_end_131:
    ; Quellcode Zeile: 319
    ; IF CheckLower('z')
    mov rcx, __dbase_wfm_text_141
    mov edx, 1
    call __dbase_wfm_proc_CheckLower
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fldz
    fucomip st0, st1
    fstp st0
    je __dbase_wfm_flow_if_false_135
    ; Quellcode Zeile: 320
    ; ? "Kleinbuchstabe erkannt"
    mov rcx, __dbase_wfm_output_text_142
    mov edx, 22
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 321
__dbase_wfm_flow_if_false_135:
__dbase_wfm_flow_if_end_136:
    ; Quellcode Zeile: 323
    mov rax, __dbase_wfm_output_text_143
    mov qword ptr [__dbase_wfm_mem___wfm_text_literal_5_ptr], rax
    mov dword ptr [__dbase_wfm_mem___wfm_text_literal_5_len], 10
    mov dword ptr [__dbase_wfm_mem___wfm_text_literal_5_type], 3
    cmp dword ptr [__dbase_wfm_mem___wfm_text_literal_5_type], 3
    je __dbase_wfm_flow_len_valid_137
    xor ecx, ecx
    jmp __dbase_wfm_flow_len_skip_140
__dbase_wfm_flow_len_valid_137:
    mov r8, qword ptr [__dbase_wfm_mem___wfm_text_literal_5_ptr]
    mov r9d, dword ptr [__dbase_wfm_mem___wfm_text_literal_5_len]
    xor ecx, ecx
__dbase_wfm_flow_len_loop_139:
    test r8, r8
    je __dbase_wfm_flow_len_finish_141
    test r9d, r9d
    jz __dbase_wfm_flow_len_finish_141
    movzx eax, byte ptr [r8]
    and eax, 192
    cmp eax, 128
    je len___dbase_wfm_flow_len_loop_139_continuation
    inc ecx
len___dbase_wfm_flow_len_loop_139_continuation:
    inc r8
    dec r9d
    jmp __dbase_wfm_flow_len_loop_139
__dbase_wfm_flow_len_finish_141:
__dbase_wfm_flow_len_skip_140:
    mov dword ptr [__dbase_temp_number], ecx
    fild dword ptr [__dbase_temp_number]
    fstp qword ptr [__dbase_wfm_mem___wfm_len_6_num]
    mov dword ptr [__dbase_wfm_mem___wfm_len_6_type], 1
    mov dword ptr [__dbase_wfm_mem___wfm_len_6_len], 0
    mov qword ptr [__dbase_wfm_mem___wfm_len_6_ptr], 0
    ; ? LEN("Ein String")
    mov rcx, __dbase_wfm_mem___wfm_len_6_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 326
    ; STORE "   Hallo Welt   " TO Text
    mov rax, __dbase_wfm_output_text_144
    mov qword ptr [__dbase_wfm_mem_Text_ptr], rax
    mov dword ptr [__dbase_wfm_mem_Text_len], 16
    mov dword ptr [__dbase_wfm_mem_Text_type], 3
    ; Quellcode Zeile: 328
    cmp dword ptr [__dbase_wfm_mem_Text_type], 3
    je __dbase_wfm_flow_len_valid_142
    xor ecx, ecx
    jmp __dbase_wfm_flow_len_skip_145
__dbase_wfm_flow_len_valid_142:
    mov r8, qword ptr [__dbase_wfm_mem_Text_ptr]
    mov r9d, dword ptr [__dbase_wfm_mem_Text_len]
    xor ecx, ecx
__dbase_wfm_flow_len_loop_144:
    test r8, r8
    je __dbase_wfm_flow_len_finish_146
    test r9d, r9d
    jz __dbase_wfm_flow_len_finish_146
    movzx eax, byte ptr [r8]
    and eax, 192
    cmp eax, 128
    je len___dbase_wfm_flow_len_loop_144_continuation
    inc ecx
len___dbase_wfm_flow_len_loop_144_continuation:
    inc r8
    dec r9d
    jmp __dbase_wfm_flow_len_loop_144
__dbase_wfm_flow_len_finish_146:
__dbase_wfm_flow_len_skip_145:
    mov dword ptr [__dbase_temp_number], ecx
    fild dword ptr [__dbase_temp_number]
    fstp qword ptr [__dbase_wfm_mem___wfm_len_7_num]
    mov dword ptr [__dbase_wfm_mem___wfm_len_7_type], 1
    mov dword ptr [__dbase_wfm_mem___wfm_len_7_len], 0
    mov qword ptr [__dbase_wfm_mem___wfm_len_7_ptr], 0
    ; ? LEN(Text)
    mov rcx, __dbase_wfm_mem___wfm_len_7_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 331
    cmp dword ptr [__dbase_wfm_mem_Text_type], 3
    je __dbase_wfm_flow_ltrim_valid_147
    mov rax, __dbase_wfm_output_text_146
    mov qword ptr [__dbase_wfm_mem___wfm_ltrim_8_ptr], rax
    mov dword ptr [__dbase_wfm_mem___wfm_ltrim_8_len], 0
    mov dword ptr [__dbase_wfm_mem___wfm_ltrim_8_type], 3
    jmp __dbase_wfm_flow_ltrim_done_148
__dbase_wfm_flow_ltrim_valid_147:
    mov eax, dword ptr [__dbase_wfm_mem_Text_len]
    inc eax
    mov ecx, eax
    call __dbase_malloc
    test rax, rax
    jne __dbase_wfm_flow_trim_ltrim_149_allocated
    mov ecx, 8
    sub rsp, 40
    call ExitProcess
__dbase_wfm_flow_trim_ltrim_149_allocated:
    mov qword ptr [__dbase_wfm_mem___wfm_ltrim_8_ptr], rax
    push rsi
    push rdi
    mov rsi, qword ptr [__dbase_wfm_mem_Text_ptr]
    mov rdi, rsi
    mov eax, dword ptr [__dbase_wfm_mem_Text_len]
    add rdi, rax
__dbase_wfm_flow_trim_ltrim_149_left_loop:
    cmp rsi, rdi
    jae __dbase_wfm_flow_trim_ltrim_149_left_done
    mov al, byte ptr [rsi]
    cmp al, 32
    jne __dbase_wfm_flow_trim_ltrim_149_left_done
__dbase_wfm_flow_trim_ltrim_149_left_advance:
    inc rsi
    jmp __dbase_wfm_flow_trim_ltrim_149_left_loop
__dbase_wfm_flow_trim_ltrim_149_left_done:
    sub rdi, rsi
    mov dword ptr [__dbase_wfm_mem___wfm_ltrim_8_len], edi
    mov dword ptr [__dbase_wfm_mem___wfm_ltrim_8_type], 3
    mov ecx, edi
    mov rdi, qword ptr [__dbase_wfm_mem___wfm_ltrim_8_ptr]
__dbase_wfm_flow_trim_ltrim_149_copy_loop:
    test ecx, ecx
    je __dbase_wfm_flow_trim_ltrim_149_copy_done
    movzx eax, byte ptr [rsi]
    mov byte ptr [rdi], al
    inc rsi
    inc rdi
    dec ecx
    jmp __dbase_wfm_flow_trim_ltrim_149_copy_loop
__dbase_wfm_flow_trim_ltrim_149_copy_done:
    mov byte ptr [rdi], 0
    pop rdi
    pop rsi
__dbase_wfm_flow_ltrim_done_148:
    ; ? "[" + LTRIM(Text) + "]"
    mov rcx, __dbase_wfm_output_text_145
    mov edx, 1
    mov r8d, 0
    call DBaseQtConsoleWrite
    mov rcx, __dbase_wfm_mem___wfm_ltrim_8_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 0
    call DBaseQtConsoleWrite
    mov rcx, __dbase_wfm_output_text_147
    mov edx, 1
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 334
    cmp dword ptr [__dbase_wfm_mem_Text_type], 3
    je __dbase_wfm_flow_trim_valid_150
    mov rax, __dbase_wfm_output_text_149
    mov qword ptr [__dbase_wfm_mem___wfm_trim_9_ptr], rax
    mov dword ptr [__dbase_wfm_mem___wfm_trim_9_len], 0
    mov dword ptr [__dbase_wfm_mem___wfm_trim_9_type], 3
    jmp __dbase_wfm_flow_trim_done_151
__dbase_wfm_flow_trim_valid_150:
    mov eax, dword ptr [__dbase_wfm_mem_Text_len]
    inc eax
    mov ecx, eax
    call __dbase_malloc
    test rax, rax
    jne __dbase_wfm_flow_trim_trim_152_allocated
    mov ecx, 8
    sub rsp, 40
    call ExitProcess
__dbase_wfm_flow_trim_trim_152_allocated:
    mov qword ptr [__dbase_wfm_mem___wfm_trim_9_ptr], rax
    push rsi
    push rdi
    mov rsi, qword ptr [__dbase_wfm_mem_Text_ptr]
    mov rdi, rsi
    mov eax, dword ptr [__dbase_wfm_mem_Text_len]
    add rdi, rax
__dbase_wfm_flow_trim_trim_152_left_loop:
    cmp rsi, rdi
    jae __dbase_wfm_flow_trim_trim_152_left_done
    mov al, byte ptr [rsi]
    cmp al, 32
    je __dbase_wfm_flow_trim_trim_152_left_advance
    cmp al, 9
    je __dbase_wfm_flow_trim_trim_152_left_advance
    cmp al, 10
    je __dbase_wfm_flow_trim_trim_152_left_advance
    cmp al, 8
    je __dbase_wfm_flow_trim_trim_152_left_advance
    cmp al, 13
    jne __dbase_wfm_flow_trim_trim_152_left_done
__dbase_wfm_flow_trim_trim_152_left_advance:
    inc rsi
    jmp __dbase_wfm_flow_trim_trim_152_left_loop
__dbase_wfm_flow_trim_trim_152_left_done:
__dbase_wfm_flow_trim_trim_152_right_loop:
    cmp rdi, rsi
    jbe __dbase_wfm_flow_trim_trim_152_right_done
    mov al, byte ptr [rdi-1]
    cmp al, 32
    je __dbase_wfm_flow_trim_trim_152_right_retreat
    cmp al, 9
    je __dbase_wfm_flow_trim_trim_152_right_retreat
    cmp al, 10
    je __dbase_wfm_flow_trim_trim_152_right_retreat
    cmp al, 8
    je __dbase_wfm_flow_trim_trim_152_right_retreat
    cmp al, 13
    jne __dbase_wfm_flow_trim_trim_152_right_done
__dbase_wfm_flow_trim_trim_152_right_retreat:
    dec rdi
    jmp __dbase_wfm_flow_trim_trim_152_right_loop
__dbase_wfm_flow_trim_trim_152_right_done:
    sub rdi, rsi
    mov dword ptr [__dbase_wfm_mem___wfm_trim_9_len], edi
    mov dword ptr [__dbase_wfm_mem___wfm_trim_9_type], 3
    mov ecx, edi
    mov rdi, qword ptr [__dbase_wfm_mem___wfm_trim_9_ptr]
__dbase_wfm_flow_trim_trim_152_copy_loop:
    test ecx, ecx
    je __dbase_wfm_flow_trim_trim_152_copy_done
    movzx eax, byte ptr [rsi]
    mov byte ptr [rdi], al
    inc rsi
    inc rdi
    dec ecx
    jmp __dbase_wfm_flow_trim_trim_152_copy_loop
__dbase_wfm_flow_trim_trim_152_copy_done:
    mov byte ptr [rdi], 0
    pop rdi
    pop rsi
__dbase_wfm_flow_trim_done_151:
    ; ? "[" + TRIM(Text) + "]"
    mov rcx, __dbase_wfm_output_text_148
    mov edx, 1
    mov r8d, 0
    call DBaseQtConsoleWrite
    mov rcx, __dbase_wfm_mem___wfm_trim_9_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 0
    call DBaseQtConsoleWrite
    mov rcx, __dbase_wfm_output_text_150
    mov edx, 1
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 337
    cmp dword ptr [__dbase_wfm_mem_Text_type], 3
    je __dbase_wfm_flow_trim_valid_153
    mov rax, __dbase_wfm_output_text_151
    mov qword ptr [__dbase_wfm_mem___wfm_trim_10_ptr], rax
    mov dword ptr [__dbase_wfm_mem___wfm_trim_10_len], 0
    mov dword ptr [__dbase_wfm_mem___wfm_trim_10_type], 3
    jmp __dbase_wfm_flow_trim_done_154
__dbase_wfm_flow_trim_valid_153:
    mov eax, dword ptr [__dbase_wfm_mem_Text_len]
    inc eax
    mov ecx, eax
    call __dbase_malloc
    test rax, rax
    jne __dbase_wfm_flow_trim_trim_155_allocated
    mov ecx, 8
    sub rsp, 40
    call ExitProcess
__dbase_wfm_flow_trim_trim_155_allocated:
    mov qword ptr [__dbase_wfm_mem___wfm_trim_10_ptr], rax
    push rsi
    push rdi
    mov rsi, qword ptr [__dbase_wfm_mem_Text_ptr]
    mov rdi, rsi
    mov eax, dword ptr [__dbase_wfm_mem_Text_len]
    add rdi, rax
__dbase_wfm_flow_trim_trim_155_left_loop:
    cmp rsi, rdi
    jae __dbase_wfm_flow_trim_trim_155_left_done
    mov al, byte ptr [rsi]
    cmp al, 32
    je __dbase_wfm_flow_trim_trim_155_left_advance
    cmp al, 9
    je __dbase_wfm_flow_trim_trim_155_left_advance
    cmp al, 10
    je __dbase_wfm_flow_trim_trim_155_left_advance
    cmp al, 8
    je __dbase_wfm_flow_trim_trim_155_left_advance
    cmp al, 13
    jne __dbase_wfm_flow_trim_trim_155_left_done
__dbase_wfm_flow_trim_trim_155_left_advance:
    inc rsi
    jmp __dbase_wfm_flow_trim_trim_155_left_loop
__dbase_wfm_flow_trim_trim_155_left_done:
__dbase_wfm_flow_trim_trim_155_right_loop:
    cmp rdi, rsi
    jbe __dbase_wfm_flow_trim_trim_155_right_done
    mov al, byte ptr [rdi-1]
    cmp al, 32
    je __dbase_wfm_flow_trim_trim_155_right_retreat
    cmp al, 9
    je __dbase_wfm_flow_trim_trim_155_right_retreat
    cmp al, 10
    je __dbase_wfm_flow_trim_trim_155_right_retreat
    cmp al, 8
    je __dbase_wfm_flow_trim_trim_155_right_retreat
    cmp al, 13
    jne __dbase_wfm_flow_trim_trim_155_right_done
__dbase_wfm_flow_trim_trim_155_right_retreat:
    dec rdi
    jmp __dbase_wfm_flow_trim_trim_155_right_loop
__dbase_wfm_flow_trim_trim_155_right_done:
    sub rdi, rsi
    mov dword ptr [__dbase_wfm_mem___wfm_trim_10_len], edi
    mov dword ptr [__dbase_wfm_mem___wfm_trim_10_type], 3
    mov ecx, edi
    mov rdi, qword ptr [__dbase_wfm_mem___wfm_trim_10_ptr]
__dbase_wfm_flow_trim_trim_155_copy_loop:
    test ecx, ecx
    je __dbase_wfm_flow_trim_trim_155_copy_done
    movzx eax, byte ptr [rsi]
    mov byte ptr [rdi], al
    inc rsi
    inc rdi
    dec ecx
    jmp __dbase_wfm_flow_trim_trim_155_copy_loop
__dbase_wfm_flow_trim_trim_155_copy_done:
    mov byte ptr [rdi], 0
    pop rdi
    pop rsi
__dbase_wfm_flow_trim_done_154:
    mov eax, dword ptr [__dbase_wfm_mem___wfm_trim_10_type]
    mov dword ptr [__dbase_wfm_mem_Ergebnis_type], eax
    fld qword ptr [__dbase_wfm_mem___wfm_trim_10_num]
    fstp qword ptr [__dbase_wfm_mem_Ergebnis_num]
    mov eax, dword ptr [__dbase_wfm_mem___wfm_trim_10_len]
    mov dword ptr [__dbase_wfm_mem_Ergebnis_len], eax
    mov rax, qword ptr [__dbase_wfm_mem___wfm_trim_10_ptr]
    mov qword ptr [__dbase_wfm_mem_Ergebnis_ptr], rax
    ; Quellcode Zeile: 338
    cmp dword ptr [__dbase_wfm_mem_Ergebnis_type], 3
    je __dbase_wfm_flow_len_valid_156
    xor ecx, ecx
    jmp __dbase_wfm_flow_len_skip_159
__dbase_wfm_flow_len_valid_156:
    mov r8, qword ptr [__dbase_wfm_mem_Ergebnis_ptr]
    mov r9d, dword ptr [__dbase_wfm_mem_Ergebnis_len]
    xor ecx, ecx
__dbase_wfm_flow_len_loop_158:
    test r8, r8
    je __dbase_wfm_flow_len_finish_160
    test r9d, r9d
    jz __dbase_wfm_flow_len_finish_160
    movzx eax, byte ptr [r8]
    and eax, 192
    cmp eax, 128
    je len___dbase_wfm_flow_len_loop_158_continuation
    inc ecx
len___dbase_wfm_flow_len_loop_158_continuation:
    inc r8
    dec r9d
    jmp __dbase_wfm_flow_len_loop_158
__dbase_wfm_flow_len_finish_160:
__dbase_wfm_flow_len_skip_159:
    mov dword ptr [__dbase_temp_number], ecx
    fild dword ptr [__dbase_temp_number]
    fstp qword ptr [__dbase_wfm_mem___wfm_len_11_num]
    mov dword ptr [__dbase_wfm_mem___wfm_len_11_type], 1
    mov dword ptr [__dbase_wfm_mem___wfm_len_11_len], 0
    mov qword ptr [__dbase_wfm_mem___wfm_len_11_ptr], 0
    ; ? LEN(Ergebnis)
    mov rcx, __dbase_wfm_mem___wfm_len_11_type
    mov rdx, qword ptr [__dbase_format_buffer]
    mov r8, __dbase_wfm_format_result
    call DBaseWfmFormatValue
    mov rcx, qword ptr [__dbase_wfm_format_result]
    mov edx, dword ptr [__dbase_wfm_format_result_len]
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 340
__dbase_wfm_flow_method_exit_114:
    add rsp, 40
    ret
; END WFM PROCEDURE/FUNCTION: PushButton1_onClick


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: TestAndNotXor
; ------------------------------------------------------------
__dbase_wfm_proc_TestAndNotXor:
    sub rsp, 40
    ; Quellcode Zeile: 261
    ; IF A > 0 .AND. C < 10
    fld qword ptr [__dbase_wfm_mem_A_num]
    fld qword ptr [__dbase_wfm_numconst_12]
    fucomip st0, st1
    fstp st0
    jae __dbase_wfm_flow_if_false_162
    fld qword ptr [__dbase_wfm_mem_C_num]
    fld qword ptr [__dbase_wfm_numconst_13]
    fucomip st0, st1
    fstp st0
    jbe __dbase_wfm_flow_if_false_162
    ; Quellcode Zeile: 262
    ; ? "Beide Bedingungen erfüllt"
    mov rcx, __dbase_wfm_output_text_152
    mov edx, 26
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 263
    jmp __dbase_wfm_flow_if_end_163
__dbase_wfm_flow_if_false_162:
    ; Quellcode Zeile: 264
    ; ? "Bedingung nicht erfüllt"
    mov rcx, __dbase_wfm_output_text_153
    mov edx, 24
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 265
__dbase_wfm_flow_if_end_163:
    ; Quellcode Zeile: 266
    ; IF .NOT. (A = 0 .OR. C >= 10)
    fld qword ptr [__dbase_wfm_mem_A_num]
    fld qword ptr [__dbase_wfm_numconst_14]
    fucomip st0, st1
    fstp st0
    je __dbase_wfm_flow_or_true_167
__dbase_wfm_flow_not_true_168:
    fld qword ptr [__dbase_wfm_mem_C_num]
    fld qword ptr [__dbase_wfm_numconst_15]
    fucomip st0, st1
    fstp st0
    ja __dbase_wfm_flow_not_true_166
__dbase_wfm_flow_or_true_167:
    jmp __dbase_wfm_flow_if_false_164
__dbase_wfm_flow_not_true_166:
    ; Quellcode Zeile: 267
    ; ? "NOT und OR funktionieren"
    mov rcx, __dbase_wfm_output_text_154
    mov edx, 24
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 268
__dbase_wfm_flow_if_false_164:
__dbase_wfm_flow_if_end_165:
    ; Quellcode Zeile: 269
    ; IF (A > 0) .XOR. (C < 0)
    fld qword ptr [__dbase_wfm_mem_A_num]
    fld qword ptr [__dbase_wfm_numconst_16]
    fucomip st0, st1
    fstp st0
    jae __dbase_wfm_flow_xor_left_false_171
    fld qword ptr [__dbase_wfm_mem_C_num]
    fld qword ptr [__dbase_wfm_numconst_17]
    fucomip st0, st1
    fstp st0
    ja __dbase_wfm_flow_if_false_169
__dbase_wfm_flow_not_true_173:
    jmp __dbase_wfm_flow_xor_done_172
__dbase_wfm_flow_xor_left_false_171:
    fld qword ptr [__dbase_wfm_mem_C_num]
    fld qword ptr [__dbase_wfm_numconst_18]
    fucomip st0, st1
    fstp st0
    jbe __dbase_wfm_flow_if_false_169
__dbase_wfm_flow_xor_done_172:
    ; Quellcode Zeile: 270
    ; ? "Genau eine Bedingung ist wahr"
    mov rcx, __dbase_wfm_output_text_155
    mov edx, 29
    mov r8d, 1
    call DBaseQtConsoleWrite
    ; Quellcode Zeile: 271
__dbase_wfm_flow_if_false_169:
__dbase_wfm_flow_if_end_170:
    ; Quellcode Zeile: 272
__dbase_wfm_flow_method_exit_161:
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
__dbase_wfm_text_141:
    db 122, 92, 48
__dbase_wfm_output_text_75:
    db 115, 104, 101, 108, 108, 51, 50, 46, 100, 108, 108
__dbase_wfm_flow_ffi_ansi_4:
    db 111, 112, 101, 110, 0
__dbase_wfm_flow_ffi_ansi_6:
    db 110, 111, 116, 101, 112, 97, 100, 46, 101, 120, 101, 0
__dbase_wfm_output_text_76:
    db 78
__dbase_wfm_output_text_77:
    db 67
__dbase_wfm_output_text_78:
    db 79
__dbase_wfm_output_text_79:
    db 76
__dbase_wfm_output_text_80:
    db 68
__dbase_wfm_output_text_81:
    db 85
__dbase_wfm_output_text_82:
    db 78
__dbase_wfm_output_text_83:
    db 67
__dbase_wfm_output_text_84:
    db 79
__dbase_wfm_output_text_85:
    db 76
__dbase_wfm_output_text_86:
    db 68
__dbase_wfm_output_text_87:
    db 85
__dbase_wfm_output_text_88:
    db 120, 121, 122, 32, 105, 115, 116, 32, 110, 117, 109, 101, 114, 105, 115, 99, 104
__dbase_wfm_output_text_89:
    db 72, 97, 108, 108, 111
__dbase_wfm_output_text_90:
    db 78
__dbase_wfm_output_text_91:
    db 67
__dbase_wfm_output_text_92:
    db 79
__dbase_wfm_output_text_93:
    db 76
__dbase_wfm_output_text_94:
    db 68
__dbase_wfm_output_text_95:
    db 85
__dbase_wfm_output_text_96:
    db 78
__dbase_wfm_output_text_97:
    db 67
__dbase_wfm_output_text_98:
    db 79
__dbase_wfm_output_text_99:
    db 76
__dbase_wfm_output_text_100:
    db 68
__dbase_wfm_output_text_101:
    db 85
__dbase_wfm_output_text_102:
    db 78
__dbase_wfm_output_text_103:
    db 67
__dbase_wfm_output_text_104:
    db 79
__dbase_wfm_output_text_105:
    db 76
__dbase_wfm_output_text_106:
    db 68
__dbase_wfm_output_text_107:
    db 85
__dbase_wfm_output_text_108:
    db 112, 49, 32, 61, 32
__dbase_wfm_output_text_109:
    db 53, 49
__dbase_wfm_output_text_110:
    db 112, 50, 32, 61, 32
__dbase_wfm_output_text_111:
    db 52
__dbase_wfm_output_text_112:
    db 78
__dbase_wfm_output_text_113:
    db 67
__dbase_wfm_output_text_114:
    db 79
__dbase_wfm_output_text_115:
    db 76
__dbase_wfm_output_text_116:
    db 68
__dbase_wfm_output_text_117:
    db 85
__dbase_wfm_output_text_118:
    db 78
__dbase_wfm_output_text_119:
    db 67
__dbase_wfm_output_text_120:
    db 79
__dbase_wfm_output_text_121:
    db 76
__dbase_wfm_output_text_122:
    db 68
__dbase_wfm_output_text_123:
    db 85
__dbase_wfm_output_text_124:
    db 49, 58, 32
__dbase_wfm_output_text_125:
    db 49, 48, 49, 46, 52, 50
__dbase_wfm_output_text_126:
    db 50, 58, 32
__dbase_wfm_output_text_127:
    db 49, 48, 49
__dbase_wfm_output_text_128:
    db 51, 58, 32
__dbase_wfm_output_text_129:
    db 90, 101, 105, 99, 104, 101, 110, 115, 116, 114, 105, 110, 103
__dbase_wfm_output_text_130:
    db 52, 58, 32
__dbase_wfm_output_text_131:
    db 53, 58, 32
__dbase_wfm_output_text_132:
    db 69, 105, 110, 101, 32, 77, 97, 117, 115, 32, 105, 115, 116, 32, 118, 111, 114, 104, 97, 110, 100, 101, 110, 46
__dbase_wfm_output_text_133:
    db 75, 101, 105, 110, 101, 32, 77, 97, 117, 115, 32, 101, 114, 107, 97, 110, 110, 116, 46
__dbase_wfm_output_text_134:
    db 77, 97, 117, 115, 32, 107, 97, 110, 110, 32, 118, 101, 114, 119, 101, 110, 100, 101, 116, 32, 119, 101, 114, 100, 101, 110, 46
__dbase_wfm_output_text_135:
    db 69, 105, 110, 101, 32, 84, 97, 115, 116, 97, 116, 117, 114, 32, 105, 115, 116, 32, 118, 111, 114, 104, 97, 110, 100, 101, 110, 46
__dbase_wfm_output_text_136:
    db 75, 101, 105, 110, 101, 32, 84, 97, 115, 116, 97, 116, 117, 114, 32, 101, 114, 107, 97, 110, 110, 116, 46
__dbase_wfm_output_text_137:
    db 77, 97, 117, 115, 32, 117, 110, 100, 32, 84, 97, 115, 116, 97, 116, 117, 114, 32, 115, 105, 110, 100, 32, 118, 111, 114, 104, 97, 110, 100, 101, 110, 46
__dbase_wfm_output_text_138:
    db 75, 101, 105, 110, 101, 32, 84, 97, 115, 116, 97, 116, 117, 114, 32, 103, 101, 102, 117, 110, 100, 101, 110, 46
__dbase_wfm_output_text_139:
    db 65
__dbase_wfm_output_text_140:
    db 71, 114, 111, 115, 115, 98, 117, 99, 104, 115, 116, 97, 98, 101, 32, 101, 114, 107, 97, 110, 110, 116
__dbase_wfm_output_text_142:
    db 75, 108, 101, 105, 110, 98, 117, 99, 104, 115, 116, 97, 98, 101, 32, 101, 114, 107, 97, 110, 110, 116
__dbase_wfm_output_text_143:
    db 69, 105, 110, 32, 83, 116, 114, 105, 110, 103
__dbase_wfm_output_text_144:
    db 32, 32, 32, 72, 97, 108, 108, 111, 32, 87, 101, 108, 116, 32, 32, 32
__dbase_wfm_output_text_145:
    db 91
__dbase_wfm_output_text_146:
    db 0
__dbase_wfm_output_text_147:
    db 93
__dbase_wfm_output_text_148:
    db 91
__dbase_wfm_output_text_149:
    db 0
__dbase_wfm_output_text_150:
    db 93
__dbase_wfm_output_text_151:
    db 0
__dbase_wfm_output_text_152:
    db 66, 101, 105, 100, 101, 32, 66, 101, 100, 105, 110, 103, 117, 110, 103, 101, 110, 32, 101, 114, 102, 195, 188, 108, 108, 116
__dbase_wfm_output_text_153:
    db 66, 101, 100, 105, 110, 103, 117, 110, 103, 32, 110, 105, 99, 104, 116, 32, 101, 114, 102, 195, 188, 108, 108, 116
__dbase_wfm_output_text_154:
    db 78, 79, 84, 32, 117, 110, 100, 32, 79, 82, 32, 102, 117, 110, 107, 116, 105, 111, 110, 105, 101, 114, 101, 110
__dbase_wfm_output_text_155:
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
    dd 0, 0
__dbase_wfm_numconst_1:
    dd 0, 1072693248
__dbase_wfm_numconst_2:
    dd 0, 1075970048
__dbase_wfm_numconst_3:
    dd 0, 1074790400
__dbase_wfm_numconst_4:
    dd 3435973837, 1079958732
__dbase_wfm_numconst_5:
    dd 1202590843, 1079597793
__dbase_wfm_numconst_6:
    dd 1202590843, 1079597793
__dbase_wfm_numconst_7:
    dd 0, 1075838976
__dbase_wfm_numconst_8:
    dd 0, 1075314688
__dbase_wfm_numconst_9:
    dd 0, 1072693248
__dbase_wfm_numconst_10:
    dd 0, 1072693248
__dbase_wfm_numconst_11:
    dd 0, 1072693248
__dbase_wfm_numconst_12:
    dd 0, 0
__dbase_wfm_numconst_13:
    dd 0, 1076101120
__dbase_wfm_numconst_14:
    dd 0, 0
__dbase_wfm_numconst_15:
    dd 0, 1076101120
__dbase_wfm_numconst_16:
    dd 0, 0
__dbase_wfm_numconst_17:
    dd 0, 0
__dbase_wfm_numconst_18:
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
__dbase_wfm_param_CheckLower_c:
    resq 1
__dbase_wfm_param_PushButton1_onClick_Sender:
    resq 1

; Stage 449: shared WFM formatter's output (ptr, length)
__dbase_wfm_format_result:
    resq 1
__dbase_wfm_format_result_len:
    resd 1

; Stage 223: typed dBase WFM memory variables (.bss)
__dbase_wfm_mem_result_type:
    resd 1
__dbase_wfm_mem_result_num:
    resq 1
__dbase_wfm_mem_result_ptr:
    resq 1
__dbase_wfm_mem_result_len:
    resd 1
__dbase_wfm_mem_xyz_type:
    resd 1
__dbase_wfm_mem_xyz_num:
    resq 1
__dbase_wfm_mem_xyz_ptr:
    resq 1
__dbase_wfm_mem_xyz_len:
    resd 1
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
__dbase_wfm_mem_Zeichen_type:
    resd 1
__dbase_wfm_mem_Zeichen_num:
    resq 1
__dbase_wfm_mem_Zeichen_ptr:
    resq 1
__dbase_wfm_mem_Zeichen_len:
    resd 1
__dbase_wfm_mem_Text_type:
    resd 1
__dbase_wfm_mem_Text_num:
    resq 1
__dbase_wfm_mem_Text_ptr:
    resq 1
__dbase_wfm_mem_Text_len:
    resd 1
__dbase_wfm_mem_Ergebnis_type:
    resd 1
__dbase_wfm_mem_Ergebnis_num:
    resq 1
__dbase_wfm_mem_Ergebnis_ptr:
    resq 1
__dbase_wfm_mem_Ergebnis_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_ptr:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_ptr:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_ptr:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_ptr:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_ptr:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_ptr:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_14_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_14_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_14_ptr:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_14_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_27_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_27_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_27_ptr:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_27_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_48_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_48_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_48_ptr:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_48_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_61_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_61_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_61_ptr:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_61_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_74_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_74_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_74_ptr:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_74_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_83_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_83_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_83_ptr:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_83_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_96_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_96_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_96_ptr:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_96_len:
    resd 1
__dbase_wfm_mem___wfm_arg_CheckLower_c_type:
    resd 1
__dbase_wfm_mem___wfm_arg_CheckLower_c_num:
    resq 1
__dbase_wfm_mem___wfm_arg_CheckLower_c_ptr:
    resq 1
__dbase_wfm_mem___wfm_arg_CheckLower_c_len:
    resd 1
__dbase_wfm_mem___string_arg_1_type:
    resd 1
__dbase_wfm_mem___string_arg_1_num:
    resq 1
__dbase_wfm_mem___string_arg_1_ptr:
    resq 1
__dbase_wfm_mem___string_arg_1_len:
    resd 1
__dbase_wfm_mem___string_arg_2_type:
    resd 1
__dbase_wfm_mem___string_arg_2_num:
    resq 1
__dbase_wfm_mem___string_arg_2_ptr:
    resq 1
__dbase_wfm_mem___string_arg_2_len:
    resd 1
__dbase_wfm_mem___string_arg_3_type:
    resd 1
__dbase_wfm_mem___string_arg_3_num:
    resq 1
__dbase_wfm_mem___string_arg_3_ptr:
    resq 1
__dbase_wfm_mem___string_arg_3_len:
    resd 1
__dbase_wfm_mem___string_arg_4_type:
    resd 1
__dbase_wfm_mem___string_arg_4_num:
    resq 1
__dbase_wfm_mem___string_arg_4_ptr:
    resq 1
__dbase_wfm_mem___string_arg_4_len:
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
__dbase_wfm_mem___wfm_text_literal_5_type:
    resd 1
__dbase_wfm_mem___wfm_text_literal_5_num:
    resq 1
__dbase_wfm_mem___wfm_text_literal_5_ptr:
    resq 1
__dbase_wfm_mem___wfm_text_literal_5_len:
    resd 1
__dbase_wfm_mem___wfm_len_6_type:
    resd 1
__dbase_wfm_mem___wfm_len_6_num:
    resq 1
__dbase_wfm_mem___wfm_len_6_ptr:
    resq 1
__dbase_wfm_mem___wfm_len_6_len:
    resd 1
__dbase_wfm_mem___wfm_len_7_type:
    resd 1
__dbase_wfm_mem___wfm_len_7_num:
    resq 1
__dbase_wfm_mem___wfm_len_7_ptr:
    resq 1
__dbase_wfm_mem___wfm_len_7_len:
    resd 1
__dbase_wfm_mem___wfm_ltrim_8_type:
    resd 1
__dbase_wfm_mem___wfm_ltrim_8_num:
    resq 1
__dbase_wfm_mem___wfm_ltrim_8_ptr:
    resq 1
__dbase_wfm_mem___wfm_ltrim_8_len:
    resd 1
__dbase_wfm_mem___wfm_trim_9_type:
    resd 1
__dbase_wfm_mem___wfm_trim_9_num:
    resq 1
__dbase_wfm_mem___wfm_trim_9_ptr:
    resq 1
__dbase_wfm_mem___wfm_trim_9_len:
    resd 1
__dbase_wfm_mem___wfm_trim_10_type:
    resd 1
__dbase_wfm_mem___wfm_trim_10_num:
    resq 1
__dbase_wfm_mem___wfm_trim_10_ptr:
    resq 1
__dbase_wfm_mem___wfm_trim_10_len:
    resd 1
__dbase_wfm_mem___wfm_len_11_type:
    resd 1
__dbase_wfm_mem___wfm_len_11_num:
    resq 1
__dbase_wfm_mem___wfm_len_11_ptr:
    resq 1
__dbase_wfm_mem___wfm_len_11_len:
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
__dbase_wfm_local___dbase_top_level___a_type:
    resd 1
__dbase_wfm_local___dbase_top_level___a_num:
    resq 1
__dbase_wfm_local___dbase_top_level___a_ptr:
    resq 1
__dbase_wfm_local___dbase_top_level___a_len:
    resd 1
__dbase_wfm_local___dbase_top_level___c_type:
    resd 1
__dbase_wfm_local___dbase_top_level___c_num:
    resq 1
__dbase_wfm_local___dbase_top_level___c_ptr:
    resq 1
__dbase_wfm_local___dbase_top_level___c_len:
    resd 1
