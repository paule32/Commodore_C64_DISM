%include "Form1.generated.pe32.extern.inc"
bits 32

global _start
entry _start

section .text

_start:
    push __dbase_format_buffer
    push 0
    push 0
    push 0
    push __dbase_text_0
    call DBaseQtRuntimeStartup
    add esp, 20
    test eax, eax
    jne __dbase_qt_init_ok_2
    push 1
    call ExitProcess
__dbase_qt_init_ok_2:
    push 0
    call DBaseQtSetDebugVisible
    add esp, 4
    call DBaseQtEnsureDefaultMenu
    call DBaseQtShowWindow
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
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
    push 1
    call DBaseQtSetDebugVisible
    add esp, 4
__dbase_output_already_visible_7:
    jmp __dbase_output_done_6
__dbase_output_console_4:
    push 0
    push __dbase_text_1
    call DBaseConsoleWrite
    add esp, 8
__dbase_output_done_6:
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    call DBaseQtMarkProgramFinished
    call DBaseQtExec
    mov dword ptr [__dbase_exit_code], eax
__dbase_program_cleanup_1:
    call DBaseConsoleShutdown
    push __dbase_format_buffer
    call DBaseQtRuntimeShutdown
    add esp, 4
    push dword ptr [__dbase_exit_code]
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
    resd 1
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

; Stage 462: WFM DLL-Runtime-Startup/Shutdown fuer PE32
.section .text
.entry __d64_wfm_entry
__d64_wfm_entry:
    mov eax, __dbase_wfm_qt_output_marker
    push __dbase_format_buffer
    push 1
    push 0
    push 0
    push __dbase_wfm_text_0
    call DBaseQtRuntimeStartup
    add esp, 20
    test eax, eax
    jne __dbase_wfm_runtime_ready
    push 1
    call ExitProcess
__dbase_wfm_runtime_ready:
    call __dbase_wfm_proc___dbase_top_level__
    push 5
    push __dbase_wfm_text_0
    call DBaseQtFormCreate
    add esp, 8
    mov dword ptr [__dbase_wfm_form], eax
    push 0
    push 0
    push dword ptr [__dbase_wfm_form]
    push 10
    push __dbase_wfm_text_1
    call DBaseQtControlCreateEx
    add esp, 20
    mov dword ptr [__dbase_wfm_obj_THIS_PushButton1], eax
    push __dbase_wfm_proc_PushButton1_onClick
    push 7
    push __dbase_wfm_text_2
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtObjectBindEvent
    add esp, 16
    push __dbase_wfm_proc_PushButton1_onGotFocus
    push 10
    push __dbase_wfm_text_3
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtObjectBindEvent
    add esp, 16
    push __dbase_wfm_proc_PushButton1_onLostFocus
    push 11
    push __dbase_wfm_text_4
    push dword ptr [__dbase_wfm_obj_THIS_PushButton1]
    call DBaseQtObjectBindEvent
    add esp, 16
    push 0
    push 0
    push dword ptr [__dbase_wfm_form]
    push 10
    push __dbase_wfm_text_1
    call DBaseQtControlCreateEx
    add esp, 20
    mov dword ptr [__dbase_wfm_obj_THIS_Button1], eax
    push __dbase_wfm_proc_Button1_onLostFocus
    push 11
    push __dbase_wfm_text_4
    push dword ptr [__dbase_wfm_obj_THIS_Button1]
    call DBaseQtObjectBindEvent
    add esp, 16
    push __dbase_wfm_proc_Button1_onGotFocus
    push 10
    push __dbase_wfm_text_3
    push dword ptr [__dbase_wfm_obj_THIS_Button1]
    call DBaseQtObjectBindEvent
    add esp, 16
    push __dbase_wfm_proc_Button1_onClick
    push 7
    push __dbase_wfm_text_2
    push dword ptr [__dbase_wfm_obj_THIS_Button1]
    call DBaseQtObjectBindEvent
    add esp, 16
    push 0
    push 0
    push dword ptr [__dbase_wfm_form]
    push 10
    push __dbase_wfm_text_1
    call DBaseQtControlCreateEx
    add esp, 20
    mov dword ptr [__dbase_wfm_obj_THIS_Button2], eax
    push __dbase_wfm_proc_Button2_onLostFocus
    push 11
    push __dbase_wfm_text_4
    push dword ptr [__dbase_wfm_obj_THIS_Button2]
    call DBaseQtObjectBindEvent
    add esp, 16
    push __dbase_wfm_proc_Button2_onGotFocus
    push 10
    push __dbase_wfm_text_3
    push dword ptr [__dbase_wfm_obj_THIS_Button2]
    call DBaseQtObjectBindEvent
    add esp, 16
    push __dbase_wfm_proc_Button2_onClick
    push 7
    push __dbase_wfm_text_2
    push dword ptr [__dbase_wfm_obj_THIS_Button2]
    call DBaseQtObjectBindEvent
    add esp, 16
; WFM UI payload: binary, zlib, 682 bytes
    push 1
    push 682
    push __dbase_wfm_external_ui_payload
    push 4
    push __dbase_wfm_external_ui_slots
    call DBaseQtFormApplyExternalUi
    add esp, 20
    push 4
    push 51
    call __dbase_wfm_proc___init__
    add esp, 8
    push dword ptr [__dbase_wfm_form]
    call DBaseQtFormOpen
    add esp, 4
    call __dbase_wfm_proc___main__
    call DBaseQtWfmModalParameter
    push eax
    push dword ptr [__dbase_wfm_form]
    call DBaseQtFormRun
    add esp, 8
    call __dbase_wfm_proc___del__
    push __dbase_format_buffer
    call DBaseQtRuntimeShutdown
    add esp, 4
    push 0
    call ExitProcess

; Stage 133: WFM Event-/Methoden-Code
.section .text

; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: __dbase_top_level__
; ------------------------------------------------------------
__dbase_wfm_proc___dbase_top_level__:
    mov dword ptr [__dbase_wfm_local___dbase_top_level___a_type], 0
    mov dword ptr [__dbase_wfm_local___dbase_top_level___a_len], 0
    fldz
    fstp qword ptr [__dbase_wfm_local___dbase_top_level___a_num]
    mov dword ptr [__dbase_wfm_local___dbase_top_level___a_ptr], 0
    mov dword ptr [__dbase_wfm_local___dbase_top_level___c_type], 0
    mov dword ptr [__dbase_wfm_local___dbase_top_level___c_len], 0
    fldz
    fstp qword ptr [__dbase_wfm_local___dbase_top_level___c_num]
    mov dword ptr [__dbase_wfm_local___dbase_top_level___c_ptr], 0
    ; Quellcode Zeile: 37
    ; ? "shell32.dll"
    push 1
    push 11
    push __dbase_wfm_output_text_5
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 39
    fldz
    fstp qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_num]
    mov eax, __dbase_wfm_flow_ffi_ansi_4
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_ptr], eax
    mov eax, __dbase_wfm_flow_ffi_ansi_6
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_ptr], eax
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_ptr], 0
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_ptr], 0
    fld1
    fstp qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_num]
    cmp dword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_type], 4
    je __dbase_wfm_flow_ffi_pointer_10
    fld qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_num]
    fistp dword ptr [__dbase_temp_number]
    push dword ptr [__dbase_temp_number]
    jmp __dbase_wfm_flow_ffi_push_done_11
__dbase_wfm_flow_ffi_pointer_10:
    push dword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_ptr]
__dbase_wfm_flow_ffi_push_done_11:
    push dword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_ptr]
    push dword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_ptr]
    push dword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_ptr]
    push dword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_ptr]
    cmp dword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_type], 4
    je __dbase_wfm_flow_ffi_pointer_12
    fld qword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_num]
    fistp dword ptr [__dbase_temp_number]
    push dword ptr [__dbase_temp_number]
    jmp __dbase_wfm_flow_ffi_push_done_13
__dbase_wfm_flow_ffi_pointer_12:
    push dword ptr [__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_ptr]
__dbase_wfm_flow_ffi_push_done_13:
    call __dbase_ffi_shellexecute
    mov dword ptr [__dbase_ffi_return], eax
    mov dword ptr [__dbase_ffi_return+4], 0
    fild qword ptr [__dbase_ffi_return]
    fstp qword ptr [__dbase_wfm_mem_result_num]
    mov eax, __dbase_wfm_mem_result_type
    mov edx, 1
    call __dbase_wfm_assign_numeric_header
    ; Quellcode Zeile: 41
    ; ? result
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem_result_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 43
    ; local A = 9
    fld qword ptr [__dbase_wfm_numconst_0]
    fstp qword ptr [__dbase_wfm_local___dbase_top_level___a_num]
    mov eax, __dbase_wfm_local___dbase_top_level___a_type
    mov edx, 1
    call __dbase_wfm_assign_numeric_header
    ; Quellcode Zeile: 44
    ; local C = 4
    fld qword ptr [__dbase_wfm_numconst_1]
    fstp qword ptr [__dbase_wfm_local___dbase_top_level___c_num]
    mov eax, __dbase_wfm_local___dbase_top_level___c_type
    mov edx, 1
    call __dbase_wfm_assign_numeric_header
    ; Quellcode Zeile: 47
    ; STORE 123.45 TO xyz
    fld qword ptr [__dbase_wfm_numconst_2]
    fstp qword ptr [__dbase_wfm_mem_xyz_num]
    mov eax, __dbase_wfm_mem_xyz_type
    mov edx, 2
    call __dbase_wfm_assign_numeric_header
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
    mov eax, __dbase_wfm_output_text_6
    jmp __dbase_wfm_flow_type_slot_done_21
__dbase_wfm_flow_type_slot_next_22:
    cmp eax, 67
    jne __dbase_wfm_flow_type_slot_next_23
    mov eax, __dbase_wfm_output_text_7
    jmp __dbase_wfm_flow_type_slot_done_21
__dbase_wfm_flow_type_slot_next_23:
    cmp eax, 79
    jne __dbase_wfm_flow_type_slot_next_24
    mov eax, __dbase_wfm_output_text_8
    jmp __dbase_wfm_flow_type_slot_done_21
__dbase_wfm_flow_type_slot_next_24:
    cmp eax, 76
    jne __dbase_wfm_flow_type_slot_next_25
    mov eax, __dbase_wfm_output_text_9
    jmp __dbase_wfm_flow_type_slot_done_21
__dbase_wfm_flow_type_slot_next_25:
    cmp eax, 68
    jne __dbase_wfm_flow_type_slot_next_26
    mov eax, __dbase_wfm_output_text_10
    jmp __dbase_wfm_flow_type_slot_done_21
__dbase_wfm_flow_type_slot_next_26:
    mov eax, __dbase_wfm_output_text_11
__dbase_wfm_flow_type_slot_done_21:
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_14_ptr], eax
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_14_len], 1
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_14_type], 3
    ; ? TYPE("xyz")
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem___dbase_wfm_flow_type_print_14_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
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
    mov eax, __dbase_wfm_output_text_12
    jmp __dbase_wfm_flow_type_slot_done_34
__dbase_wfm_flow_type_slot_next_35:
    cmp eax, 67
    jne __dbase_wfm_flow_type_slot_next_36
    mov eax, __dbase_wfm_output_text_13
    jmp __dbase_wfm_flow_type_slot_done_34
__dbase_wfm_flow_type_slot_next_36:
    cmp eax, 79
    jne __dbase_wfm_flow_type_slot_next_37
    mov eax, __dbase_wfm_output_text_14
    jmp __dbase_wfm_flow_type_slot_done_34
__dbase_wfm_flow_type_slot_next_37:
    cmp eax, 76
    jne __dbase_wfm_flow_type_slot_next_38
    mov eax, __dbase_wfm_output_text_15
    jmp __dbase_wfm_flow_type_slot_done_34
__dbase_wfm_flow_type_slot_next_38:
    cmp eax, 68
    jne __dbase_wfm_flow_type_slot_next_39
    mov eax, __dbase_wfm_output_text_16
    jmp __dbase_wfm_flow_type_slot_done_34
__dbase_wfm_flow_type_slot_next_39:
    mov eax, __dbase_wfm_output_text_17
__dbase_wfm_flow_type_slot_done_34:
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_27_ptr], eax
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_27_len], 1
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_27_type], 3
    ; ? VARTYPE(xyz)
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem___dbase_wfm_flow_type_print_27_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
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
    push eax
    mov eax, 78
    pop ecx
    cmp ecx, eax
    jne __dbase_wfm_flow_if_false_40
    ; Quellcode Zeile: 53
    ; ? "xyz ist numerisch"
    push 1
    push 17
    push __dbase_wfm_output_text_18
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 54
__dbase_wfm_flow_if_false_40:
__dbase_wfm_flow_if_end_41:
    ; Quellcode Zeile: 56
    ; STORE "Hallo" TO xyz
    mov dword ptr [__dbase_wfm_mem_xyz_ptr], __dbase_wfm_output_text_19
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
    mov eax, __dbase_wfm_output_text_20
    jmp __dbase_wfm_flow_type_slot_done_55
__dbase_wfm_flow_type_slot_next_56:
    cmp eax, 67
    jne __dbase_wfm_flow_type_slot_next_57
    mov eax, __dbase_wfm_output_text_21
    jmp __dbase_wfm_flow_type_slot_done_55
__dbase_wfm_flow_type_slot_next_57:
    cmp eax, 79
    jne __dbase_wfm_flow_type_slot_next_58
    mov eax, __dbase_wfm_output_text_22
    jmp __dbase_wfm_flow_type_slot_done_55
__dbase_wfm_flow_type_slot_next_58:
    cmp eax, 76
    jne __dbase_wfm_flow_type_slot_next_59
    mov eax, __dbase_wfm_output_text_23
    jmp __dbase_wfm_flow_type_slot_done_55
__dbase_wfm_flow_type_slot_next_59:
    cmp eax, 68
    jne __dbase_wfm_flow_type_slot_next_60
    mov eax, __dbase_wfm_output_text_24
    jmp __dbase_wfm_flow_type_slot_done_55
__dbase_wfm_flow_type_slot_next_60:
    mov eax, __dbase_wfm_output_text_25
__dbase_wfm_flow_type_slot_done_55:
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_48_ptr], eax
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_48_len], 1
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_48_type], 3
    ; ? TYPE("xyz")
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem___dbase_wfm_flow_type_print_48_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
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
    mov eax, __dbase_wfm_output_text_26
    jmp __dbase_wfm_flow_type_slot_done_68
__dbase_wfm_flow_type_slot_next_69:
    cmp eax, 67
    jne __dbase_wfm_flow_type_slot_next_70
    mov eax, __dbase_wfm_output_text_27
    jmp __dbase_wfm_flow_type_slot_done_68
__dbase_wfm_flow_type_slot_next_70:
    cmp eax, 79
    jne __dbase_wfm_flow_type_slot_next_71
    mov eax, __dbase_wfm_output_text_28
    jmp __dbase_wfm_flow_type_slot_done_68
__dbase_wfm_flow_type_slot_next_71:
    cmp eax, 76
    jne __dbase_wfm_flow_type_slot_next_72
    mov eax, __dbase_wfm_output_text_29
    jmp __dbase_wfm_flow_type_slot_done_68
__dbase_wfm_flow_type_slot_next_72:
    cmp eax, 68
    jne __dbase_wfm_flow_type_slot_next_73
    mov eax, __dbase_wfm_output_text_30
    jmp __dbase_wfm_flow_type_slot_done_68
__dbase_wfm_flow_type_slot_next_73:
    mov eax, __dbase_wfm_output_text_31
__dbase_wfm_flow_type_slot_done_68:
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_61_ptr], eax
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_61_len], 1
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_61_type], 3
    ; ? VARTYPE(xyz)
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem___dbase_wfm_flow_type_print_61_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 61
    mov eax, 85
    cmp eax, 78
    jne __dbase_wfm_flow_type_slot_next_76
    mov eax, __dbase_wfm_output_text_32
    jmp __dbase_wfm_flow_type_slot_done_75
__dbase_wfm_flow_type_slot_next_76:
    cmp eax, 67
    jne __dbase_wfm_flow_type_slot_next_77
    mov eax, __dbase_wfm_output_text_33
    jmp __dbase_wfm_flow_type_slot_done_75
__dbase_wfm_flow_type_slot_next_77:
    cmp eax, 79
    jne __dbase_wfm_flow_type_slot_next_78
    mov eax, __dbase_wfm_output_text_34
    jmp __dbase_wfm_flow_type_slot_done_75
__dbase_wfm_flow_type_slot_next_78:
    cmp eax, 76
    jne __dbase_wfm_flow_type_slot_next_79
    mov eax, __dbase_wfm_output_text_35
    jmp __dbase_wfm_flow_type_slot_done_75
__dbase_wfm_flow_type_slot_next_79:
    cmp eax, 68
    jne __dbase_wfm_flow_type_slot_next_80
    mov eax, __dbase_wfm_output_text_36
    jmp __dbase_wfm_flow_type_slot_done_75
__dbase_wfm_flow_type_slot_next_80:
    mov eax, __dbase_wfm_output_text_37
__dbase_wfm_flow_type_slot_done_75:
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_74_ptr], eax
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_74_len], 1
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_74_type], 3
    ; ? TYPE("unbekannt")
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem___dbase_wfm_flow_type_print_74_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
__dbase_wfm_flow_method_exit_1:
    ret
; END WFM PROCEDURE/FUNCTION: __dbase_top_level__


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: __del__
; ------------------------------------------------------------
__dbase_wfm_proc___del__:
    ; Quellcode Zeile: 427
__dbase_wfm_flow_method_exit_81:
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
    ; Quellcode Zeile: 418
    ; ? "p1 = " + int(p1)
    push 0
    push 5
    push __dbase_wfm_output_text_38
    call DBaseQtConsoleWrite
    add esp, 12
    push 1
    push 2
    push __dbase_wfm_output_text_39
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 419
    ; ? "p2 = " + int(p2)
    push 0
    push 5
    push __dbase_wfm_output_text_40
    call DBaseQtConsoleWrite
    add esp, 12
    push 1
    push 1
    push __dbase_wfm_output_text_41
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 421
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
    mov eax, __dbase_wfm_output_text_42
    jmp __dbase_wfm_flow_type_slot_done_90
__dbase_wfm_flow_type_slot_next_91:
    cmp eax, 67
    jne __dbase_wfm_flow_type_slot_next_92
    mov eax, __dbase_wfm_output_text_43
    jmp __dbase_wfm_flow_type_slot_done_90
__dbase_wfm_flow_type_slot_next_92:
    cmp eax, 79
    jne __dbase_wfm_flow_type_slot_next_93
    mov eax, __dbase_wfm_output_text_44
    jmp __dbase_wfm_flow_type_slot_done_90
__dbase_wfm_flow_type_slot_next_93:
    cmp eax, 76
    jne __dbase_wfm_flow_type_slot_next_94
    mov eax, __dbase_wfm_output_text_45
    jmp __dbase_wfm_flow_type_slot_done_90
__dbase_wfm_flow_type_slot_next_94:
    cmp eax, 68
    jne __dbase_wfm_flow_type_slot_next_95
    mov eax, __dbase_wfm_output_text_46
    jmp __dbase_wfm_flow_type_slot_done_90
__dbase_wfm_flow_type_slot_next_95:
    mov eax, __dbase_wfm_output_text_47
__dbase_wfm_flow_type_slot_done_90:
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_83_ptr], eax
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_83_len], 1
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_83_type], 3
    ; ? TYPE("xyz")
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem___dbase_wfm_flow_type_print_83_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 422
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
    mov eax, __dbase_wfm_output_text_48
    jmp __dbase_wfm_flow_type_slot_done_103
__dbase_wfm_flow_type_slot_next_104:
    cmp eax, 67
    jne __dbase_wfm_flow_type_slot_next_105
    mov eax, __dbase_wfm_output_text_49
    jmp __dbase_wfm_flow_type_slot_done_103
__dbase_wfm_flow_type_slot_next_105:
    cmp eax, 79
    jne __dbase_wfm_flow_type_slot_next_106
    mov eax, __dbase_wfm_output_text_50
    jmp __dbase_wfm_flow_type_slot_done_103
__dbase_wfm_flow_type_slot_next_106:
    cmp eax, 76
    jne __dbase_wfm_flow_type_slot_next_107
    mov eax, __dbase_wfm_output_text_51
    jmp __dbase_wfm_flow_type_slot_done_103
__dbase_wfm_flow_type_slot_next_107:
    cmp eax, 68
    jne __dbase_wfm_flow_type_slot_next_108
    mov eax, __dbase_wfm_output_text_52
    jmp __dbase_wfm_flow_type_slot_done_103
__dbase_wfm_flow_type_slot_next_108:
    mov eax, __dbase_wfm_output_text_53
__dbase_wfm_flow_type_slot_done_103:
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_96_ptr], eax
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_96_len], 1
    mov dword ptr [__dbase_wfm_mem___dbase_wfm_flow_type_print_96_type], 3
    ; ? VARTYPE(xyz)
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem___dbase_wfm_flow_type_print_96_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 424
__dbase_wfm_flow_method_exit_82:
    ret
; END WFM PROCEDURE/FUNCTION: __init__


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: __main__
; ------------------------------------------------------------
__dbase_wfm_proc___main__:
    ; Quellcode Zeile: 430
    mov eax, 7
__dbase_wfm_flow_method_exit_109:
    ret
; END WFM PROCEDURE/FUNCTION: __main__


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: Button1_onClick
; ------------------------------------------------------------
__dbase_wfm_proc_Button1_onClick:
    mov eax, dword ptr [esp+4]
    mov dword ptr [__dbase_wfm_param_Button1_onClick_Sender], eax
    ; Quellcode Zeile: 542
    ; ? "Button 1 on Click"
    push 1
    push 17
    push __dbase_wfm_output_text_54
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 543
__dbase_wfm_flow_method_exit_110:
    ret
; END WFM PROCEDURE/FUNCTION: Button1_onClick


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: Button1_onGotFocus
; ------------------------------------------------------------
__dbase_wfm_proc_Button1_onGotFocus:
    mov eax, dword ptr [esp+4]
    mov dword ptr [__dbase_wfm_param_Button1_onGotFocus_Sender], eax
    ; Quellcode Zeile: 530
    ; ? "Button 1 on Got Focus"
    push 1
    push 21
    push __dbase_wfm_output_text_55
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 531
__dbase_wfm_flow_method_exit_111:
    ret
; END WFM PROCEDURE/FUNCTION: Button1_onGotFocus


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: Button1_onLostFocus
; ------------------------------------------------------------
__dbase_wfm_proc_Button1_onLostFocus:
    mov eax, dword ptr [esp+4]
    mov dword ptr [__dbase_wfm_param_Button1_onLostFocus_Sender], eax
    ; Quellcode Zeile: 526
    ; ? "Button 1 on Lost Focus"
    push 1
    push 22
    push __dbase_wfm_output_text_56
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 527
__dbase_wfm_flow_method_exit_112:
    ret
; END WFM PROCEDURE/FUNCTION: Button1_onLostFocus


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: Button2_onClick
; ------------------------------------------------------------
__dbase_wfm_proc_Button2_onClick:
    mov eax, dword ptr [esp+4]
    mov dword ptr [__dbase_wfm_param_Button2_onClick_Sender], eax
    ; Quellcode Zeile: 546
    ; ? "Button 2 onClick"
    push 1
    push 16
    push __dbase_wfm_output_text_57
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 547
__dbase_wfm_flow_method_exit_113:
    ret
; END WFM PROCEDURE/FUNCTION: Button2_onClick


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: Button2_onGotFocus
; ------------------------------------------------------------
__dbase_wfm_proc_Button2_onGotFocus:
    mov eax, dword ptr [esp+4]
    mov dword ptr [__dbase_wfm_param_Button2_onGotFocus_Sender], eax
    ; Quellcode Zeile: 538
    ; ? "Button 2 got focus on Button"
    push 1
    push 28
    push __dbase_wfm_output_text_58
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 539
__dbase_wfm_flow_method_exit_114:
    ret
; END WFM PROCEDURE/FUNCTION: Button2_onGotFocus


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: Button2_onLostFocus
; ------------------------------------------------------------
__dbase_wfm_proc_Button2_onLostFocus:
    mov eax, dword ptr [esp+4]
    mov dword ptr [__dbase_wfm_param_Button2_onLostFocus_Sender], eax
    ; Quellcode Zeile: 534
    ; ? "Button 2 on lost focus"
    push 1
    push 22
    push __dbase_wfm_output_text_59
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 535
__dbase_wfm_flow_method_exit_115:
    ret
; END WFM PROCEDURE/FUNCTION: Button2_onLostFocus


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: CheckLower
; ------------------------------------------------------------
__dbase_wfm_proc_CheckLower:
    mov eax, dword ptr [esp+4]
    mov dword ptr [__dbase_wfm_param_CheckLower_c], eax
    mov dword ptr [__dbase_wfm_mem___wfm_arg_CheckLower_c_type], 3
    mov eax, dword ptr [__dbase_wfm_param_CheckLower_c]
    mov dword ptr [__dbase_wfm_mem___wfm_arg_CheckLower_c_ptr], eax
    mov eax, dword ptr [esp+8]
    mov dword ptr [__dbase_wfm_mem___wfm_arg_CheckLower_c_len], eax
    ; Quellcode Zeile: 515
    cmp dword ptr [__dbase_wfm_mem___wfm_arg_CheckLower_c_type], 3
    je __dbase_wfm_flow_char_case_valid_117
    fldz
    jmp __dbase_wfm_flow_char_case_end_118
__dbase_wfm_flow_char_case_valid_117:
    push dword ptr [__dbase_wfm_mem___wfm_arg_CheckLower_c_len]
    push dword ptr [__dbase_wfm_mem___wfm_arg_CheckLower_c_ptr]
    call DBaseCharIsLowerUtf8
    add esp, 8
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
__dbase_wfm_flow_char_case_end_118:
    fistp dword ptr [__dbase_temp_number]
    mov eax, dword ptr [__dbase_temp_number]
__dbase_wfm_flow_method_exit_116:
    ret
; END WFM PROCEDURE/FUNCTION: CheckLower


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: PushButton1_onClick
; ------------------------------------------------------------
__dbase_wfm_proc_PushButton1_onClick:
    mov eax, dword ptr [esp+4]
    mov dword ptr [__dbase_wfm_param_PushButton1_onClick_Sender], eax
    ; Quellcode Zeile: 447
    ; STORE 101.42 TO Ausdruck
    fld qword ptr [__dbase_wfm_numconst_3]
    fstp qword ptr [__dbase_wfm_mem_Ausdruck_num]
    mov eax, __dbase_wfm_mem_Ausdruck_type
    mov edx, 2
    call __dbase_wfm_assign_numeric_header
    ; Quellcode Zeile: 448
    ; Ausdruck = 101.42
    fld qword ptr [__dbase_wfm_numconst_3]
    fstp qword ptr [__dbase_wfm_mem_Ausdruck_num]
    mov eax, __dbase_wfm_mem_Ausdruck_type
    mov edx, 2
    call __dbase_wfm_assign_numeric_header
    ; Quellcode Zeile: 449
    ; ? Ausdruck
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem_Ausdruck_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 450
    ; STORE INT(Ausdruck) TO Ausdruck
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 1
    je __dbase_wfm_int_numeric_0
    cmp dword ptr [__dbase_wfm_mem_Ausdruck_type], 2
    je __dbase_wfm_int_numeric_0
    mov eax, __dbase_wfm_mem_Ausdruck_type
    mov edx, 0
    call __dbase_wfm_assign_numeric_header
    jmp __dbase_wfm_int_done_0
__dbase_wfm_int_numeric_0:
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
__dbase_wfm_int_done_0:
    ; Quellcode Zeile: 451
    ; ? Ausdruck
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem_Ausdruck_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 452
    ; ? "1: " + 101.42
    push 0
    push 3
    push __dbase_wfm_output_text_60
    call DBaseQtConsoleWrite
    add esp, 12
    push 1
    push 6
    push __dbase_wfm_output_text_61
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 453
    ; ? "2: " + INT(101.42)
    push 0
    push 3
    push __dbase_wfm_output_text_62
    call DBaseQtConsoleWrite
    add esp, 12
    push 1
    push 3
    push __dbase_wfm_output_text_63
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 454
    ; ? "3: " + Ausdruck
    push 0
    push 3
    push __dbase_wfm_output_text_64
    call DBaseQtConsoleWrite
    add esp, 12
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem_Ausdruck_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 455
    ; STORE "Zeichenstring" TO SpeicherVar
    mov dword ptr [__dbase_wfm_mem_SpeicherVar_ptr], __dbase_wfm_output_text_65
    mov dword ptr [__dbase_wfm_mem_SpeicherVar_len], 13
    mov dword ptr [__dbase_wfm_mem_SpeicherVar_type], 3
    ; Quellcode Zeile: 456
    ; ? "4: " + SpeicherVar
    push 0
    push 3
    push __dbase_wfm_output_text_66
    call DBaseQtConsoleWrite
    add esp, 12
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem_SpeicherVar_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 457
    cmp dword ptr [__dbase_wfm_mem_SpeicherVar_type], 3
    je __wfm_upper_1_valid
    push 13
    call ExitProcess
__wfm_upper_1_valid:
    fld qword ptr [__dbase_wfm_numconst_4]
    fstp qword ptr [__dbase_wfm_mem___string_arg_2_num]
    mov eax, __dbase_wfm_mem___string_arg_2_type
    mov edx, 2
    call __dbase_wfm_assign_numeric_header
    fld qword ptr [__dbase_wfm_numconst_5]
    fstp qword ptr [__dbase_wfm_mem___string_arg_3_num]
    mov eax, __dbase_wfm_mem___string_arg_3_type
    mov edx, 2
    call __dbase_wfm_assign_numeric_header
    mov eax, dword ptr [__dbase_wfm_mem_SpeicherVar_len]
    mov ecx, eax
    add eax, ecx
    add eax, ecx
    add eax, 1
    push eax
    call __dbase_malloc
    add esp, 4
    test eax, eax
    jne __wfm_upper_4_allocated
    push 8
    call ExitProcess
__wfm_upper_4_allocated:
    mov dword ptr [__dbase_wfm_mem___string_arg_4_ptr], eax
    mov eax, dword ptr [__dbase_wfm_mem_SpeicherVar_len]
    mov ecx, eax
    add eax, ecx
    add eax, ecx
    add eax, 1
    push __dbase_wfm_mem___string_arg_3_num
    push __dbase_wfm_mem___string_arg_2_num
    push dword ptr [__dbase_wfm_mem_SpeicherVar_len]
    push dword ptr [__dbase_wfm_mem_SpeicherVar_ptr]
    push eax
    push dword ptr [__dbase_wfm_mem___string_arg_4_ptr]
    call DBaseUtf8SubstringUpper
    add esp, 24
    cmp eax, -1
    jne __wfm_upper_4_converted
    push 13
    call ExitProcess
__wfm_upper_4_converted:
    mov dword ptr [__dbase_wfm_mem___string_arg_4_len], eax
    mov dword ptr [__dbase_wfm_mem___string_arg_4_type], 3
    ; ? "5: " + !($(SpeicherVar, 8, 6))
    push 0
    push 3
    push __dbase_wfm_output_text_67
    call DBaseQtConsoleWrite
    add esp, 12
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem___string_arg_4_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 458
    ; TestAndNotXor()
    call __dbase_wfm_proc_TestAndNotXor
    ; Quellcode Zeile: 460
    push 19
    call GetSystemMetrics
    test eax, eax
    setne al
    movzx eax, al
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fstp qword ptr [__dbase_wfm_mem_HatMaus_num]
    mov eax, __dbase_wfm_mem_HatMaus_type
    mov edx, 1
    call __dbase_wfm_assign_numeric_header
    ; Quellcode Zeile: 461
    ; IF HatMaus = 1
    fld qword ptr [__dbase_wfm_mem_HatMaus_num]
    fld1
    fucomip st0, st1
    fstp st0
    jne __dbase_wfm_flow_if_false_121
    ; Quellcode Zeile: 462
    ; ? "Eine Maus ist vorhanden."
    push 1
    push 24
    push __dbase_wfm_output_text_68
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 463
    jmp __dbase_wfm_flow_if_end_122
__dbase_wfm_flow_if_false_121:
    ; Quellcode Zeile: 464
    ; ? "Keine Maus erkannt."
    push 1
    push 19
    push __dbase_wfm_output_text_69
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 465
__dbase_wfm_flow_if_end_122:
    ; Quellcode Zeile: 466
    ; IF ismouse() .AND. HatMaus = 1
    push 19
    call GetSystemMetrics
    test eax, eax
    setne al
    movzx eax, al
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fldz
    fucomip st0, st1
    fstp st0
    je __dbase_wfm_flow_if_false_123
    fld qword ptr [__dbase_wfm_mem_HatMaus_num]
    fld1
    fucomip st0, st1
    fstp st0
    jne __dbase_wfm_flow_if_false_123
    ; Quellcode Zeile: 467
    ; ? "Maus kann verwendet werden."
    push 1
    push 27
    push __dbase_wfm_output_text_70
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 468
__dbase_wfm_flow_if_false_123:
__dbase_wfm_flow_if_end_124:
    ; Quellcode Zeile: 469
    push 19
    call GetSystemMetrics
    test eax, eax
    setne al
    movzx eax, al
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fstp qword ptr [__dbase_wfm_mem___wfm_ismouse_print_num]
    ; ? ismouse()
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem___wfm_ismouse_print_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 472
    sub esp, 12
    mov dword ptr [esp], 0
    mov dword ptr [esp+4], 0
    mov dword ptr [esp+8], 0
    lea eax, [esp]
    push 8
    push eax
    push 0
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_125_done
    mov edx, dword ptr [esp]
    test edx, edx
    jz __dbase_wfm_flow_iskeyboard_125_done
    cmp edx, 536870911
    ja __dbase_wfm_flow_iskeyboard_125_done
    shl edx, 3
    push 4
    push 12288
    push edx
    push 0
    call VirtualAlloc
    test eax, eax
    jz __dbase_wfm_flow_iskeyboard_125_done
    mov dword ptr [esp+4], eax
    lea edx, [esp]
    push 8
    push edx
    push eax
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_125_release
    test eax, eax
    jz __dbase_wfm_flow_iskeyboard_125_release
    mov ecx, eax
    mov edx, dword ptr [esp+4]
__dbase_wfm_flow_iskeyboard_125_scan:
    cmp dword ptr [edx+4], 1
    je __dbase_wfm_flow_iskeyboard_125_present
    add edx, 8
    dec ecx
    jnz __dbase_wfm_flow_iskeyboard_125_scan
    jmp __dbase_wfm_flow_iskeyboard_125_release
__dbase_wfm_flow_iskeyboard_125_present:
    mov dword ptr [esp+8], 1
__dbase_wfm_flow_iskeyboard_125_release:
    mov eax, dword ptr [esp+4]
    push 32768
    push 0
    push eax
    call VirtualFree
__dbase_wfm_flow_iskeyboard_125_done:
    mov eax, dword ptr [esp+8]
    add esp, 12
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fstp qword ptr [__dbase_wfm_mem_HatTastatur_num]
    mov eax, __dbase_wfm_mem_HatTastatur_type
    mov edx, 1
    call __dbase_wfm_assign_numeric_header
    ; Quellcode Zeile: 473
    ; IF HatTastatur = 1
    fld qword ptr [__dbase_wfm_mem_HatTastatur_num]
    fld1
    fucomip st0, st1
    fstp st0
    jne __dbase_wfm_flow_if_false_126
    ; Quellcode Zeile: 474
    ; ? "Eine Tastatur ist vorhanden."
    push 1
    push 28
    push __dbase_wfm_output_text_71
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 475
    jmp __dbase_wfm_flow_if_end_127
__dbase_wfm_flow_if_false_126:
    ; Quellcode Zeile: 476
    ; ? "Keine Tastatur erkannt."
    push 1
    push 23
    push __dbase_wfm_output_text_72
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 477
__dbase_wfm_flow_if_end_127:
    ; Quellcode Zeile: 478
    ; IF iskeyboard() .AND. ismouse()
    sub esp, 12
    mov dword ptr [esp], 0
    mov dword ptr [esp+4], 0
    mov dword ptr [esp+8], 0
    lea eax, [esp]
    push 8
    push eax
    push 0
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_130_done
    mov edx, dword ptr [esp]
    test edx, edx
    jz __dbase_wfm_flow_iskeyboard_130_done
    cmp edx, 536870911
    ja __dbase_wfm_flow_iskeyboard_130_done
    shl edx, 3
    push 4
    push 12288
    push edx
    push 0
    call VirtualAlloc
    test eax, eax
    jz __dbase_wfm_flow_iskeyboard_130_done
    mov dword ptr [esp+4], eax
    lea edx, [esp]
    push 8
    push edx
    push eax
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_130_release
    test eax, eax
    jz __dbase_wfm_flow_iskeyboard_130_release
    mov ecx, eax
    mov edx, dword ptr [esp+4]
__dbase_wfm_flow_iskeyboard_130_scan:
    cmp dword ptr [edx+4], 1
    je __dbase_wfm_flow_iskeyboard_130_present
    add edx, 8
    dec ecx
    jnz __dbase_wfm_flow_iskeyboard_130_scan
    jmp __dbase_wfm_flow_iskeyboard_130_release
__dbase_wfm_flow_iskeyboard_130_present:
    mov dword ptr [esp+8], 1
__dbase_wfm_flow_iskeyboard_130_release:
    mov eax, dword ptr [esp+4]
    push 32768
    push 0
    push eax
    call VirtualFree
__dbase_wfm_flow_iskeyboard_130_done:
    mov eax, dword ptr [esp+8]
    add esp, 12
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fldz
    fucomip st0, st1
    fstp st0
    je __dbase_wfm_flow_if_false_128
    push 19
    call GetSystemMetrics
    test eax, eax
    setne al
    movzx eax, al
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fldz
    fucomip st0, st1
    fstp st0
    je __dbase_wfm_flow_if_false_128
    ; Quellcode Zeile: 479
    ; ? "Maus und Tastatur sind vorhanden."
    push 1
    push 33
    push __dbase_wfm_output_text_73
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 480
__dbase_wfm_flow_if_false_128:
__dbase_wfm_flow_if_end_129:
    ; Quellcode Zeile: 481
    ; IF .NOT. iskeyboard()
    sub esp, 12
    mov dword ptr [esp], 0
    mov dword ptr [esp+4], 0
    mov dword ptr [esp+8], 0
    lea eax, [esp]
    push 8
    push eax
    push 0
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_134_done
    mov edx, dword ptr [esp]
    test edx, edx
    jz __dbase_wfm_flow_iskeyboard_134_done
    cmp edx, 536870911
    ja __dbase_wfm_flow_iskeyboard_134_done
    shl edx, 3
    push 4
    push 12288
    push edx
    push 0
    call VirtualAlloc
    test eax, eax
    jz __dbase_wfm_flow_iskeyboard_134_done
    mov dword ptr [esp+4], eax
    lea edx, [esp]
    push 8
    push edx
    push eax
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_134_release
    test eax, eax
    jz __dbase_wfm_flow_iskeyboard_134_release
    mov ecx, eax
    mov edx, dword ptr [esp+4]
__dbase_wfm_flow_iskeyboard_134_scan:
    cmp dword ptr [edx+4], 1
    je __dbase_wfm_flow_iskeyboard_134_present
    add edx, 8
    dec ecx
    jnz __dbase_wfm_flow_iskeyboard_134_scan
    jmp __dbase_wfm_flow_iskeyboard_134_release
__dbase_wfm_flow_iskeyboard_134_present:
    mov dword ptr [esp+8], 1
__dbase_wfm_flow_iskeyboard_134_release:
    mov eax, dword ptr [esp+4]
    push 32768
    push 0
    push eax
    call VirtualFree
__dbase_wfm_flow_iskeyboard_134_done:
    mov eax, dword ptr [esp+8]
    add esp, 12
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fldz
    fucomip st0, st1
    fstp st0
    jne __dbase_wfm_flow_if_false_131
__dbase_wfm_flow_not_true_133:
    ; Quellcode Zeile: 482
    ; ? "Keine Tastatur gefunden."
    push 1
    push 24
    push __dbase_wfm_output_text_74
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 483
__dbase_wfm_flow_if_false_131:
__dbase_wfm_flow_if_end_132:
    ; Quellcode Zeile: 484
    sub esp, 12
    mov dword ptr [esp], 0
    mov dword ptr [esp+4], 0
    mov dword ptr [esp+8], 0
    lea eax, [esp]
    push 8
    push eax
    push 0
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_135_done
    mov edx, dword ptr [esp]
    test edx, edx
    jz __dbase_wfm_flow_iskeyboard_135_done
    cmp edx, 536870911
    ja __dbase_wfm_flow_iskeyboard_135_done
    shl edx, 3
    push 4
    push 12288
    push edx
    push 0
    call VirtualAlloc
    test eax, eax
    jz __dbase_wfm_flow_iskeyboard_135_done
    mov dword ptr [esp+4], eax
    lea edx, [esp]
    push 8
    push edx
    push eax
    call GetRawInputDeviceList
    cmp eax, 4294967295
    je __dbase_wfm_flow_iskeyboard_135_release
    test eax, eax
    jz __dbase_wfm_flow_iskeyboard_135_release
    mov ecx, eax
    mov edx, dword ptr [esp+4]
__dbase_wfm_flow_iskeyboard_135_scan:
    cmp dword ptr [edx+4], 1
    je __dbase_wfm_flow_iskeyboard_135_present
    add edx, 8
    dec ecx
    jnz __dbase_wfm_flow_iskeyboard_135_scan
    jmp __dbase_wfm_flow_iskeyboard_135_release
__dbase_wfm_flow_iskeyboard_135_present:
    mov dword ptr [esp+8], 1
__dbase_wfm_flow_iskeyboard_135_release:
    mov eax, dword ptr [esp+4]
    push 32768
    push 0
    push eax
    call VirtualFree
__dbase_wfm_flow_iskeyboard_135_done:
    mov eax, dword ptr [esp+8]
    add esp, 12
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fstp qword ptr [__dbase_wfm_mem___wfm_iskeyboard_print_num]
    ; ? iskeyboard()
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem___wfm_iskeyboard_print_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 487
    ; STORE 'A' TO Zeichen
    mov dword ptr [__dbase_wfm_mem_Zeichen_ptr], __dbase_wfm_output_text_75
    mov dword ptr [__dbase_wfm_mem_Zeichen_len], 1
    mov dword ptr [__dbase_wfm_mem_Zeichen_type], 3
    ; Quellcode Zeile: 488
    ; IF ISUPPER(Zeichen)
    cmp dword ptr [__dbase_wfm_mem_Zeichen_type], 3
    je __dbase_wfm_flow_char_case_valid_138
    fldz
    jmp __dbase_wfm_flow_char_case_end_139
__dbase_wfm_flow_char_case_valid_138:
    push dword ptr [__dbase_wfm_mem_Zeichen_len]
    push dword ptr [__dbase_wfm_mem_Zeichen_ptr]
    call DBaseCharIsUpperUtf8
    add esp, 8
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
__dbase_wfm_flow_char_case_end_139:
    fldz
    fucomip st0, st1
    fstp st0
    je __dbase_wfm_flow_if_false_136
    ; Quellcode Zeile: 489
    ; ? "Grossbuchstabe erkannt"
    push 1
    push 22
    push __dbase_wfm_output_text_76
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 490
__dbase_wfm_flow_if_false_136:
__dbase_wfm_flow_if_end_137:
    ; Quellcode Zeile: 491
    ; IF CheckLower('z')
    push 1
    push __dbase_wfm_text_77
    call __dbase_wfm_proc_CheckLower
    add esp, 8
    mov dword ptr [__dbase_temp_number], eax
    fild dword ptr [__dbase_temp_number]
    fldz
    fucomip st0, st1
    fstp st0
    je __dbase_wfm_flow_if_false_141
    ; Quellcode Zeile: 492
    ; ? "Kleinbuchstabe erkannt"
    push 1
    push 22
    push __dbase_wfm_output_text_78
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 493
__dbase_wfm_flow_if_false_141:
__dbase_wfm_flow_if_end_142:
    ; Quellcode Zeile: 495
    mov dword ptr [__dbase_wfm_mem___wfm_text_literal_5_ptr], __dbase_wfm_output_text_79
    mov dword ptr [__dbase_wfm_mem___wfm_text_literal_5_len], 10
    mov dword ptr [__dbase_wfm_mem___wfm_text_literal_5_type], 3
    cmp dword ptr [__dbase_wfm_mem___wfm_text_literal_5_type], 3
    je __dbase_wfm_flow_len_valid_143
    xor ecx, ecx
    jmp __dbase_wfm_flow_len_skip_146
__dbase_wfm_flow_len_valid_143:
    push esi
    mov esi, dword ptr [__dbase_wfm_mem___wfm_text_literal_5_ptr]
    mov edx, dword ptr [__dbase_wfm_mem___wfm_text_literal_5_len]
    xor ecx, ecx
__dbase_wfm_flow_len_loop_145:
    test esi, esi
    je __dbase_wfm_flow_len_finish_147
    test edx, edx
    jz __dbase_wfm_flow_len_finish_147
    movzx eax, byte ptr [esi]
    and eax, 192
    cmp eax, 128
    je len___dbase_wfm_flow_len_loop_145_continuation
    inc ecx
len___dbase_wfm_flow_len_loop_145_continuation:
    inc esi
    dec edx
    jmp __dbase_wfm_flow_len_loop_145
__dbase_wfm_flow_len_finish_147:
    pop esi
__dbase_wfm_flow_len_skip_146:
    mov dword ptr [__dbase_temp_number], ecx
    fild dword ptr [__dbase_temp_number]
    fstp qword ptr [__dbase_wfm_mem___wfm_len_6_num]
    ; ? LEN("Ein String")
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem___wfm_len_6_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 498
    ; STORE "   Hallo Welt   " TO Text
    mov dword ptr [__dbase_wfm_mem_Text_ptr], __dbase_wfm_output_text_80
    mov dword ptr [__dbase_wfm_mem_Text_len], 16
    mov dword ptr [__dbase_wfm_mem_Text_type], 3
    ; Quellcode Zeile: 500
    cmp dword ptr [__dbase_wfm_mem_Text_type], 3
    je __dbase_wfm_flow_len_valid_148
    xor ecx, ecx
    jmp __dbase_wfm_flow_len_skip_151
__dbase_wfm_flow_len_valid_148:
    push esi
    mov esi, dword ptr [__dbase_wfm_mem_Text_ptr]
    mov edx, dword ptr [__dbase_wfm_mem_Text_len]
    xor ecx, ecx
__dbase_wfm_flow_len_loop_150:
    test esi, esi
    je __dbase_wfm_flow_len_finish_152
    test edx, edx
    jz __dbase_wfm_flow_len_finish_152
    movzx eax, byte ptr [esi]
    and eax, 192
    cmp eax, 128
    je len___dbase_wfm_flow_len_loop_150_continuation
    inc ecx
len___dbase_wfm_flow_len_loop_150_continuation:
    inc esi
    dec edx
    jmp __dbase_wfm_flow_len_loop_150
__dbase_wfm_flow_len_finish_152:
    pop esi
__dbase_wfm_flow_len_skip_151:
    mov dword ptr [__dbase_temp_number], ecx
    fild dword ptr [__dbase_temp_number]
    fstp qword ptr [__dbase_wfm_mem___wfm_len_7_num]
    ; ? LEN(Text)
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem___wfm_len_7_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 503
    cmp dword ptr [__dbase_wfm_mem_Text_type], 3
    je __dbase_wfm_flow_ltrim_valid_153
    mov dword ptr [__dbase_wfm_mem___wfm_ltrim_8_ptr], __dbase_wfm_output_text_82
    mov dword ptr [__dbase_wfm_mem___wfm_ltrim_8_len], 0
    mov dword ptr [__dbase_wfm_mem___wfm_ltrim_8_type], 3
    jmp __dbase_wfm_flow_ltrim_done_154
__dbase_wfm_flow_ltrim_valid_153:
    mov eax, dword ptr [__dbase_wfm_mem_Text_len]
    inc eax
    push eax
    call __dbase_malloc
    add esp, 4
    test eax, eax
    jne __dbase_wfm_flow_trim_ltrim_155_allocated
    push 8
    call ExitProcess
__dbase_wfm_flow_trim_ltrim_155_allocated:
    mov dword ptr [__dbase_wfm_mem___wfm_ltrim_8_ptr], eax
    push esi
    push edi
    mov esi, dword ptr [__dbase_wfm_mem_Text_ptr]
    mov edi, esi
    mov eax, dword ptr [__dbase_wfm_mem_Text_len]
    add edi, eax
__dbase_wfm_flow_trim_ltrim_155_left_loop:
    cmp esi, edi
    jae __dbase_wfm_flow_trim_ltrim_155_left_done
    mov al, byte ptr [esi]
    cmp al, 32
    jne __dbase_wfm_flow_trim_ltrim_155_left_done
__dbase_wfm_flow_trim_ltrim_155_left_advance:
    inc esi
    jmp __dbase_wfm_flow_trim_ltrim_155_left_loop
__dbase_wfm_flow_trim_ltrim_155_left_done:
    sub edi, esi
    mov dword ptr [__dbase_wfm_mem___wfm_ltrim_8_len], edi
    mov dword ptr [__dbase_wfm_mem___wfm_ltrim_8_type], 3
    mov ecx, edi
    mov edi, dword ptr [__dbase_wfm_mem___wfm_ltrim_8_ptr]
__dbase_wfm_flow_trim_ltrim_155_copy_loop:
    test ecx, ecx
    je __dbase_wfm_flow_trim_ltrim_155_copy_done
    movzx eax, byte ptr [esi]
    mov byte ptr [edi], al
    inc esi
    inc edi
    dec ecx
    jmp __dbase_wfm_flow_trim_ltrim_155_copy_loop
__dbase_wfm_flow_trim_ltrim_155_copy_done:
    mov byte ptr [edi], 0
    pop edi
    pop esi
__dbase_wfm_flow_ltrim_done_154:
    ; ? "[" + LTRIM(Text) + "]"
    push 0
    push 1
    push __dbase_wfm_output_text_81
    call DBaseQtConsoleWrite
    add esp, 12
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem___wfm_ltrim_8_type
    call DBaseWfmFormatValue
    add esp, 12
    push 0
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
    push 1
    push 1
    push __dbase_wfm_output_text_83
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 506
    cmp dword ptr [__dbase_wfm_mem_Text_type], 3
    je __dbase_wfm_flow_trim_valid_156
    mov dword ptr [__dbase_wfm_mem___wfm_trim_9_ptr], __dbase_wfm_output_text_85
    mov dword ptr [__dbase_wfm_mem___wfm_trim_9_len], 0
    mov dword ptr [__dbase_wfm_mem___wfm_trim_9_type], 3
    jmp __dbase_wfm_flow_trim_done_157
__dbase_wfm_flow_trim_valid_156:
    mov eax, dword ptr [__dbase_wfm_mem_Text_len]
    inc eax
    push eax
    call __dbase_malloc
    add esp, 4
    test eax, eax
    jne __dbase_wfm_flow_trim_trim_158_allocated
    push 8
    call ExitProcess
__dbase_wfm_flow_trim_trim_158_allocated:
    mov dword ptr [__dbase_wfm_mem___wfm_trim_9_ptr], eax
    push esi
    push edi
    mov esi, dword ptr [__dbase_wfm_mem_Text_ptr]
    mov edi, esi
    mov eax, dword ptr [__dbase_wfm_mem_Text_len]
    add edi, eax
__dbase_wfm_flow_trim_trim_158_left_loop:
    cmp esi, edi
    jae __dbase_wfm_flow_trim_trim_158_left_done
    mov al, byte ptr [esi]
    cmp al, 32
    je __dbase_wfm_flow_trim_trim_158_left_advance
    cmp al, 9
    je __dbase_wfm_flow_trim_trim_158_left_advance
    cmp al, 10
    je __dbase_wfm_flow_trim_trim_158_left_advance
    cmp al, 8
    je __dbase_wfm_flow_trim_trim_158_left_advance
    cmp al, 13
    jne __dbase_wfm_flow_trim_trim_158_left_done
__dbase_wfm_flow_trim_trim_158_left_advance:
    inc esi
    jmp __dbase_wfm_flow_trim_trim_158_left_loop
__dbase_wfm_flow_trim_trim_158_left_done:
__dbase_wfm_flow_trim_trim_158_right_loop:
    cmp edi, esi
    jbe __dbase_wfm_flow_trim_trim_158_right_done
    mov al, byte ptr [edi-1]
    cmp al, 32
    je __dbase_wfm_flow_trim_trim_158_right_retreat
    cmp al, 9
    je __dbase_wfm_flow_trim_trim_158_right_retreat
    cmp al, 10
    je __dbase_wfm_flow_trim_trim_158_right_retreat
    cmp al, 8
    je __dbase_wfm_flow_trim_trim_158_right_retreat
    cmp al, 13
    jne __dbase_wfm_flow_trim_trim_158_right_done
__dbase_wfm_flow_trim_trim_158_right_retreat:
    dec edi
    jmp __dbase_wfm_flow_trim_trim_158_right_loop
__dbase_wfm_flow_trim_trim_158_right_done:
    sub edi, esi
    mov dword ptr [__dbase_wfm_mem___wfm_trim_9_len], edi
    mov dword ptr [__dbase_wfm_mem___wfm_trim_9_type], 3
    mov ecx, edi
    mov edi, dword ptr [__dbase_wfm_mem___wfm_trim_9_ptr]
__dbase_wfm_flow_trim_trim_158_copy_loop:
    test ecx, ecx
    je __dbase_wfm_flow_trim_trim_158_copy_done
    movzx eax, byte ptr [esi]
    mov byte ptr [edi], al
    inc esi
    inc edi
    dec ecx
    jmp __dbase_wfm_flow_trim_trim_158_copy_loop
__dbase_wfm_flow_trim_trim_158_copy_done:
    mov byte ptr [edi], 0
    pop edi
    pop esi
__dbase_wfm_flow_trim_done_157:
    ; ? "[" + TRIM(Text) + "]"
    push 0
    push 1
    push __dbase_wfm_output_text_84
    call DBaseQtConsoleWrite
    add esp, 12
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem___wfm_trim_9_type
    call DBaseWfmFormatValue
    add esp, 12
    push 0
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
    push 1
    push 1
    push __dbase_wfm_output_text_86
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 509
    cmp dword ptr [__dbase_wfm_mem_Text_type], 3
    je __dbase_wfm_flow_trim_valid_159
    mov dword ptr [__dbase_wfm_mem___wfm_trim_10_ptr], __dbase_wfm_output_text_87
    mov dword ptr [__dbase_wfm_mem___wfm_trim_10_len], 0
    mov dword ptr [__dbase_wfm_mem___wfm_trim_10_type], 3
    jmp __dbase_wfm_flow_trim_done_160
__dbase_wfm_flow_trim_valid_159:
    mov eax, dword ptr [__dbase_wfm_mem_Text_len]
    inc eax
    push eax
    call __dbase_malloc
    add esp, 4
    test eax, eax
    jne __dbase_wfm_flow_trim_trim_161_allocated
    push 8
    call ExitProcess
__dbase_wfm_flow_trim_trim_161_allocated:
    mov dword ptr [__dbase_wfm_mem___wfm_trim_10_ptr], eax
    push esi
    push edi
    mov esi, dword ptr [__dbase_wfm_mem_Text_ptr]
    mov edi, esi
    mov eax, dword ptr [__dbase_wfm_mem_Text_len]
    add edi, eax
__dbase_wfm_flow_trim_trim_161_left_loop:
    cmp esi, edi
    jae __dbase_wfm_flow_trim_trim_161_left_done
    mov al, byte ptr [esi]
    cmp al, 32
    je __dbase_wfm_flow_trim_trim_161_left_advance
    cmp al, 9
    je __dbase_wfm_flow_trim_trim_161_left_advance
    cmp al, 10
    je __dbase_wfm_flow_trim_trim_161_left_advance
    cmp al, 8
    je __dbase_wfm_flow_trim_trim_161_left_advance
    cmp al, 13
    jne __dbase_wfm_flow_trim_trim_161_left_done
__dbase_wfm_flow_trim_trim_161_left_advance:
    inc esi
    jmp __dbase_wfm_flow_trim_trim_161_left_loop
__dbase_wfm_flow_trim_trim_161_left_done:
__dbase_wfm_flow_trim_trim_161_right_loop:
    cmp edi, esi
    jbe __dbase_wfm_flow_trim_trim_161_right_done
    mov al, byte ptr [edi-1]
    cmp al, 32
    je __dbase_wfm_flow_trim_trim_161_right_retreat
    cmp al, 9
    je __dbase_wfm_flow_trim_trim_161_right_retreat
    cmp al, 10
    je __dbase_wfm_flow_trim_trim_161_right_retreat
    cmp al, 8
    je __dbase_wfm_flow_trim_trim_161_right_retreat
    cmp al, 13
    jne __dbase_wfm_flow_trim_trim_161_right_done
__dbase_wfm_flow_trim_trim_161_right_retreat:
    dec edi
    jmp __dbase_wfm_flow_trim_trim_161_right_loop
__dbase_wfm_flow_trim_trim_161_right_done:
    sub edi, esi
    mov dword ptr [__dbase_wfm_mem___wfm_trim_10_len], edi
    mov dword ptr [__dbase_wfm_mem___wfm_trim_10_type], 3
    mov ecx, edi
    mov edi, dword ptr [__dbase_wfm_mem___wfm_trim_10_ptr]
__dbase_wfm_flow_trim_trim_161_copy_loop:
    test ecx, ecx
    je __dbase_wfm_flow_trim_trim_161_copy_done
    movzx eax, byte ptr [esi]
    mov byte ptr [edi], al
    inc esi
    inc edi
    dec ecx
    jmp __dbase_wfm_flow_trim_trim_161_copy_loop
__dbase_wfm_flow_trim_trim_161_copy_done:
    mov byte ptr [edi], 0
    pop edi
    pop esi
__dbase_wfm_flow_trim_done_160:
    mov eax, __dbase_wfm_mem___wfm_trim_10_type
    mov edx, __dbase_wfm_mem_Ergebnis_type
    call __dbase_wfm_copy_variant
    ; Quellcode Zeile: 510
    cmp dword ptr [__dbase_wfm_mem_Ergebnis_type], 3
    je __dbase_wfm_flow_len_valid_162
    xor ecx, ecx
    jmp __dbase_wfm_flow_len_skip_165
__dbase_wfm_flow_len_valid_162:
    push esi
    mov esi, dword ptr [__dbase_wfm_mem_Ergebnis_ptr]
    mov edx, dword ptr [__dbase_wfm_mem_Ergebnis_len]
    xor ecx, ecx
__dbase_wfm_flow_len_loop_164:
    test esi, esi
    je __dbase_wfm_flow_len_finish_166
    test edx, edx
    jz __dbase_wfm_flow_len_finish_166
    movzx eax, byte ptr [esi]
    and eax, 192
    cmp eax, 128
    je len___dbase_wfm_flow_len_loop_164_continuation
    inc ecx
len___dbase_wfm_flow_len_loop_164_continuation:
    inc esi
    dec edx
    jmp __dbase_wfm_flow_len_loop_164
__dbase_wfm_flow_len_finish_166:
    pop esi
__dbase_wfm_flow_len_skip_165:
    mov dword ptr [__dbase_temp_number], ecx
    fild dword ptr [__dbase_temp_number]
    fstp qword ptr [__dbase_wfm_mem___wfm_len_11_num]
    ; ? LEN(Ergebnis)
    push __dbase_wfm_format_result
    push dword ptr [__dbase_format_buffer]
    push __dbase_wfm_mem___wfm_len_11_type
    call DBaseWfmFormatValue
    add esp, 12
    push 1
    push dword ptr [__dbase_wfm_format_result_len]
    push dword ptr [__dbase_wfm_format_result]
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 512
__dbase_wfm_flow_method_exit_120:
    ret
; END WFM PROCEDURE/FUNCTION: PushButton1_onClick


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: PushButton1_onGotFocus
; ------------------------------------------------------------
__dbase_wfm_proc_PushButton1_onGotFocus:
    mov eax, dword ptr [esp+4]
    mov dword ptr [__dbase_wfm_param_PushButton1_onGotFocus_Sender], eax
    ; Quellcode Zeile: 518
    ; ? "Button 0 onGotFocus"
    push 1
    push 19
    push __dbase_wfm_output_text_88
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 519
__dbase_wfm_flow_method_exit_167:
    ret
; END WFM PROCEDURE/FUNCTION: PushButton1_onGotFocus


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: PushButton1_onLostFocus
; ------------------------------------------------------------
__dbase_wfm_proc_PushButton1_onLostFocus:
    mov eax, dword ptr [esp+4]
    mov dword ptr [__dbase_wfm_param_PushButton1_onLostFocus_Sender], eax
    ; Quellcode Zeile: 522
    ; ? "Button 0 onLostFocus"
    push 1
    push 20
    push __dbase_wfm_output_text_89
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 523
__dbase_wfm_flow_method_exit_168:
    ret
; END WFM PROCEDURE/FUNCTION: PushButton1_onLostFocus


; ------------------------------------------------------------
; WFM PROCEDURE/FUNCTION MASCHINENCODE: TestAndNotXor
; ------------------------------------------------------------
__dbase_wfm_proc_TestAndNotXor:
    ; Quellcode Zeile: 433
    ; IF A > 0 .AND. C < 10
    fld qword ptr [__dbase_wfm_mem_A_num]
    fldz
    fucomip st0, st1
    fstp st0
    jae __dbase_wfm_flow_if_false_170
    fld qword ptr [__dbase_wfm_mem_C_num]
    fld qword ptr [__dbase_wfm_numconst_6]
    fucomip st0, st1
    fstp st0
    jbe __dbase_wfm_flow_if_false_170
    ; Quellcode Zeile: 434
    ; ? "Beide Bedingungen erfüllt"
    push 1
    push 26
    push __dbase_wfm_output_text_90
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 435
    jmp __dbase_wfm_flow_if_end_171
__dbase_wfm_flow_if_false_170:
    ; Quellcode Zeile: 436
    ; ? "Bedingung nicht erfüllt"
    push 1
    push 24
    push __dbase_wfm_output_text_91
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 437
__dbase_wfm_flow_if_end_171:
    ; Quellcode Zeile: 438
    ; IF .NOT. (A = 0 .OR. C >= 10)
    fld qword ptr [__dbase_wfm_mem_A_num]
    fldz
    fucomip st0, st1
    fstp st0
    je __dbase_wfm_flow_or_true_175
__dbase_wfm_flow_not_true_176:
    fld qword ptr [__dbase_wfm_mem_C_num]
    fld qword ptr [__dbase_wfm_numconst_6]
    fucomip st0, st1
    fstp st0
    ja __dbase_wfm_flow_not_true_174
__dbase_wfm_flow_or_true_175:
    jmp __dbase_wfm_flow_if_false_172
__dbase_wfm_flow_not_true_174:
    ; Quellcode Zeile: 439
    ; ? "NOT und OR funktionieren"
    push 1
    push 24
    push __dbase_wfm_output_text_92
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 440
__dbase_wfm_flow_if_false_172:
__dbase_wfm_flow_if_end_173:
    ; Quellcode Zeile: 441
    ; IF (A > 0) .XOR. (C < 0)
    fld qword ptr [__dbase_wfm_mem_A_num]
    fldz
    fucomip st0, st1
    fstp st0
    jae __dbase_wfm_flow_xor_left_false_179
    fld qword ptr [__dbase_wfm_mem_C_num]
    fldz
    fucomip st0, st1
    fstp st0
    ja __dbase_wfm_flow_if_false_177
__dbase_wfm_flow_not_true_181:
    jmp __dbase_wfm_flow_xor_done_180
__dbase_wfm_flow_xor_left_false_179:
    fld qword ptr [__dbase_wfm_mem_C_num]
    fldz
    fucomip st0, st1
    fstp st0
    jbe __dbase_wfm_flow_if_false_177
__dbase_wfm_flow_xor_done_180:
    ; Quellcode Zeile: 442
    ; ? "Genau eine Bedingung ist wahr"
    push 1
    push 29
    push __dbase_wfm_output_text_93
    call DBaseQtConsoleWrite
    add esp, 12
    ; Quellcode Zeile: 443
__dbase_wfm_flow_if_false_177:
__dbase_wfm_flow_if_end_178:
    ; Quellcode Zeile: 444
__dbase_wfm_flow_method_exit_169:
    ret
; END WFM PROCEDURE/FUNCTION: TestAndNotXor

; Stage 460: shared dynamic variant helpers
.section .text
__dbase_wfm_assign_numeric_header:
    mov dword ptr [eax], edx
    mov dword ptr [eax+12], 0
    mov dword ptr [eax+16], 0
    ret
__dbase_wfm_copy_variant:
    mov ecx, dword ptr [eax]
    mov dword ptr [edx], ecx
    fld qword ptr [eax+4]
    fstp qword ptr [edx+4]
    mov ecx, dword ptr [eax+12]
    mov dword ptr [edx+12], ecx
    mov ecx, dword ptr [eax+16]
    mov dword ptr [edx+16], ecx
    ret

; Stage 127 WFM initialized data
.section .data
__dbase_wfm_qt_output_marker:
    db 68, 54, 52, 68, 66, 65, 83, 69, 95, 87, 70, 77, 95, 81, 84, 95, 79, 85, 84, 80, 85, 84, 95, 86, 49, 0
__dbase_wfm_text_0:
    db 70, 111, 114, 109, 49, 92, 48
__dbase_wfm_text_1:
    db 80, 85, 83, 72, 66, 85, 84, 84, 79, 78, 92, 48
__dbase_wfm_text_2:
    db 79, 110, 67, 108, 105, 99, 107, 92, 48
__dbase_wfm_text_3:
    db 79, 110, 71, 111, 116, 70, 111, 99, 117, 115, 92, 48
__dbase_wfm_text_4:
    db 79, 110, 76, 111, 115, 116, 70, 111, 99, 117, 115, 92, 48
__dbase_wfm_text_77:
    db 122, 92, 48
__dbase_wfm_output_text_5:
    db 115, 104, 101, 108, 108, 51, 50, 46, 100, 108, 108
__dbase_wfm_flow_ffi_ansi_4:
    db 111, 112, 101, 110, 0
__dbase_wfm_flow_ffi_ansi_6:
    db 110, 111, 116, 101, 112, 97, 100, 46, 101, 120, 101, 0
__dbase_wfm_output_text_6:
    db 78
__dbase_wfm_output_text_7:
    db 67
__dbase_wfm_output_text_8:
    db 79
__dbase_wfm_output_text_9:
    db 76
__dbase_wfm_output_text_10:
    db 68
__dbase_wfm_output_text_11:
    db 85
__dbase_wfm_output_text_12:
    db 78
__dbase_wfm_output_text_13:
    db 67
__dbase_wfm_output_text_14:
    db 79
__dbase_wfm_output_text_15:
    db 76
__dbase_wfm_output_text_16:
    db 68
__dbase_wfm_output_text_17:
    db 85
__dbase_wfm_output_text_18:
    db 120, 121, 122, 32, 105, 115, 116, 32, 110, 117, 109, 101, 114, 105, 115, 99, 104
__dbase_wfm_output_text_19:
    db 72, 97, 108, 108, 111
__dbase_wfm_output_text_20:
    db 78
__dbase_wfm_output_text_21:
    db 67
__dbase_wfm_output_text_22:
    db 79
__dbase_wfm_output_text_23:
    db 76
__dbase_wfm_output_text_24:
    db 68
__dbase_wfm_output_text_25:
    db 85
__dbase_wfm_output_text_26:
    db 78
__dbase_wfm_output_text_27:
    db 67
__dbase_wfm_output_text_28:
    db 79
__dbase_wfm_output_text_29:
    db 76
__dbase_wfm_output_text_30:
    db 68
__dbase_wfm_output_text_31:
    db 85
__dbase_wfm_output_text_32:
    db 78
__dbase_wfm_output_text_33:
    db 67
__dbase_wfm_output_text_34:
    db 79
__dbase_wfm_output_text_35:
    db 76
__dbase_wfm_output_text_36:
    db 68
__dbase_wfm_output_text_37:
    db 85
__dbase_wfm_output_text_38:
    db 112, 49, 32, 61, 32
__dbase_wfm_output_text_39:
    db 53, 49
__dbase_wfm_output_text_40:
    db 112, 50, 32, 61, 32
__dbase_wfm_output_text_41:
    db 52
__dbase_wfm_output_text_42:
    db 78
__dbase_wfm_output_text_43:
    db 67
__dbase_wfm_output_text_44:
    db 79
__dbase_wfm_output_text_45:
    db 76
__dbase_wfm_output_text_46:
    db 68
__dbase_wfm_output_text_47:
    db 85
__dbase_wfm_output_text_48:
    db 78
__dbase_wfm_output_text_49:
    db 67
__dbase_wfm_output_text_50:
    db 79
__dbase_wfm_output_text_51:
    db 76
__dbase_wfm_output_text_52:
    db 68
__dbase_wfm_output_text_53:
    db 85
__dbase_wfm_output_text_54:
    db 66, 117, 116, 116, 111, 110, 32, 49, 32, 111, 110, 32, 67, 108, 105, 99, 107
__dbase_wfm_output_text_55:
    db 66, 117, 116, 116, 111, 110, 32, 49, 32, 111, 110, 32, 71, 111, 116, 32, 70, 111, 99, 117, 115
__dbase_wfm_output_text_56:
    db 66, 117, 116, 116, 111, 110, 32, 49, 32, 111, 110, 32, 76, 111, 115, 116, 32, 70, 111, 99, 117, 115
__dbase_wfm_output_text_57:
    db 66, 117, 116, 116, 111, 110, 32, 50, 32, 111, 110, 67, 108, 105, 99, 107
__dbase_wfm_output_text_58:
    db 66, 117, 116, 116, 111, 110, 32, 50, 32, 103, 111, 116, 32, 102, 111, 99, 117, 115, 32, 111, 110, 32, 66, 117, 116, 116, 111, 110
__dbase_wfm_output_text_59:
    db 66, 117, 116, 116, 111, 110, 32, 50, 32, 111, 110, 32, 108, 111, 115, 116, 32, 102, 111, 99, 117, 115
__dbase_wfm_output_text_60:
    db 49, 58, 32
__dbase_wfm_output_text_61:
    db 49, 48, 49, 46, 52, 50
__dbase_wfm_output_text_62:
    db 50, 58, 32
__dbase_wfm_output_text_63:
    db 49, 48, 49
__dbase_wfm_output_text_64:
    db 51, 58, 32
__dbase_wfm_output_text_65:
    db 90, 101, 105, 99, 104, 101, 110, 115, 116, 114, 105, 110, 103
__dbase_wfm_output_text_66:
    db 52, 58, 32
__dbase_wfm_output_text_67:
    db 53, 58, 32
__dbase_wfm_output_text_68:
    db 69, 105, 110, 101, 32, 77, 97, 117, 115, 32, 105, 115, 116, 32, 118, 111, 114, 104, 97, 110, 100, 101, 110, 46
__dbase_wfm_output_text_69:
    db 75, 101, 105, 110, 101, 32, 77, 97, 117, 115, 32, 101, 114, 107, 97, 110, 110, 116, 46
__dbase_wfm_output_text_70:
    db 77, 97, 117, 115, 32, 107, 97, 110, 110, 32, 118, 101, 114, 119, 101, 110, 100, 101, 116, 32, 119, 101, 114, 100, 101, 110, 46
__dbase_wfm_output_text_71:
    db 69, 105, 110, 101, 32, 84, 97, 115, 116, 97, 116, 117, 114, 32, 105, 115, 116, 32, 118, 111, 114, 104, 97, 110, 100, 101, 110, 46
__dbase_wfm_output_text_72:
    db 75, 101, 105, 110, 101, 32, 84, 97, 115, 116, 97, 116, 117, 114, 32, 101, 114, 107, 97, 110, 110, 116, 46
__dbase_wfm_output_text_73:
    db 77, 97, 117, 115, 32, 117, 110, 100, 32, 84, 97, 115, 116, 97, 116, 117, 114, 32, 115, 105, 110, 100, 32, 118, 111, 114, 104, 97, 110, 100, 101, 110, 46
__dbase_wfm_output_text_74:
    db 75, 101, 105, 110, 101, 32, 84, 97, 115, 116, 97, 116, 117, 114, 32, 103, 101, 102, 117, 110, 100, 101, 110, 46
__dbase_wfm_output_text_75:
    db 65
__dbase_wfm_output_text_76:
    db 71, 114, 111, 115, 115, 98, 117, 99, 104, 115, 116, 97, 98, 101, 32, 101, 114, 107, 97, 110, 110, 116
__dbase_wfm_output_text_78:
    db 75, 108, 101, 105, 110, 98, 117, 99, 104, 115, 116, 97, 98, 101, 32, 101, 114, 107, 97, 110, 110, 116
__dbase_wfm_output_text_79:
    db 69, 105, 110, 32, 83, 116, 114, 105, 110, 103
__dbase_wfm_output_text_80:
    db 32, 32, 32, 72, 97, 108, 108, 111, 32, 87, 101, 108, 116, 32, 32, 32
__dbase_wfm_output_text_81:
    db 91
__dbase_wfm_output_text_82:
    db 0
__dbase_wfm_output_text_83:
    db 93
__dbase_wfm_output_text_84:
    db 91
__dbase_wfm_output_text_85:
    db 0
__dbase_wfm_output_text_86:
    db 93
__dbase_wfm_output_text_87:
    db 0
__dbase_wfm_output_text_88:
    db 66, 117, 116, 116, 111, 110, 32, 48, 32, 111, 110, 71, 111, 116, 70, 111, 99, 117, 115
__dbase_wfm_output_text_89:
    db 66, 117, 116, 116, 111, 110, 32, 48, 32, 111, 110, 76, 111, 115, 116, 70, 111, 99, 117, 115
__dbase_wfm_output_text_90:
    db 66, 101, 105, 100, 101, 32, 66, 101, 100, 105, 110, 103, 117, 110, 103, 101, 110, 32, 101, 114, 102, 195, 188, 108, 108, 116
__dbase_wfm_output_text_91:
    db 66, 101, 100, 105, 110, 103, 117, 110, 103, 32, 110, 105, 99, 104, 116, 32, 101, 114, 102, 195, 188, 108, 108, 116
__dbase_wfm_output_text_92:
    db 78, 79, 84, 32, 117, 110, 100, 32, 79, 82, 32, 102, 117, 110, 107, 116, 105, 111, 110, 105, 101, 114, 101, 110
__dbase_wfm_output_text_93:
    db 71, 101, 110, 97, 117, 32, 101, 105, 110, 101, 32, 66, 101, 100, 105, 110, 103, 117, 110, 103, 32, 105, 115, 116, 32, 119, 97, 104, 114

; Stage 456: one embedded JSON document per WFM FORM
__dbase_wfm_external_ui_slots:
    dd __dbase_wfm_form
    dd __dbase_wfm_obj_THIS_PushButton1
    dd __dbase_wfm_obj_THIS_Button1
    dd __dbase_wfm_obj_THIS_Button2
__dbase_wfm_external_ui_payload:
    %include "Form1.generated.pe32.payload.inc"
; Stage 460: fixed numeric WFM internal slot (__wfm_ismouse_print)
__dbase_wfm_mem___wfm_ismouse_print_type:
    dd 1
__dbase_wfm_mem___wfm_ismouse_print_num:
    dq 0
__dbase_wfm_mem___wfm_ismouse_print_ptr:
    dd 0
__dbase_wfm_mem___wfm_ismouse_print_len:
    dd 0
; Stage 460: fixed numeric WFM internal slot (__wfm_iskeyboard_print)
__dbase_wfm_mem___wfm_iskeyboard_print_type:
    dd 1
__dbase_wfm_mem___wfm_iskeyboard_print_num:
    dq 0
__dbase_wfm_mem___wfm_iskeyboard_print_ptr:
    dd 0
__dbase_wfm_mem___wfm_iskeyboard_print_len:
    dd 0
; Stage 460: fixed numeric WFM internal slot (__wfm_len_6)
__dbase_wfm_mem___wfm_len_6_type:
    dd 1
__dbase_wfm_mem___wfm_len_6_num:
    dq 0
__dbase_wfm_mem___wfm_len_6_ptr:
    dd 0
__dbase_wfm_mem___wfm_len_6_len:
    dd 0
; Stage 460: fixed numeric WFM internal slot (__wfm_len_7)
__dbase_wfm_mem___wfm_len_7_type:
    dd 1
__dbase_wfm_mem___wfm_len_7_num:
    dq 0
__dbase_wfm_mem___wfm_len_7_ptr:
    dd 0
__dbase_wfm_mem___wfm_len_7_len:
    dd 0
; Stage 460: fixed numeric WFM internal slot (__wfm_len_11)
__dbase_wfm_mem___wfm_len_11_type:
    dd 1
__dbase_wfm_mem___wfm_len_11_num:
    dq 0
__dbase_wfm_mem___wfm_len_11_ptr:
    dd 0
__dbase_wfm_mem___wfm_len_11_len:
    dd 0

; Stage 192: WFM numeric STORE constants
__dbase_wfm_numconst_0:
    dd 0, 1075970048
__dbase_wfm_numconst_1:
    dd 0, 1074790400
__dbase_wfm_numconst_2:
    dd 3435973837, 1079958732
__dbase_wfm_numconst_3:
    dd 1202590843, 1079597793
__dbase_wfm_numconst_4:
    dd 0, 1075838976
__dbase_wfm_numconst_5:
    dd 0, 1075314688
__dbase_wfm_numconst_6:
    dd 0, 1076101120

; Stage 223 WFM zero-initialized storage
.section .bss
__dbase_wfm_form:
    resd 1
__dbase_wfm_obj_THIS_PushButton1:
    resd 1
__dbase_wfm_obj_THIS_Button1:
    resd 1
__dbase_wfm_obj_THIS_Button2:
    resd 1

; Stage 223: WFM runtime parameter slots (.bss)
__dbase_wfm_param___init___p1:
    resd 1
__dbase_wfm_param___init___p2:
    resd 1
__dbase_wfm_param_Button1_onClick_Sender:
    resd 1
__dbase_wfm_param_Button1_onGotFocus_Sender:
    resd 1
__dbase_wfm_param_Button1_onLostFocus_Sender:
    resd 1
__dbase_wfm_param_Button2_onClick_Sender:
    resd 1
__dbase_wfm_param_Button2_onGotFocus_Sender:
    resd 1
__dbase_wfm_param_Button2_onLostFocus_Sender:
    resd 1
__dbase_wfm_param_CheckLower_c:
    resd 1
__dbase_wfm_param_PushButton1_onClick_Sender:
    resd 1
__dbase_wfm_param_PushButton1_onGotFocus_Sender:
    resd 1
__dbase_wfm_param_PushButton1_onLostFocus_Sender:
    resd 1

; Stage 449: shared WFM formatter's output (ptr, length)
__dbase_wfm_format_result:
    resd 1
__dbase_wfm_format_result_len:
    resd 1

; Stage 223: typed dBase WFM memory variables (.bss)
__dbase_wfm_mem_result_type:
    resd 1
__dbase_wfm_mem_result_num:
    resq 1
__dbase_wfm_mem_result_ptr:
    resd 1
__dbase_wfm_mem_result_len:
    resd 1
__dbase_wfm_mem_xyz_type:
    resd 1
__dbase_wfm_mem_xyz_num:
    resq 1
__dbase_wfm_mem_xyz_ptr:
    resd 1
__dbase_wfm_mem_xyz_len:
    resd 1
__dbase_wfm_mem_Ausdruck_type:
    resd 1
__dbase_wfm_mem_Ausdruck_num:
    resq 1
__dbase_wfm_mem_Ausdruck_ptr:
    resd 1
__dbase_wfm_mem_Ausdruck_len:
    resd 1
__dbase_wfm_mem_SpeicherVar_type:
    resd 1
__dbase_wfm_mem_SpeicherVar_num:
    resq 1
__dbase_wfm_mem_SpeicherVar_ptr:
    resd 1
__dbase_wfm_mem_SpeicherVar_len:
    resd 1
__dbase_wfm_mem_HatMaus_type:
    resd 1
__dbase_wfm_mem_HatMaus_num:
    resq 1
__dbase_wfm_mem_HatMaus_ptr:
    resd 1
__dbase_wfm_mem_HatMaus_len:
    resd 1
__dbase_wfm_mem_HatTastatur_type:
    resd 1
__dbase_wfm_mem_HatTastatur_num:
    resq 1
__dbase_wfm_mem_HatTastatur_ptr:
    resd 1
__dbase_wfm_mem_HatTastatur_len:
    resd 1
__dbase_wfm_mem_Zeichen_type:
    resd 1
__dbase_wfm_mem_Zeichen_num:
    resq 1
__dbase_wfm_mem_Zeichen_ptr:
    resd 1
__dbase_wfm_mem_Zeichen_len:
    resd 1
__dbase_wfm_mem_Text_type:
    resd 1
__dbase_wfm_mem_Text_num:
    resq 1
__dbase_wfm_mem_Text_ptr:
    resd 1
__dbase_wfm_mem_Text_len:
    resd 1
__dbase_wfm_mem_Ergebnis_type:
    resd 1
__dbase_wfm_mem_Ergebnis_num:
    resq 1
__dbase_wfm_mem_Ergebnis_ptr:
    resd 1
__dbase_wfm_mem_Ergebnis_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_ptr:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_ptr:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_ptr:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_ptr:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_ptr:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_ptr:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_14_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_14_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_14_ptr:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_14_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_27_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_27_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_27_ptr:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_27_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_48_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_48_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_48_ptr:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_48_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_61_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_61_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_61_ptr:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_61_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_74_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_74_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_74_ptr:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_74_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_83_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_83_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_83_ptr:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_83_len:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_96_type:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_96_num:
    resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_96_ptr:
    resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_96_len:
    resd 1
__dbase_wfm_mem___wfm_arg_CheckLower_c_type:
    resd 1
__dbase_wfm_mem___wfm_arg_CheckLower_c_num:
    resq 1
__dbase_wfm_mem___wfm_arg_CheckLower_c_ptr:
    resd 1
__dbase_wfm_mem___wfm_arg_CheckLower_c_len:
    resd 1
__dbase_wfm_mem___string_arg_1_type:
    resd 1
__dbase_wfm_mem___string_arg_1_num:
    resq 1
__dbase_wfm_mem___string_arg_1_ptr:
    resd 1
__dbase_wfm_mem___string_arg_1_len:
    resd 1
__dbase_wfm_mem___string_arg_2_type:
    resd 1
__dbase_wfm_mem___string_arg_2_num:
    resq 1
__dbase_wfm_mem___string_arg_2_ptr:
    resd 1
__dbase_wfm_mem___string_arg_2_len:
    resd 1
__dbase_wfm_mem___string_arg_3_type:
    resd 1
__dbase_wfm_mem___string_arg_3_num:
    resq 1
__dbase_wfm_mem___string_arg_3_ptr:
    resd 1
__dbase_wfm_mem___string_arg_3_len:
    resd 1
__dbase_wfm_mem___string_arg_4_type:
    resd 1
__dbase_wfm_mem___string_arg_4_num:
    resq 1
__dbase_wfm_mem___string_arg_4_ptr:
    resd 1
__dbase_wfm_mem___string_arg_4_len:
    resd 1
__dbase_wfm_mem___wfm_text_literal_5_type:
    resd 1
__dbase_wfm_mem___wfm_text_literal_5_num:
    resq 1
__dbase_wfm_mem___wfm_text_literal_5_ptr:
    resd 1
__dbase_wfm_mem___wfm_text_literal_5_len:
    resd 1
__dbase_wfm_mem___wfm_ltrim_8_type:
    resd 1
__dbase_wfm_mem___wfm_ltrim_8_num:
    resq 1
__dbase_wfm_mem___wfm_ltrim_8_ptr:
    resd 1
__dbase_wfm_mem___wfm_ltrim_8_len:
    resd 1
__dbase_wfm_mem___wfm_trim_9_type:
    resd 1
__dbase_wfm_mem___wfm_trim_9_num:
    resq 1
__dbase_wfm_mem___wfm_trim_9_ptr:
    resd 1
__dbase_wfm_mem___wfm_trim_9_len:
    resd 1
__dbase_wfm_mem___wfm_trim_10_type:
    resd 1
__dbase_wfm_mem___wfm_trim_10_num:
    resq 1
__dbase_wfm_mem___wfm_trim_10_ptr:
    resd 1
__dbase_wfm_mem___wfm_trim_10_len:
    resd 1
__dbase_wfm_mem_A_type:
    resd 1
__dbase_wfm_mem_A_num:
    resq 1
__dbase_wfm_mem_A_ptr:
    resd 1
__dbase_wfm_mem_A_len:
    resd 1
__dbase_wfm_mem_C_type:
    resd 1
__dbase_wfm_mem_C_num:
    resq 1
__dbase_wfm_mem_C_ptr:
    resd 1
__dbase_wfm_mem_C_len:
    resd 1
__dbase_wfm_local___dbase_top_level___a_type:
    resd 1
__dbase_wfm_local___dbase_top_level___a_num:
    resq 1
__dbase_wfm_local___dbase_top_level___a_ptr:
    resd 1
__dbase_wfm_local___dbase_top_level___a_len:
    resd 1
__dbase_wfm_local___dbase_top_level___c_type:
    resd 1
__dbase_wfm_local___dbase_top_level___c_num:
    resq 1
__dbase_wfm_local___dbase_top_level___c_ptr:
    resd 1
__dbase_wfm_local___dbase_top_level___c_len:
    resd 1
