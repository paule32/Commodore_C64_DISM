.att_syntax
%include "Form1.generated.pe32.extern.inc"
.code32

.globl _start
.d64_entry _start

.text

_start:
    push $__dbase_format_buffer
    push $0
    push $0
    push $0
    push $__dbase_text_0
    call DBaseQtRuntimeStartup
    addl $20, %esp
    testl %eax, %eax
    jne __dbase_qt_init_ok_2
    push $1
    call ExitProcess
__dbase_qt_init_ok_2:
    push $0
    call DBaseQtSetDebugVisible
    addl $4, %esp
    call DBaseQtEnsureDefaultMenu
    call DBaseQtShowWindow
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    testl %eax, %eax
    jne __dbase_program_cleanup_1
    cmpl $-1, __dbase_output_debug_override
    jne __dbase_output_override_ready_3
    cmpl $0, __dbase_output_format_screen
    je __dbase_output_console_4
    jmp __dbase_output_show_done_5
__dbase_output_override_ready_3:
    cmpl $0, __dbase_output_debug_override
    je __dbase_output_console_4
__dbase_output_show_done_5:
    cmpl $0, __dbase_output_debug_visible
    jne __dbase_output_already_visible_7
    movl $1, __dbase_output_debug_visible
    push $1
    call DBaseQtSetDebugVisible
    addl $4, %esp
__dbase_output_already_visible_7:
    jmp __dbase_output_done_6
__dbase_output_console_4:
    push $0
    push $__dbase_text_1
    call DBaseConsoleWrite
    addl $8, %esp
__dbase_output_done_6:
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    testl %eax, %eax
    jne __dbase_program_cleanup_1
    call DBaseQtMarkProgramFinished
    call DBaseQtExec
    movl %eax, __dbase_exit_code
__dbase_program_cleanup_1:
    call DBaseConsoleShutdown
    push $__dbase_format_buffer
    call DBaseQtRuntimeShutdown
    addl $4, %esp
    pushl __dbase_exit_code
    call ExitProcess

.data

__dbase_text_0:
    .byte 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    .byte 71, 0
__dbase_output_debug_override:
    .long -1
__dbase_workstation_lazy_console_marker:
    .byte 68, 54, 52, 68, 66, 65, 83, 69, 95, 76, 65, 90, 89, 95, 67, 79, 78, 83, 79, 76, 69, 95, 86, 49, 0

.bss

__dbase_ffi_return:
    .d64_resq 1
__dbase_temp_number:
    .d64_resd 1
__dbase_temp_number_hi:
    .d64_resd 1
__dbase_int_cw:
    .d64_resw 1
__dbase_int_cw_trunc:
    .d64_resw 1
__dbase_call_number:
    .d64_resq 1
__dbase_format_buffer:
    .d64_resd 1
__dbase_exit_code:
    .d64_resd 1
__dbase_output_format_screen:
    .d64_resd 1
__dbase_output_debug_visible:
    .d64_resd 1
__dbase_console_number_len:
    .d64_resd 1
__dbase_text_1:
    .d64_resb 1

# Stage 462: WFM DLL-Runtime-Startup/Shutdown fuer PE32
.section $.text
.entry $__d64_wfm_entry
__d64_wfm_entry:
    movl $__dbase_wfm_qt_output_marker, %eax
    push $__dbase_format_buffer
    push $1
    push $0
    push $0
    push $__dbase_wfm_text_0
    call DBaseQtRuntimeStartup
    addl $20, %esp
    testl %eax, %eax
    jne __dbase_wfm_runtime_ready
    push $1
    call ExitProcess
__dbase_wfm_runtime_ready:
    call __dbase_wfm_proc___dbase_top_level__
    push $5
    push $__dbase_wfm_text_0
    call DBaseQtFormCreate
    addl $8, %esp
    movl %eax, __dbase_wfm_form
    push $0
    push $0
    pushl __dbase_wfm_form
    push $10
    push $__dbase_wfm_text_1
    call DBaseQtControlCreateEx
    addl $20, %esp
    movl %eax, __dbase_wfm_obj_THIS_PushButton1
    push $__dbase_wfm_proc_PushButton1_onClick
    push $7
    push $__dbase_wfm_text_2
    pushl __dbase_wfm_obj_THIS_PushButton1
    call DBaseQtObjectBindEvent
    addl $16, %esp
# WFM UI payload: binary, zlib, 566 bytes
    push $1
    push $566
    push $__dbase_wfm_external_ui_payload
    push $2
    push $__dbase_wfm_external_ui_slots
    call DBaseQtFormApplyExternalUi
    addl $20, %esp
    push $4
    push $51
    call __dbase_wfm_proc___init__
    addl $8, %esp
    pushl __dbase_wfm_form
    call DBaseQtFormOpen
    addl $4, %esp
    call __dbase_wfm_proc___main__
    call DBaseQtWfmModalParameter
    pushl %eax
    pushl __dbase_wfm_form
    call DBaseQtFormRun
    addl $8, %esp
    call __dbase_wfm_proc___del__
    push $__dbase_format_buffer
    call DBaseQtRuntimeShutdown
    addl $4, %esp
    push $0
    call ExitProcess

# Stage 133: WFM Event-/Methoden-Code
.section $.text

# ------------------------------------------------------------
# WFM PROCEDURE/FUNCTION MASCHINENCODE: __dbase_top_level__
# ------------------------------------------------------------
__dbase_wfm_proc___dbase_top_level__:
    movl $0, __dbase_wfm_local___dbase_top_level___a_type
    movl $0, __dbase_wfm_local___dbase_top_level___a_len
    fldz
    fstpl __dbase_wfm_local___dbase_top_level___a_num
    movl $0, __dbase_wfm_local___dbase_top_level___a_ptr
    movl $0, __dbase_wfm_local___dbase_top_level___c_type
    movl $0, __dbase_wfm_local___dbase_top_level___c_len
    fldz
    fstpl __dbase_wfm_local___dbase_top_level___c_num
    movl $0, __dbase_wfm_local___dbase_top_level___c_ptr
# Quellcode Zeile: 36
# ? "shell32.dll"
    push $1
    push $11
    push $__dbase_wfm_output_text_3
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 38
    fldz
    fstpl __dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_num
    movl $__dbase_wfm_flow_ffi_ansi_4, %eax
    movl %eax, __dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_ptr
    movl $__dbase_wfm_flow_ffi_ansi_6, %eax
    movl %eax, __dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_ptr
    movl $0, __dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_ptr
    movl $0, __dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_ptr
    fld1
    fstpl __dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_num
    cmpl $4, __dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_type
    je __dbase_wfm_flow_ffi_pointer_10
    fldl __dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_num
    fistps __dbase_temp_number
    pushl __dbase_temp_number
    jmp __dbase_wfm_flow_ffi_push_done_11
__dbase_wfm_flow_ffi_pointer_10:
    pushl __dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_ptr
__dbase_wfm_flow_ffi_push_done_11:
    pushl __dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_ptr
    pushl __dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_ptr
    pushl __dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_ptr
    pushl __dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_ptr
    cmpl $4, __dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_type
    je __dbase_wfm_flow_ffi_pointer_12
    fldl __dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_num
    fistps __dbase_temp_number
    pushl __dbase_temp_number
    jmp __dbase_wfm_flow_ffi_push_done_13
__dbase_wfm_flow_ffi_pointer_12:
    pushl __dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_ptr
__dbase_wfm_flow_ffi_push_done_13:
    call __dbase_ffi_shellexecute
    movl %eax, __dbase_ffi_return
    movl $0, __dbase_ffi_return+4
    fildl __dbase_ffi_return
    fstpl __dbase_wfm_mem_result_num
    movl $__dbase_wfm_mem_result_type, %eax
    movl $1, %edx
    call __dbase_wfm_assign_numeric_header
# Quellcode Zeile: 40
# ? result
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem_result_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 42
# local A = 9
    fldl __dbase_wfm_numconst_0
    fstpl __dbase_wfm_local___dbase_top_level___a_num
    movl $__dbase_wfm_local___dbase_top_level___a_type, %eax
    movl $1, %edx
    call __dbase_wfm_assign_numeric_header
# Quellcode Zeile: 43
# local C = 4
    fldl __dbase_wfm_numconst_1
    fstpl __dbase_wfm_local___dbase_top_level___c_num
    movl $__dbase_wfm_local___dbase_top_level___c_type, %eax
    movl $1, %edx
    call __dbase_wfm_assign_numeric_header
# Quellcode Zeile: 46
# STORE 123.45 TO xyz
    fldl __dbase_wfm_numconst_2
    fstpl __dbase_wfm_mem_xyz_num
    movl $__dbase_wfm_mem_xyz_type, %eax
    movl $2, %edx
    call __dbase_wfm_assign_numeric_header
# Quellcode Zeile: 48
    movl __dbase_wfm_mem_xyz_type, %edx
    cmpl $1, %edx
    je __dbase_wfm_flow_type_numeric_15
    cmpl $2, %edx
    je __dbase_wfm_flow_type_numeric_15
    cmpl $3, %edx
    je __dbase_wfm_flow_type_string_16
    cmpl $4, %edx
    je __dbase_wfm_flow_type_object_17
    cmpl $5, %edx
    je __dbase_wfm_flow_type_logical_18
    cmpl $6, %edx
    je __dbase_wfm_flow_type_date_19
    movl $85, %eax
    jmp __dbase_wfm_flow_type_ready_20
__dbase_wfm_flow_type_numeric_15:
    movl $78, %eax
    jmp __dbase_wfm_flow_type_ready_20
__dbase_wfm_flow_type_string_16:
    movl $67, %eax
    jmp __dbase_wfm_flow_type_ready_20
__dbase_wfm_flow_type_object_17:
    movl $79, %eax
    jmp __dbase_wfm_flow_type_ready_20
__dbase_wfm_flow_type_logical_18:
    movl $76, %eax
    jmp __dbase_wfm_flow_type_ready_20
__dbase_wfm_flow_type_date_19:
    movl $68, %eax
__dbase_wfm_flow_type_ready_20:
    cmpl $78, %eax
    jne __dbase_wfm_flow_type_slot_next_22
    movl $__dbase_wfm_output_text_4, %eax
    jmp __dbase_wfm_flow_type_slot_done_21
__dbase_wfm_flow_type_slot_next_22:
    cmpl $67, %eax
    jne __dbase_wfm_flow_type_slot_next_23
    movl $__dbase_wfm_output_text_5, %eax
    jmp __dbase_wfm_flow_type_slot_done_21
__dbase_wfm_flow_type_slot_next_23:
    cmpl $79, %eax
    jne __dbase_wfm_flow_type_slot_next_24
    movl $__dbase_wfm_output_text_6, %eax
    jmp __dbase_wfm_flow_type_slot_done_21
__dbase_wfm_flow_type_slot_next_24:
    cmpl $76, %eax
    jne __dbase_wfm_flow_type_slot_next_25
    movl $__dbase_wfm_output_text_7, %eax
    jmp __dbase_wfm_flow_type_slot_done_21
__dbase_wfm_flow_type_slot_next_25:
    cmpl $68, %eax
    jne __dbase_wfm_flow_type_slot_next_26
    movl $__dbase_wfm_output_text_8, %eax
    jmp __dbase_wfm_flow_type_slot_done_21
__dbase_wfm_flow_type_slot_next_26:
    movl $__dbase_wfm_output_text_9, %eax
__dbase_wfm_flow_type_slot_done_21:
    movl %eax, __dbase_wfm_mem___dbase_wfm_flow_type_print_14_ptr
    movl $1, __dbase_wfm_mem___dbase_wfm_flow_type_print_14_len
    movl $3, __dbase_wfm_mem___dbase_wfm_flow_type_print_14_type
# ? TYPE("xyz")
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem___dbase_wfm_flow_type_print_14_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 49
    movl __dbase_wfm_mem_xyz_type, %edx
    cmpl $1, %edx
    je __dbase_wfm_flow_type_numeric_28
    cmpl $2, %edx
    je __dbase_wfm_flow_type_numeric_28
    cmpl $3, %edx
    je __dbase_wfm_flow_type_string_29
    cmpl $4, %edx
    je __dbase_wfm_flow_type_object_30
    cmpl $5, %edx
    je __dbase_wfm_flow_type_logical_31
    cmpl $6, %edx
    je __dbase_wfm_flow_type_date_32
    movl $85, %eax
    jmp __dbase_wfm_flow_type_ready_33
__dbase_wfm_flow_type_numeric_28:
    movl $78, %eax
    jmp __dbase_wfm_flow_type_ready_33
__dbase_wfm_flow_type_string_29:
    movl $67, %eax
    jmp __dbase_wfm_flow_type_ready_33
__dbase_wfm_flow_type_object_30:
    movl $79, %eax
    jmp __dbase_wfm_flow_type_ready_33
__dbase_wfm_flow_type_logical_31:
    movl $76, %eax
    jmp __dbase_wfm_flow_type_ready_33
__dbase_wfm_flow_type_date_32:
    movl $68, %eax
__dbase_wfm_flow_type_ready_33:
    cmpl $78, %eax
    jne __dbase_wfm_flow_type_slot_next_35
    movl $__dbase_wfm_output_text_10, %eax
    jmp __dbase_wfm_flow_type_slot_done_34
__dbase_wfm_flow_type_slot_next_35:
    cmpl $67, %eax
    jne __dbase_wfm_flow_type_slot_next_36
    movl $__dbase_wfm_output_text_11, %eax
    jmp __dbase_wfm_flow_type_slot_done_34
__dbase_wfm_flow_type_slot_next_36:
    cmpl $79, %eax
    jne __dbase_wfm_flow_type_slot_next_37
    movl $__dbase_wfm_output_text_12, %eax
    jmp __dbase_wfm_flow_type_slot_done_34
__dbase_wfm_flow_type_slot_next_37:
    cmpl $76, %eax
    jne __dbase_wfm_flow_type_slot_next_38
    movl $__dbase_wfm_output_text_13, %eax
    jmp __dbase_wfm_flow_type_slot_done_34
__dbase_wfm_flow_type_slot_next_38:
    cmpl $68, %eax
    jne __dbase_wfm_flow_type_slot_next_39
    movl $__dbase_wfm_output_text_14, %eax
    jmp __dbase_wfm_flow_type_slot_done_34
__dbase_wfm_flow_type_slot_next_39:
    movl $__dbase_wfm_output_text_15, %eax
__dbase_wfm_flow_type_slot_done_34:
    movl %eax, __dbase_wfm_mem___dbase_wfm_flow_type_print_27_ptr
    movl $1, __dbase_wfm_mem___dbase_wfm_flow_type_print_27_len
    movl $3, __dbase_wfm_mem___dbase_wfm_flow_type_print_27_type
# ? VARTYPE(xyz)
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem___dbase_wfm_flow_type_print_27_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 51
# IF TYPE("xyz") == "N"
    movl __dbase_wfm_mem_xyz_type, %edx
    cmpl $1, %edx
    je __dbase_wfm_flow_type_numeric_42
    cmpl $2, %edx
    je __dbase_wfm_flow_type_numeric_42
    cmpl $3, %edx
    je __dbase_wfm_flow_type_string_43
    cmpl $4, %edx
    je __dbase_wfm_flow_type_object_44
    cmpl $5, %edx
    je __dbase_wfm_flow_type_logical_45
    cmpl $6, %edx
    je __dbase_wfm_flow_type_date_46
    movl $85, %eax
    jmp __dbase_wfm_flow_type_ready_47
__dbase_wfm_flow_type_numeric_42:
    movl $78, %eax
    jmp __dbase_wfm_flow_type_ready_47
__dbase_wfm_flow_type_string_43:
    movl $67, %eax
    jmp __dbase_wfm_flow_type_ready_47
__dbase_wfm_flow_type_object_44:
    movl $79, %eax
    jmp __dbase_wfm_flow_type_ready_47
__dbase_wfm_flow_type_logical_45:
    movl $76, %eax
    jmp __dbase_wfm_flow_type_ready_47
__dbase_wfm_flow_type_date_46:
    movl $68, %eax
__dbase_wfm_flow_type_ready_47:
    pushl %eax
    movl $78, %eax
    popl %ecx
    cmpl %eax, %ecx
    jne __dbase_wfm_flow_if_false_40
# Quellcode Zeile: 52
# ? "xyz ist numerisch"
    push $1
    push $17
    push $__dbase_wfm_output_text_16
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 53
__dbase_wfm_flow_if_false_40:
__dbase_wfm_flow_if_end_41:
# Quellcode Zeile: 55
# STORE "Hallo" TO xyz
    movl $__dbase_wfm_output_text_17, __dbase_wfm_mem_xyz_ptr
    movl $5, __dbase_wfm_mem_xyz_len
    movl $3, __dbase_wfm_mem_xyz_type
# Quellcode Zeile: 57
    movl __dbase_wfm_mem_xyz_type, %edx
    cmpl $1, %edx
    je __dbase_wfm_flow_type_numeric_49
    cmpl $2, %edx
    je __dbase_wfm_flow_type_numeric_49
    cmpl $3, %edx
    je __dbase_wfm_flow_type_string_50
    cmpl $4, %edx
    je __dbase_wfm_flow_type_object_51
    cmpl $5, %edx
    je __dbase_wfm_flow_type_logical_52
    cmpl $6, %edx
    je __dbase_wfm_flow_type_date_53
    movl $85, %eax
    jmp __dbase_wfm_flow_type_ready_54
__dbase_wfm_flow_type_numeric_49:
    movl $78, %eax
    jmp __dbase_wfm_flow_type_ready_54
__dbase_wfm_flow_type_string_50:
    movl $67, %eax
    jmp __dbase_wfm_flow_type_ready_54
__dbase_wfm_flow_type_object_51:
    movl $79, %eax
    jmp __dbase_wfm_flow_type_ready_54
__dbase_wfm_flow_type_logical_52:
    movl $76, %eax
    jmp __dbase_wfm_flow_type_ready_54
__dbase_wfm_flow_type_date_53:
    movl $68, %eax
__dbase_wfm_flow_type_ready_54:
    cmpl $78, %eax
    jne __dbase_wfm_flow_type_slot_next_56
    movl $__dbase_wfm_output_text_18, %eax
    jmp __dbase_wfm_flow_type_slot_done_55
__dbase_wfm_flow_type_slot_next_56:
    cmpl $67, %eax
    jne __dbase_wfm_flow_type_slot_next_57
    movl $__dbase_wfm_output_text_19, %eax
    jmp __dbase_wfm_flow_type_slot_done_55
__dbase_wfm_flow_type_slot_next_57:
    cmpl $79, %eax
    jne __dbase_wfm_flow_type_slot_next_58
    movl $__dbase_wfm_output_text_20, %eax
    jmp __dbase_wfm_flow_type_slot_done_55
__dbase_wfm_flow_type_slot_next_58:
    cmpl $76, %eax
    jne __dbase_wfm_flow_type_slot_next_59
    movl $__dbase_wfm_output_text_21, %eax
    jmp __dbase_wfm_flow_type_slot_done_55
__dbase_wfm_flow_type_slot_next_59:
    cmpl $68, %eax
    jne __dbase_wfm_flow_type_slot_next_60
    movl $__dbase_wfm_output_text_22, %eax
    jmp __dbase_wfm_flow_type_slot_done_55
__dbase_wfm_flow_type_slot_next_60:
    movl $__dbase_wfm_output_text_23, %eax
__dbase_wfm_flow_type_slot_done_55:
    movl %eax, __dbase_wfm_mem___dbase_wfm_flow_type_print_48_ptr
    movl $1, __dbase_wfm_mem___dbase_wfm_flow_type_print_48_len
    movl $3, __dbase_wfm_mem___dbase_wfm_flow_type_print_48_type
# ? TYPE("xyz")
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem___dbase_wfm_flow_type_print_48_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 58
    movl __dbase_wfm_mem_xyz_type, %edx
    cmpl $1, %edx
    je __dbase_wfm_flow_type_numeric_62
    cmpl $2, %edx
    je __dbase_wfm_flow_type_numeric_62
    cmpl $3, %edx
    je __dbase_wfm_flow_type_string_63
    cmpl $4, %edx
    je __dbase_wfm_flow_type_object_64
    cmpl $5, %edx
    je __dbase_wfm_flow_type_logical_65
    cmpl $6, %edx
    je __dbase_wfm_flow_type_date_66
    movl $85, %eax
    jmp __dbase_wfm_flow_type_ready_67
__dbase_wfm_flow_type_numeric_62:
    movl $78, %eax
    jmp __dbase_wfm_flow_type_ready_67
__dbase_wfm_flow_type_string_63:
    movl $67, %eax
    jmp __dbase_wfm_flow_type_ready_67
__dbase_wfm_flow_type_object_64:
    movl $79, %eax
    jmp __dbase_wfm_flow_type_ready_67
__dbase_wfm_flow_type_logical_65:
    movl $76, %eax
    jmp __dbase_wfm_flow_type_ready_67
__dbase_wfm_flow_type_date_66:
    movl $68, %eax
__dbase_wfm_flow_type_ready_67:
    cmpl $78, %eax
    jne __dbase_wfm_flow_type_slot_next_69
    movl $__dbase_wfm_output_text_24, %eax
    jmp __dbase_wfm_flow_type_slot_done_68
__dbase_wfm_flow_type_slot_next_69:
    cmpl $67, %eax
    jne __dbase_wfm_flow_type_slot_next_70
    movl $__dbase_wfm_output_text_25, %eax
    jmp __dbase_wfm_flow_type_slot_done_68
__dbase_wfm_flow_type_slot_next_70:
    cmpl $79, %eax
    jne __dbase_wfm_flow_type_slot_next_71
    movl $__dbase_wfm_output_text_26, %eax
    jmp __dbase_wfm_flow_type_slot_done_68
__dbase_wfm_flow_type_slot_next_71:
    cmpl $76, %eax
    jne __dbase_wfm_flow_type_slot_next_72
    movl $__dbase_wfm_output_text_27, %eax
    jmp __dbase_wfm_flow_type_slot_done_68
__dbase_wfm_flow_type_slot_next_72:
    cmpl $68, %eax
    jne __dbase_wfm_flow_type_slot_next_73
    movl $__dbase_wfm_output_text_28, %eax
    jmp __dbase_wfm_flow_type_slot_done_68
__dbase_wfm_flow_type_slot_next_73:
    movl $__dbase_wfm_output_text_29, %eax
__dbase_wfm_flow_type_slot_done_68:
    movl %eax, __dbase_wfm_mem___dbase_wfm_flow_type_print_61_ptr
    movl $1, __dbase_wfm_mem___dbase_wfm_flow_type_print_61_len
    movl $3, __dbase_wfm_mem___dbase_wfm_flow_type_print_61_type
# ? VARTYPE(xyz)
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem___dbase_wfm_flow_type_print_61_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 60
    movl $85, %eax
    cmpl $78, %eax
    jne __dbase_wfm_flow_type_slot_next_76
    movl $__dbase_wfm_output_text_30, %eax
    jmp __dbase_wfm_flow_type_slot_done_75
__dbase_wfm_flow_type_slot_next_76:
    cmpl $67, %eax
    jne __dbase_wfm_flow_type_slot_next_77
    movl $__dbase_wfm_output_text_31, %eax
    jmp __dbase_wfm_flow_type_slot_done_75
__dbase_wfm_flow_type_slot_next_77:
    cmpl $79, %eax
    jne __dbase_wfm_flow_type_slot_next_78
    movl $__dbase_wfm_output_text_32, %eax
    jmp __dbase_wfm_flow_type_slot_done_75
__dbase_wfm_flow_type_slot_next_78:
    cmpl $76, %eax
    jne __dbase_wfm_flow_type_slot_next_79
    movl $__dbase_wfm_output_text_33, %eax
    jmp __dbase_wfm_flow_type_slot_done_75
__dbase_wfm_flow_type_slot_next_79:
    cmpl $68, %eax
    jne __dbase_wfm_flow_type_slot_next_80
    movl $__dbase_wfm_output_text_34, %eax
    jmp __dbase_wfm_flow_type_slot_done_75
__dbase_wfm_flow_type_slot_next_80:
    movl $__dbase_wfm_output_text_35, %eax
__dbase_wfm_flow_type_slot_done_75:
    movl %eax, __dbase_wfm_mem___dbase_wfm_flow_type_print_74_ptr
    movl $1, __dbase_wfm_mem___dbase_wfm_flow_type_print_74_len
    movl $3, __dbase_wfm_mem___dbase_wfm_flow_type_print_74_type
# ? TYPE("unbekannt")
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem___dbase_wfm_flow_type_print_74_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
__dbase_wfm_flow_method_exit_1:
    ret
# END WFM PROCEDURE/FUNCTION: __dbase_top_level__


# ------------------------------------------------------------
# WFM PROCEDURE/FUNCTION MASCHINENCODE: __del__
# ------------------------------------------------------------
__dbase_wfm_proc___del__:
# Quellcode Zeile: 254
__dbase_wfm_flow_method_exit_81:
    ret
# END WFM PROCEDURE/FUNCTION: __del__


# ------------------------------------------------------------
# WFM PROCEDURE/FUNCTION MASCHINENCODE: __init__
# ------------------------------------------------------------
__dbase_wfm_proc___init__:
    movl 4(%esp), %eax
    movl %eax, __dbase_wfm_param___init___p1
    movl 8(%esp), %eax
    movl %eax, __dbase_wfm_param___init___p2
# Quellcode Zeile: 245
# ? "p1 = " + int(p1)
    push $0
    push $5
    push $__dbase_wfm_output_text_36
    call DBaseQtConsoleWrite
    addl $12, %esp
    push $1
    push $2
    push $__dbase_wfm_output_text_37
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 246
# ? "p2 = " + int(p2)
    push $0
    push $5
    push $__dbase_wfm_output_text_38
    call DBaseQtConsoleWrite
    addl $12, %esp
    push $1
    push $1
    push $__dbase_wfm_output_text_39
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 248
    movl __dbase_wfm_mem_xyz_type, %edx
    cmpl $1, %edx
    je __dbase_wfm_flow_type_numeric_84
    cmpl $2, %edx
    je __dbase_wfm_flow_type_numeric_84
    cmpl $3, %edx
    je __dbase_wfm_flow_type_string_85
    cmpl $4, %edx
    je __dbase_wfm_flow_type_object_86
    cmpl $5, %edx
    je __dbase_wfm_flow_type_logical_87
    cmpl $6, %edx
    je __dbase_wfm_flow_type_date_88
    movl $85, %eax
    jmp __dbase_wfm_flow_type_ready_89
__dbase_wfm_flow_type_numeric_84:
    movl $78, %eax
    jmp __dbase_wfm_flow_type_ready_89
__dbase_wfm_flow_type_string_85:
    movl $67, %eax
    jmp __dbase_wfm_flow_type_ready_89
__dbase_wfm_flow_type_object_86:
    movl $79, %eax
    jmp __dbase_wfm_flow_type_ready_89
__dbase_wfm_flow_type_logical_87:
    movl $76, %eax
    jmp __dbase_wfm_flow_type_ready_89
__dbase_wfm_flow_type_date_88:
    movl $68, %eax
__dbase_wfm_flow_type_ready_89:
    cmpl $78, %eax
    jne __dbase_wfm_flow_type_slot_next_91
    movl $__dbase_wfm_output_text_40, %eax
    jmp __dbase_wfm_flow_type_slot_done_90
__dbase_wfm_flow_type_slot_next_91:
    cmpl $67, %eax
    jne __dbase_wfm_flow_type_slot_next_92
    movl $__dbase_wfm_output_text_41, %eax
    jmp __dbase_wfm_flow_type_slot_done_90
__dbase_wfm_flow_type_slot_next_92:
    cmpl $79, %eax
    jne __dbase_wfm_flow_type_slot_next_93
    movl $__dbase_wfm_output_text_42, %eax
    jmp __dbase_wfm_flow_type_slot_done_90
__dbase_wfm_flow_type_slot_next_93:
    cmpl $76, %eax
    jne __dbase_wfm_flow_type_slot_next_94
    movl $__dbase_wfm_output_text_43, %eax
    jmp __dbase_wfm_flow_type_slot_done_90
__dbase_wfm_flow_type_slot_next_94:
    cmpl $68, %eax
    jne __dbase_wfm_flow_type_slot_next_95
    movl $__dbase_wfm_output_text_44, %eax
    jmp __dbase_wfm_flow_type_slot_done_90
__dbase_wfm_flow_type_slot_next_95:
    movl $__dbase_wfm_output_text_45, %eax
__dbase_wfm_flow_type_slot_done_90:
    movl %eax, __dbase_wfm_mem___dbase_wfm_flow_type_print_83_ptr
    movl $1, __dbase_wfm_mem___dbase_wfm_flow_type_print_83_len
    movl $3, __dbase_wfm_mem___dbase_wfm_flow_type_print_83_type
# ? TYPE("xyz")
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem___dbase_wfm_flow_type_print_83_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 249
    movl __dbase_wfm_mem_xyz_type, %edx
    cmpl $1, %edx
    je __dbase_wfm_flow_type_numeric_97
    cmpl $2, %edx
    je __dbase_wfm_flow_type_numeric_97
    cmpl $3, %edx
    je __dbase_wfm_flow_type_string_98
    cmpl $4, %edx
    je __dbase_wfm_flow_type_object_99
    cmpl $5, %edx
    je __dbase_wfm_flow_type_logical_100
    cmpl $6, %edx
    je __dbase_wfm_flow_type_date_101
    movl $85, %eax
    jmp __dbase_wfm_flow_type_ready_102
__dbase_wfm_flow_type_numeric_97:
    movl $78, %eax
    jmp __dbase_wfm_flow_type_ready_102
__dbase_wfm_flow_type_string_98:
    movl $67, %eax
    jmp __dbase_wfm_flow_type_ready_102
__dbase_wfm_flow_type_object_99:
    movl $79, %eax
    jmp __dbase_wfm_flow_type_ready_102
__dbase_wfm_flow_type_logical_100:
    movl $76, %eax
    jmp __dbase_wfm_flow_type_ready_102
__dbase_wfm_flow_type_date_101:
    movl $68, %eax
__dbase_wfm_flow_type_ready_102:
    cmpl $78, %eax
    jne __dbase_wfm_flow_type_slot_next_104
    movl $__dbase_wfm_output_text_46, %eax
    jmp __dbase_wfm_flow_type_slot_done_103
__dbase_wfm_flow_type_slot_next_104:
    cmpl $67, %eax
    jne __dbase_wfm_flow_type_slot_next_105
    movl $__dbase_wfm_output_text_47, %eax
    jmp __dbase_wfm_flow_type_slot_done_103
__dbase_wfm_flow_type_slot_next_105:
    cmpl $79, %eax
    jne __dbase_wfm_flow_type_slot_next_106
    movl $__dbase_wfm_output_text_48, %eax
    jmp __dbase_wfm_flow_type_slot_done_103
__dbase_wfm_flow_type_slot_next_106:
    cmpl $76, %eax
    jne __dbase_wfm_flow_type_slot_next_107
    movl $__dbase_wfm_output_text_49, %eax
    jmp __dbase_wfm_flow_type_slot_done_103
__dbase_wfm_flow_type_slot_next_107:
    cmpl $68, %eax
    jne __dbase_wfm_flow_type_slot_next_108
    movl $__dbase_wfm_output_text_50, %eax
    jmp __dbase_wfm_flow_type_slot_done_103
__dbase_wfm_flow_type_slot_next_108:
    movl $__dbase_wfm_output_text_51, %eax
__dbase_wfm_flow_type_slot_done_103:
    movl %eax, __dbase_wfm_mem___dbase_wfm_flow_type_print_96_ptr
    movl $1, __dbase_wfm_mem___dbase_wfm_flow_type_print_96_len
    movl $3, __dbase_wfm_mem___dbase_wfm_flow_type_print_96_type
# ? VARTYPE(xyz)
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem___dbase_wfm_flow_type_print_96_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 251
__dbase_wfm_flow_method_exit_82:
    ret
# END WFM PROCEDURE/FUNCTION: __init__


# ------------------------------------------------------------
# WFM PROCEDURE/FUNCTION MASCHINENCODE: __main__
# ------------------------------------------------------------
__dbase_wfm_proc___main__:
# Quellcode Zeile: 257
    movl $7, %eax
__dbase_wfm_flow_method_exit_109:
    ret
# END WFM PROCEDURE/FUNCTION: __main__


# ------------------------------------------------------------
# WFM PROCEDURE/FUNCTION MASCHINENCODE: CheckLower
# ------------------------------------------------------------
__dbase_wfm_proc_CheckLower:
    movl 4(%esp), %eax
    movl %eax, __dbase_wfm_param_CheckLower_c
    movl $3, __dbase_wfm_mem___wfm_arg_CheckLower_c_type
    movl __dbase_wfm_param_CheckLower_c, %eax
    movl %eax, __dbase_wfm_mem___wfm_arg_CheckLower_c_ptr
    movl 8(%esp), %eax
    movl %eax, __dbase_wfm_mem___wfm_arg_CheckLower_c_len
# Quellcode Zeile: 342
    cmpl $3, __dbase_wfm_mem___wfm_arg_CheckLower_c_type
    je __dbase_wfm_flow_char_case_valid_111
    fldz
    jmp __dbase_wfm_flow_char_case_end_112
__dbase_wfm_flow_char_case_valid_111:
    pushl __dbase_wfm_mem___wfm_arg_CheckLower_c_len
    pushl __dbase_wfm_mem___wfm_arg_CheckLower_c_ptr
    call DBaseCharIsLowerUtf8
    addl $8, %esp
    movl %eax, __dbase_temp_number
    filds __dbase_temp_number
__dbase_wfm_flow_char_case_end_112:
    fistps __dbase_temp_number
    movl __dbase_temp_number, %eax
__dbase_wfm_flow_method_exit_110:
    ret
# END WFM PROCEDURE/FUNCTION: CheckLower


# ------------------------------------------------------------
# WFM PROCEDURE/FUNCTION MASCHINENCODE: PushButton1_onClick
# ------------------------------------------------------------
__dbase_wfm_proc_PushButton1_onClick:
    movl 4(%esp), %eax
    movl %eax, __dbase_wfm_param_PushButton1_onClick_Sender
# Quellcode Zeile: 274
# STORE 101.42 TO Ausdruck
    fldl __dbase_wfm_numconst_3
    fstpl __dbase_wfm_mem_Ausdruck_num
    movl $__dbase_wfm_mem_Ausdruck_type, %eax
    movl $2, %edx
    call __dbase_wfm_assign_numeric_header
# Quellcode Zeile: 275
# Ausdruck = 101.42
    fldl __dbase_wfm_numconst_3
    fstpl __dbase_wfm_mem_Ausdruck_num
    movl $__dbase_wfm_mem_Ausdruck_type, %eax
    movl $2, %edx
    call __dbase_wfm_assign_numeric_header
# Quellcode Zeile: 276
# ? Ausdruck
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem_Ausdruck_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 277
# STORE INT(Ausdruck) TO Ausdruck
    cmpl $1, __dbase_wfm_mem_Ausdruck_type
    je __dbase_wfm_int_numeric_0
    cmpl $2, __dbase_wfm_mem_Ausdruck_type
    je __dbase_wfm_int_numeric_0
    movl $__dbase_wfm_mem_Ausdruck_type, %eax
    movl $0, %edx
    call __dbase_wfm_assign_numeric_header
    jmp __dbase_wfm_int_done_0
__dbase_wfm_int_numeric_0:
    fldl __dbase_wfm_mem_Ausdruck_num
    subl $8, %esp
    fnstcw (%esp)
    movl (%esp), %eax
    orl $0x0C00, %eax
    movl %eax, 4(%esp)
    fldcw 4(%esp)
    frndint
    fldcw (%esp)
    addl $8, %esp
    fstpl __dbase_wfm_mem_Ausdruck_num
    movl $1, __dbase_wfm_mem_Ausdruck_type
    movl $0, __dbase_wfm_mem_Ausdruck_len
    movl $0, __dbase_wfm_mem_Ausdruck_ptr
__dbase_wfm_int_done_0:
# Quellcode Zeile: 278
# ? Ausdruck
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem_Ausdruck_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 279
# ? "1: " + 101.42
    push $0
    push $3
    push $__dbase_wfm_output_text_52
    call DBaseQtConsoleWrite
    addl $12, %esp
    push $1
    push $6
    push $__dbase_wfm_output_text_53
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 280
# ? "2: " + INT(101.42)
    push $0
    push $3
    push $__dbase_wfm_output_text_54
    call DBaseQtConsoleWrite
    addl $12, %esp
    push $1
    push $3
    push $__dbase_wfm_output_text_55
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 281
# ? "3: " + Ausdruck
    push $0
    push $3
    push $__dbase_wfm_output_text_56
    call DBaseQtConsoleWrite
    addl $12, %esp
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem_Ausdruck_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 282
# STORE "Zeichenstring" TO SpeicherVar
    movl $__dbase_wfm_output_text_57, __dbase_wfm_mem_SpeicherVar_ptr
    movl $13, __dbase_wfm_mem_SpeicherVar_len
    movl $3, __dbase_wfm_mem_SpeicherVar_type
# Quellcode Zeile: 283
# ? "4: " + SpeicherVar
    push $0
    push $3
    push $__dbase_wfm_output_text_58
    call DBaseQtConsoleWrite
    addl $12, %esp
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem_SpeicherVar_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 284
    cmpl $3, __dbase_wfm_mem_SpeicherVar_type
    je __wfm_upper_1_valid
    push $13
    call ExitProcess
__wfm_upper_1_valid:
    fldl __dbase_wfm_numconst_4
    fstpl __dbase_wfm_mem___string_arg_2_num
    movl $__dbase_wfm_mem___string_arg_2_type, %eax
    movl $2, %edx
    call __dbase_wfm_assign_numeric_header
    fldl __dbase_wfm_numconst_5
    fstpl __dbase_wfm_mem___string_arg_3_num
    movl $__dbase_wfm_mem___string_arg_3_type, %eax
    movl $2, %edx
    call __dbase_wfm_assign_numeric_header
    movl __dbase_wfm_mem_SpeicherVar_len, %eax
    movl %eax, %ecx
    addl %ecx, %eax
    addl %ecx, %eax
    addl $1, %eax
    pushl %eax
    call __dbase_malloc
    addl $4, %esp
    testl %eax, %eax
    jne __wfm_upper_4_allocated
    push $8
    call ExitProcess
__wfm_upper_4_allocated:
    movl %eax, __dbase_wfm_mem___string_arg_4_ptr
    movl __dbase_wfm_mem_SpeicherVar_len, %eax
    movl %eax, %ecx
    addl %ecx, %eax
    addl %ecx, %eax
    addl $1, %eax
    push $__dbase_wfm_mem___string_arg_3_num
    push $__dbase_wfm_mem___string_arg_2_num
    pushl __dbase_wfm_mem_SpeicherVar_len
    pushl __dbase_wfm_mem_SpeicherVar_ptr
    pushl %eax
    pushl __dbase_wfm_mem___string_arg_4_ptr
    call DBaseUtf8SubstringUpper
    addl $24, %esp
    cmpl $-1, %eax
    jne __wfm_upper_4_converted
    push $13
    call ExitProcess
__wfm_upper_4_converted:
    movl %eax, __dbase_wfm_mem___string_arg_4_len
    movl $3, __dbase_wfm_mem___string_arg_4_type
# ? "5: " + !($(SpeicherVar, 8, 6))
    push $0
    push $3
    push $__dbase_wfm_output_text_59
    call DBaseQtConsoleWrite
    addl $12, %esp
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem___string_arg_4_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 285
# TestAndNotXor()
    call __dbase_wfm_proc_TestAndNotXor
# Quellcode Zeile: 287
    push $19
    call GetSystemMetrics
    testl %eax, %eax
    setne %al
    movzbl %al, %eax
    movl %eax, __dbase_temp_number
    filds __dbase_temp_number
    fstpl __dbase_wfm_mem_HatMaus_num
    movl $__dbase_wfm_mem_HatMaus_type, %eax
    movl $1, %edx
    call __dbase_wfm_assign_numeric_header
# Quellcode Zeile: 288
# IF HatMaus = 1
    fldl __dbase_wfm_mem_HatMaus_num
    fld1
    fucomip %st1, %st0
    fstp %st0
    jne __dbase_wfm_flow_if_false_115
# Quellcode Zeile: 289
# ? "Eine Maus ist vorhanden."
    push $1
    push $24
    push $__dbase_wfm_output_text_60
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 290
    jmp __dbase_wfm_flow_if_end_116
__dbase_wfm_flow_if_false_115:
# Quellcode Zeile: 291
# ? "Keine Maus erkannt."
    push $1
    push $19
    push $__dbase_wfm_output_text_61
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 292
__dbase_wfm_flow_if_end_116:
# Quellcode Zeile: 293
# IF ismouse() .AND. HatMaus = 1
    push $19
    call GetSystemMetrics
    testl %eax, %eax
    setne %al
    movzbl %al, %eax
    movl %eax, __dbase_temp_number
    filds __dbase_temp_number
    fldz
    fucomip %st1, %st0
    fstp %st0
    je __dbase_wfm_flow_if_false_117
    fldl __dbase_wfm_mem_HatMaus_num
    fld1
    fucomip %st1, %st0
    fstp %st0
    jne __dbase_wfm_flow_if_false_117
# Quellcode Zeile: 294
# ? "Maus kann verwendet werden."
    push $1
    push $27
    push $__dbase_wfm_output_text_62
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 295
__dbase_wfm_flow_if_false_117:
__dbase_wfm_flow_if_end_118:
# Quellcode Zeile: 296
    push $19
    call GetSystemMetrics
    testl %eax, %eax
    setne %al
    movzbl %al, %eax
    movl %eax, __dbase_temp_number
    filds __dbase_temp_number
    fstpl __dbase_wfm_mem___wfm_ismouse_print_num
# ? ismouse()
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem___wfm_ismouse_print_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 299
    subl $12, %esp
    movl $0, (%esp)
    movl $0, 4(%esp)
    movl $0, 8(%esp)
    leal (%esp), %eax
    push $8
    pushl %eax
    push $0
    call GetRawInputDeviceList
    cmpl $4294967295, %eax
    je __dbase_wfm_flow_iskeyboard_119_done
    movl (%esp), %edx
    testl %edx, %edx
    jz __dbase_wfm_flow_iskeyboard_119_done
    cmpl $536870911, %edx
    ja __dbase_wfm_flow_iskeyboard_119_done
    shll $3, %edx
    push $4
    push $12288
    pushl %edx
    push $0
    call VirtualAlloc
    testl %eax, %eax
    jz __dbase_wfm_flow_iskeyboard_119_done
    movl %eax, 4(%esp)
    leal (%esp), %edx
    push $8
    pushl %edx
    pushl %eax
    call GetRawInputDeviceList
    cmpl $4294967295, %eax
    je __dbase_wfm_flow_iskeyboard_119_release
    testl %eax, %eax
    jz __dbase_wfm_flow_iskeyboard_119_release
    movl %eax, %ecx
    movl 4(%esp), %edx
__dbase_wfm_flow_iskeyboard_119_scan:
    cmpl $1, 4(%edx)
    je __dbase_wfm_flow_iskeyboard_119_present
    addl $8, %edx
    decl %ecx
    jnz __dbase_wfm_flow_iskeyboard_119_scan
    jmp __dbase_wfm_flow_iskeyboard_119_release
__dbase_wfm_flow_iskeyboard_119_present:
    movl $1, 8(%esp)
__dbase_wfm_flow_iskeyboard_119_release:
    movl 4(%esp), %eax
    push $32768
    push $0
    pushl %eax
    call VirtualFree
__dbase_wfm_flow_iskeyboard_119_done:
    movl 8(%esp), %eax
    addl $12, %esp
    movl %eax, __dbase_temp_number
    filds __dbase_temp_number
    fstpl __dbase_wfm_mem_HatTastatur_num
    movl $__dbase_wfm_mem_HatTastatur_type, %eax
    movl $1, %edx
    call __dbase_wfm_assign_numeric_header
# Quellcode Zeile: 300
# IF HatTastatur = 1
    fldl __dbase_wfm_mem_HatTastatur_num
    fld1
    fucomip %st1, %st0
    fstp %st0
    jne __dbase_wfm_flow_if_false_120
# Quellcode Zeile: 301
# ? "Eine Tastatur ist vorhanden."
    push $1
    push $28
    push $__dbase_wfm_output_text_63
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 302
    jmp __dbase_wfm_flow_if_end_121
__dbase_wfm_flow_if_false_120:
# Quellcode Zeile: 303
# ? "Keine Tastatur erkannt."
    push $1
    push $23
    push $__dbase_wfm_output_text_64
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 304
__dbase_wfm_flow_if_end_121:
# Quellcode Zeile: 305
# IF iskeyboard() .AND. ismouse()
    subl $12, %esp
    movl $0, (%esp)
    movl $0, 4(%esp)
    movl $0, 8(%esp)
    leal (%esp), %eax
    push $8
    pushl %eax
    push $0
    call GetRawInputDeviceList
    cmpl $4294967295, %eax
    je __dbase_wfm_flow_iskeyboard_124_done
    movl (%esp), %edx
    testl %edx, %edx
    jz __dbase_wfm_flow_iskeyboard_124_done
    cmpl $536870911, %edx
    ja __dbase_wfm_flow_iskeyboard_124_done
    shll $3, %edx
    push $4
    push $12288
    pushl %edx
    push $0
    call VirtualAlloc
    testl %eax, %eax
    jz __dbase_wfm_flow_iskeyboard_124_done
    movl %eax, 4(%esp)
    leal (%esp), %edx
    push $8
    pushl %edx
    pushl %eax
    call GetRawInputDeviceList
    cmpl $4294967295, %eax
    je __dbase_wfm_flow_iskeyboard_124_release
    testl %eax, %eax
    jz __dbase_wfm_flow_iskeyboard_124_release
    movl %eax, %ecx
    movl 4(%esp), %edx
__dbase_wfm_flow_iskeyboard_124_scan:
    cmpl $1, 4(%edx)
    je __dbase_wfm_flow_iskeyboard_124_present
    addl $8, %edx
    decl %ecx
    jnz __dbase_wfm_flow_iskeyboard_124_scan
    jmp __dbase_wfm_flow_iskeyboard_124_release
__dbase_wfm_flow_iskeyboard_124_present:
    movl $1, 8(%esp)
__dbase_wfm_flow_iskeyboard_124_release:
    movl 4(%esp), %eax
    push $32768
    push $0
    pushl %eax
    call VirtualFree
__dbase_wfm_flow_iskeyboard_124_done:
    movl 8(%esp), %eax
    addl $12, %esp
    movl %eax, __dbase_temp_number
    filds __dbase_temp_number
    fldz
    fucomip %st1, %st0
    fstp %st0
    je __dbase_wfm_flow_if_false_122
    push $19
    call GetSystemMetrics
    testl %eax, %eax
    setne %al
    movzbl %al, %eax
    movl %eax, __dbase_temp_number
    filds __dbase_temp_number
    fldz
    fucomip %st1, %st0
    fstp %st0
    je __dbase_wfm_flow_if_false_122
# Quellcode Zeile: 306
# ? "Maus und Tastatur sind vorhanden."
    push $1
    push $33
    push $__dbase_wfm_output_text_65
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 307
__dbase_wfm_flow_if_false_122:
__dbase_wfm_flow_if_end_123:
# Quellcode Zeile: 308
# IF .NOT. iskeyboard()
    subl $12, %esp
    movl $0, (%esp)
    movl $0, 4(%esp)
    movl $0, 8(%esp)
    leal (%esp), %eax
    push $8
    pushl %eax
    push $0
    call GetRawInputDeviceList
    cmpl $4294967295, %eax
    je __dbase_wfm_flow_iskeyboard_128_done
    movl (%esp), %edx
    testl %edx, %edx
    jz __dbase_wfm_flow_iskeyboard_128_done
    cmpl $536870911, %edx
    ja __dbase_wfm_flow_iskeyboard_128_done
    shll $3, %edx
    push $4
    push $12288
    pushl %edx
    push $0
    call VirtualAlloc
    testl %eax, %eax
    jz __dbase_wfm_flow_iskeyboard_128_done
    movl %eax, 4(%esp)
    leal (%esp), %edx
    push $8
    pushl %edx
    pushl %eax
    call GetRawInputDeviceList
    cmpl $4294967295, %eax
    je __dbase_wfm_flow_iskeyboard_128_release
    testl %eax, %eax
    jz __dbase_wfm_flow_iskeyboard_128_release
    movl %eax, %ecx
    movl 4(%esp), %edx
__dbase_wfm_flow_iskeyboard_128_scan:
    cmpl $1, 4(%edx)
    je __dbase_wfm_flow_iskeyboard_128_present
    addl $8, %edx
    decl %ecx
    jnz __dbase_wfm_flow_iskeyboard_128_scan
    jmp __dbase_wfm_flow_iskeyboard_128_release
__dbase_wfm_flow_iskeyboard_128_present:
    movl $1, 8(%esp)
__dbase_wfm_flow_iskeyboard_128_release:
    movl 4(%esp), %eax
    push $32768
    push $0
    pushl %eax
    call VirtualFree
__dbase_wfm_flow_iskeyboard_128_done:
    movl 8(%esp), %eax
    addl $12, %esp
    movl %eax, __dbase_temp_number
    filds __dbase_temp_number
    fldz
    fucomip %st1, %st0
    fstp %st0
    jne __dbase_wfm_flow_if_false_125
__dbase_wfm_flow_not_true_127:
# Quellcode Zeile: 309
# ? "Keine Tastatur gefunden."
    push $1
    push $24
    push $__dbase_wfm_output_text_66
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 310
__dbase_wfm_flow_if_false_125:
__dbase_wfm_flow_if_end_126:
# Quellcode Zeile: 311
    subl $12, %esp
    movl $0, (%esp)
    movl $0, 4(%esp)
    movl $0, 8(%esp)
    leal (%esp), %eax
    push $8
    pushl %eax
    push $0
    call GetRawInputDeviceList
    cmpl $4294967295, %eax
    je __dbase_wfm_flow_iskeyboard_129_done
    movl (%esp), %edx
    testl %edx, %edx
    jz __dbase_wfm_flow_iskeyboard_129_done
    cmpl $536870911, %edx
    ja __dbase_wfm_flow_iskeyboard_129_done
    shll $3, %edx
    push $4
    push $12288
    pushl %edx
    push $0
    call VirtualAlloc
    testl %eax, %eax
    jz __dbase_wfm_flow_iskeyboard_129_done
    movl %eax, 4(%esp)
    leal (%esp), %edx
    push $8
    pushl %edx
    pushl %eax
    call GetRawInputDeviceList
    cmpl $4294967295, %eax
    je __dbase_wfm_flow_iskeyboard_129_release
    testl %eax, %eax
    jz __dbase_wfm_flow_iskeyboard_129_release
    movl %eax, %ecx
    movl 4(%esp), %edx
__dbase_wfm_flow_iskeyboard_129_scan:
    cmpl $1, 4(%edx)
    je __dbase_wfm_flow_iskeyboard_129_present
    addl $8, %edx
    decl %ecx
    jnz __dbase_wfm_flow_iskeyboard_129_scan
    jmp __dbase_wfm_flow_iskeyboard_129_release
__dbase_wfm_flow_iskeyboard_129_present:
    movl $1, 8(%esp)
__dbase_wfm_flow_iskeyboard_129_release:
    movl 4(%esp), %eax
    push $32768
    push $0
    pushl %eax
    call VirtualFree
__dbase_wfm_flow_iskeyboard_129_done:
    movl 8(%esp), %eax
    addl $12, %esp
    movl %eax, __dbase_temp_number
    filds __dbase_temp_number
    fstpl __dbase_wfm_mem___wfm_iskeyboard_print_num
# ? iskeyboard()
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem___wfm_iskeyboard_print_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 314
# STORE 'A' TO Zeichen
    movl $__dbase_wfm_output_text_67, __dbase_wfm_mem_Zeichen_ptr
    movl $1, __dbase_wfm_mem_Zeichen_len
    movl $3, __dbase_wfm_mem_Zeichen_type
# Quellcode Zeile: 315
# IF ISUPPER(Zeichen)
    cmpl $3, __dbase_wfm_mem_Zeichen_type
    je __dbase_wfm_flow_char_case_valid_132
    fldz
    jmp __dbase_wfm_flow_char_case_end_133
__dbase_wfm_flow_char_case_valid_132:
    pushl __dbase_wfm_mem_Zeichen_len
    pushl __dbase_wfm_mem_Zeichen_ptr
    call DBaseCharIsUpperUtf8
    addl $8, %esp
    movl %eax, __dbase_temp_number
    filds __dbase_temp_number
__dbase_wfm_flow_char_case_end_133:
    fldz
    fucomip %st1, %st0
    fstp %st0
    je __dbase_wfm_flow_if_false_130
# Quellcode Zeile: 316
# ? "Grossbuchstabe erkannt"
    push $1
    push $22
    push $__dbase_wfm_output_text_68
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 317
__dbase_wfm_flow_if_false_130:
__dbase_wfm_flow_if_end_131:
# Quellcode Zeile: 318
# IF CheckLower('z')
    push $1
    push $__dbase_wfm_text_69
    call __dbase_wfm_proc_CheckLower
    addl $8, %esp
    movl %eax, __dbase_temp_number
    filds __dbase_temp_number
    fldz
    fucomip %st1, %st0
    fstp %st0
    je __dbase_wfm_flow_if_false_135
# Quellcode Zeile: 319
# ? "Kleinbuchstabe erkannt"
    push $1
    push $22
    push $__dbase_wfm_output_text_70
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 320
__dbase_wfm_flow_if_false_135:
__dbase_wfm_flow_if_end_136:
# Quellcode Zeile: 322
    movl $__dbase_wfm_output_text_71, __dbase_wfm_mem___wfm_text_literal_5_ptr
    movl $10, __dbase_wfm_mem___wfm_text_literal_5_len
    movl $3, __dbase_wfm_mem___wfm_text_literal_5_type
    cmpl $3, __dbase_wfm_mem___wfm_text_literal_5_type
    je __dbase_wfm_flow_len_valid_137
    xorl %ecx, %ecx
    jmp __dbase_wfm_flow_len_skip_140
__dbase_wfm_flow_len_valid_137:
    pushl %esi
    movl __dbase_wfm_mem___wfm_text_literal_5_ptr, %esi
    movl __dbase_wfm_mem___wfm_text_literal_5_len, %edx
    xorl %ecx, %ecx
__dbase_wfm_flow_len_loop_139:
    testl %esi, %esi
    je __dbase_wfm_flow_len_finish_141
    testl %edx, %edx
    jz __dbase_wfm_flow_len_finish_141
    movzbl (%esi), %eax
    andl $192, %eax
    cmpl $128, %eax
    je len___dbase_wfm_flow_len_loop_139_continuation
    incl %ecx
len___dbase_wfm_flow_len_loop_139_continuation:
    incl %esi
    decl %edx
    jmp __dbase_wfm_flow_len_loop_139
__dbase_wfm_flow_len_finish_141:
    popl %esi
__dbase_wfm_flow_len_skip_140:
    movl %ecx, __dbase_temp_number
    filds __dbase_temp_number
    fstpl __dbase_wfm_mem___wfm_len_6_num
# ? LEN("Ein String")
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem___wfm_len_6_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 325
# STORE "   Hallo Welt   " TO Text
    movl $__dbase_wfm_output_text_72, __dbase_wfm_mem_Text_ptr
    movl $16, __dbase_wfm_mem_Text_len
    movl $3, __dbase_wfm_mem_Text_type
# Quellcode Zeile: 327
    cmpl $3, __dbase_wfm_mem_Text_type
    je __dbase_wfm_flow_len_valid_142
    xorl %ecx, %ecx
    jmp __dbase_wfm_flow_len_skip_145
__dbase_wfm_flow_len_valid_142:
    pushl %esi
    movl __dbase_wfm_mem_Text_ptr, %esi
    movl __dbase_wfm_mem_Text_len, %edx
    xorl %ecx, %ecx
__dbase_wfm_flow_len_loop_144:
    testl %esi, %esi
    je __dbase_wfm_flow_len_finish_146
    testl %edx, %edx
    jz __dbase_wfm_flow_len_finish_146
    movzbl (%esi), %eax
    andl $192, %eax
    cmpl $128, %eax
    je len___dbase_wfm_flow_len_loop_144_continuation
    incl %ecx
len___dbase_wfm_flow_len_loop_144_continuation:
    incl %esi
    decl %edx
    jmp __dbase_wfm_flow_len_loop_144
__dbase_wfm_flow_len_finish_146:
    popl %esi
__dbase_wfm_flow_len_skip_145:
    movl %ecx, __dbase_temp_number
    filds __dbase_temp_number
    fstpl __dbase_wfm_mem___wfm_len_7_num
# ? LEN(Text)
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem___wfm_len_7_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 330
    cmpl $3, __dbase_wfm_mem_Text_type
    je __dbase_wfm_flow_ltrim_valid_147
    movl $__dbase_wfm_output_text_74, __dbase_wfm_mem___wfm_ltrim_8_ptr
    movl $0, __dbase_wfm_mem___wfm_ltrim_8_len
    movl $3, __dbase_wfm_mem___wfm_ltrim_8_type
    jmp __dbase_wfm_flow_ltrim_done_148
__dbase_wfm_flow_ltrim_valid_147:
    movl __dbase_wfm_mem_Text_len, %eax
    incl %eax
    pushl %eax
    call __dbase_malloc
    addl $4, %esp
    testl %eax, %eax
    jne __dbase_wfm_flow_trim_ltrim_149_allocated
    push $8
    call ExitProcess
__dbase_wfm_flow_trim_ltrim_149_allocated:
    movl %eax, __dbase_wfm_mem___wfm_ltrim_8_ptr
    pushl %esi
    pushl %edi
    movl __dbase_wfm_mem_Text_ptr, %esi
    movl %esi, %edi
    movl __dbase_wfm_mem_Text_len, %eax
    addl %eax, %edi
__dbase_wfm_flow_trim_ltrim_149_left_loop:
    cmpl %edi, %esi
    jae __dbase_wfm_flow_trim_ltrim_149_left_done
    movb (%esi), %al
    cmpb $32, %al
    jne __dbase_wfm_flow_trim_ltrim_149_left_done
__dbase_wfm_flow_trim_ltrim_149_left_advance:
    incl %esi
    jmp __dbase_wfm_flow_trim_ltrim_149_left_loop
__dbase_wfm_flow_trim_ltrim_149_left_done:
    subl %esi, %edi
    movl %edi, __dbase_wfm_mem___wfm_ltrim_8_len
    movl $3, __dbase_wfm_mem___wfm_ltrim_8_type
    movl %edi, %ecx
    movl __dbase_wfm_mem___wfm_ltrim_8_ptr, %edi
__dbase_wfm_flow_trim_ltrim_149_copy_loop:
    testl %ecx, %ecx
    je __dbase_wfm_flow_trim_ltrim_149_copy_done
    movzbl (%esi), %eax
    movb %al, (%edi)
    incl %esi
    incl %edi
    decl %ecx
    jmp __dbase_wfm_flow_trim_ltrim_149_copy_loop
__dbase_wfm_flow_trim_ltrim_149_copy_done:
    movb $0, (%edi)
    popl %edi
    popl %esi
__dbase_wfm_flow_ltrim_done_148:
# ? "[" + LTRIM(Text) + "]"
    push $0
    push $1
    push $__dbase_wfm_output_text_73
    call DBaseQtConsoleWrite
    addl $12, %esp
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem___wfm_ltrim_8_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $0
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
    push $1
    push $1
    push $__dbase_wfm_output_text_75
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 333
    cmpl $3, __dbase_wfm_mem_Text_type
    je __dbase_wfm_flow_trim_valid_150
    movl $__dbase_wfm_output_text_77, __dbase_wfm_mem___wfm_trim_9_ptr
    movl $0, __dbase_wfm_mem___wfm_trim_9_len
    movl $3, __dbase_wfm_mem___wfm_trim_9_type
    jmp __dbase_wfm_flow_trim_done_151
__dbase_wfm_flow_trim_valid_150:
    movl __dbase_wfm_mem_Text_len, %eax
    incl %eax
    pushl %eax
    call __dbase_malloc
    addl $4, %esp
    testl %eax, %eax
    jne __dbase_wfm_flow_trim_trim_152_allocated
    push $8
    call ExitProcess
__dbase_wfm_flow_trim_trim_152_allocated:
    movl %eax, __dbase_wfm_mem___wfm_trim_9_ptr
    pushl %esi
    pushl %edi
    movl __dbase_wfm_mem_Text_ptr, %esi
    movl %esi, %edi
    movl __dbase_wfm_mem_Text_len, %eax
    addl %eax, %edi
__dbase_wfm_flow_trim_trim_152_left_loop:
    cmpl %edi, %esi
    jae __dbase_wfm_flow_trim_trim_152_left_done
    movb (%esi), %al
    cmpb $32, %al
    je __dbase_wfm_flow_trim_trim_152_left_advance
    cmpb $9, %al
    je __dbase_wfm_flow_trim_trim_152_left_advance
    cmpb $10, %al
    je __dbase_wfm_flow_trim_trim_152_left_advance
    cmpb $8, %al
    je __dbase_wfm_flow_trim_trim_152_left_advance
    cmpb $13, %al
    jne __dbase_wfm_flow_trim_trim_152_left_done
__dbase_wfm_flow_trim_trim_152_left_advance:
    incl %esi
    jmp __dbase_wfm_flow_trim_trim_152_left_loop
__dbase_wfm_flow_trim_trim_152_left_done:
__dbase_wfm_flow_trim_trim_152_right_loop:
    cmpl %esi, %edi
    jbe __dbase_wfm_flow_trim_trim_152_right_done
    movb -1(%edi), %al
    cmpb $32, %al
    je __dbase_wfm_flow_trim_trim_152_right_retreat
    cmpb $9, %al
    je __dbase_wfm_flow_trim_trim_152_right_retreat
    cmpb $10, %al
    je __dbase_wfm_flow_trim_trim_152_right_retreat
    cmpb $8, %al
    je __dbase_wfm_flow_trim_trim_152_right_retreat
    cmpb $13, %al
    jne __dbase_wfm_flow_trim_trim_152_right_done
__dbase_wfm_flow_trim_trim_152_right_retreat:
    decl %edi
    jmp __dbase_wfm_flow_trim_trim_152_right_loop
__dbase_wfm_flow_trim_trim_152_right_done:
    subl %esi, %edi
    movl %edi, __dbase_wfm_mem___wfm_trim_9_len
    movl $3, __dbase_wfm_mem___wfm_trim_9_type
    movl %edi, %ecx
    movl __dbase_wfm_mem___wfm_trim_9_ptr, %edi
__dbase_wfm_flow_trim_trim_152_copy_loop:
    testl %ecx, %ecx
    je __dbase_wfm_flow_trim_trim_152_copy_done
    movzbl (%esi), %eax
    movb %al, (%edi)
    incl %esi
    incl %edi
    decl %ecx
    jmp __dbase_wfm_flow_trim_trim_152_copy_loop
__dbase_wfm_flow_trim_trim_152_copy_done:
    movb $0, (%edi)
    popl %edi
    popl %esi
__dbase_wfm_flow_trim_done_151:
# ? "[" + TRIM(Text) + "]"
    push $0
    push $1
    push $__dbase_wfm_output_text_76
    call DBaseQtConsoleWrite
    addl $12, %esp
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem___wfm_trim_9_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $0
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
    push $1
    push $1
    push $__dbase_wfm_output_text_78
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 336
    cmpl $3, __dbase_wfm_mem_Text_type
    je __dbase_wfm_flow_trim_valid_153
    movl $__dbase_wfm_output_text_79, __dbase_wfm_mem___wfm_trim_10_ptr
    movl $0, __dbase_wfm_mem___wfm_trim_10_len
    movl $3, __dbase_wfm_mem___wfm_trim_10_type
    jmp __dbase_wfm_flow_trim_done_154
__dbase_wfm_flow_trim_valid_153:
    movl __dbase_wfm_mem_Text_len, %eax
    incl %eax
    pushl %eax
    call __dbase_malloc
    addl $4, %esp
    testl %eax, %eax
    jne __dbase_wfm_flow_trim_trim_155_allocated
    push $8
    call ExitProcess
__dbase_wfm_flow_trim_trim_155_allocated:
    movl %eax, __dbase_wfm_mem___wfm_trim_10_ptr
    pushl %esi
    pushl %edi
    movl __dbase_wfm_mem_Text_ptr, %esi
    movl %esi, %edi
    movl __dbase_wfm_mem_Text_len, %eax
    addl %eax, %edi
__dbase_wfm_flow_trim_trim_155_left_loop:
    cmpl %edi, %esi
    jae __dbase_wfm_flow_trim_trim_155_left_done
    movb (%esi), %al
    cmpb $32, %al
    je __dbase_wfm_flow_trim_trim_155_left_advance
    cmpb $9, %al
    je __dbase_wfm_flow_trim_trim_155_left_advance
    cmpb $10, %al
    je __dbase_wfm_flow_trim_trim_155_left_advance
    cmpb $8, %al
    je __dbase_wfm_flow_trim_trim_155_left_advance
    cmpb $13, %al
    jne __dbase_wfm_flow_trim_trim_155_left_done
__dbase_wfm_flow_trim_trim_155_left_advance:
    incl %esi
    jmp __dbase_wfm_flow_trim_trim_155_left_loop
__dbase_wfm_flow_trim_trim_155_left_done:
__dbase_wfm_flow_trim_trim_155_right_loop:
    cmpl %esi, %edi
    jbe __dbase_wfm_flow_trim_trim_155_right_done
    movb -1(%edi), %al
    cmpb $32, %al
    je __dbase_wfm_flow_trim_trim_155_right_retreat
    cmpb $9, %al
    je __dbase_wfm_flow_trim_trim_155_right_retreat
    cmpb $10, %al
    je __dbase_wfm_flow_trim_trim_155_right_retreat
    cmpb $8, %al
    je __dbase_wfm_flow_trim_trim_155_right_retreat
    cmpb $13, %al
    jne __dbase_wfm_flow_trim_trim_155_right_done
__dbase_wfm_flow_trim_trim_155_right_retreat:
    decl %edi
    jmp __dbase_wfm_flow_trim_trim_155_right_loop
__dbase_wfm_flow_trim_trim_155_right_done:
    subl %esi, %edi
    movl %edi, __dbase_wfm_mem___wfm_trim_10_len
    movl $3, __dbase_wfm_mem___wfm_trim_10_type
    movl %edi, %ecx
    movl __dbase_wfm_mem___wfm_trim_10_ptr, %edi
__dbase_wfm_flow_trim_trim_155_copy_loop:
    testl %ecx, %ecx
    je __dbase_wfm_flow_trim_trim_155_copy_done
    movzbl (%esi), %eax
    movb %al, (%edi)
    incl %esi
    incl %edi
    decl %ecx
    jmp __dbase_wfm_flow_trim_trim_155_copy_loop
__dbase_wfm_flow_trim_trim_155_copy_done:
    movb $0, (%edi)
    popl %edi
    popl %esi
__dbase_wfm_flow_trim_done_154:
    movl $__dbase_wfm_mem___wfm_trim_10_type, %eax
    movl $__dbase_wfm_mem_Ergebnis_type, %edx
    call __dbase_wfm_copy_variant
# Quellcode Zeile: 337
    cmpl $3, __dbase_wfm_mem_Ergebnis_type
    je __dbase_wfm_flow_len_valid_156
    xorl %ecx, %ecx
    jmp __dbase_wfm_flow_len_skip_159
__dbase_wfm_flow_len_valid_156:
    pushl %esi
    movl __dbase_wfm_mem_Ergebnis_ptr, %esi
    movl __dbase_wfm_mem_Ergebnis_len, %edx
    xorl %ecx, %ecx
__dbase_wfm_flow_len_loop_158:
    testl %esi, %esi
    je __dbase_wfm_flow_len_finish_160
    testl %edx, %edx
    jz __dbase_wfm_flow_len_finish_160
    movzbl (%esi), %eax
    andl $192, %eax
    cmpl $128, %eax
    je len___dbase_wfm_flow_len_loop_158_continuation
    incl %ecx
len___dbase_wfm_flow_len_loop_158_continuation:
    incl %esi
    decl %edx
    jmp __dbase_wfm_flow_len_loop_158
__dbase_wfm_flow_len_finish_160:
    popl %esi
__dbase_wfm_flow_len_skip_159:
    movl %ecx, __dbase_temp_number
    filds __dbase_temp_number
    fstpl __dbase_wfm_mem___wfm_len_11_num
# ? LEN(Ergebnis)
    push $__dbase_wfm_format_result
    pushl __dbase_format_buffer
    push $__dbase_wfm_mem___wfm_len_11_type
    call DBaseWfmFormatValue
    addl $12, %esp
    push $1
    pushl __dbase_wfm_format_result_len
    pushl __dbase_wfm_format_result
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 339
__dbase_wfm_flow_method_exit_114:
    ret
# END WFM PROCEDURE/FUNCTION: PushButton1_onClick


# ------------------------------------------------------------
# WFM PROCEDURE/FUNCTION MASCHINENCODE: TestAndNotXor
# ------------------------------------------------------------
__dbase_wfm_proc_TestAndNotXor:
# Quellcode Zeile: 260
# IF A > 0 .AND. C < 10
    fldl __dbase_wfm_mem_A_num
    fldz
    fucomip %st1, %st0
    fstp %st0
    jae __dbase_wfm_flow_if_false_162
    fldl __dbase_wfm_mem_C_num
    fldl __dbase_wfm_numconst_6
    fucomip %st1, %st0
    fstp %st0
    jbe __dbase_wfm_flow_if_false_162
# Quellcode Zeile: 261
# ? "Beide Bedingungen erfüllt"
    push $1
    push $26
    push $__dbase_wfm_output_text_80
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 262
    jmp __dbase_wfm_flow_if_end_163
__dbase_wfm_flow_if_false_162:
# Quellcode Zeile: 263
# ? "Bedingung nicht erfüllt"
    push $1
    push $24
    push $__dbase_wfm_output_text_81
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 264
__dbase_wfm_flow_if_end_163:
# Quellcode Zeile: 265
# IF .NOT. (A = 0 .OR. C >= 10)
    fldl __dbase_wfm_mem_A_num
    fldz
    fucomip %st1, %st0
    fstp %st0
    je __dbase_wfm_flow_or_true_167
__dbase_wfm_flow_not_true_168:
    fldl __dbase_wfm_mem_C_num
    fldl __dbase_wfm_numconst_6
    fucomip %st1, %st0
    fstp %st0
    ja __dbase_wfm_flow_not_true_166
__dbase_wfm_flow_or_true_167:
    jmp __dbase_wfm_flow_if_false_164
__dbase_wfm_flow_not_true_166:
# Quellcode Zeile: 266
# ? "NOT und OR funktionieren"
    push $1
    push $24
    push $__dbase_wfm_output_text_82
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 267
__dbase_wfm_flow_if_false_164:
__dbase_wfm_flow_if_end_165:
# Quellcode Zeile: 268
# IF (A > 0) .XOR. (C < 0)
    fldl __dbase_wfm_mem_A_num
    fldz
    fucomip %st1, %st0
    fstp %st0
    jae __dbase_wfm_flow_xor_left_false_171
    fldl __dbase_wfm_mem_C_num
    fldz
    fucomip %st1, %st0
    fstp %st0
    ja __dbase_wfm_flow_if_false_169
__dbase_wfm_flow_not_true_173:
    jmp __dbase_wfm_flow_xor_done_172
__dbase_wfm_flow_xor_left_false_171:
    fldl __dbase_wfm_mem_C_num
    fldz
    fucomip %st1, %st0
    fstp %st0
    jbe __dbase_wfm_flow_if_false_169
__dbase_wfm_flow_xor_done_172:
# Quellcode Zeile: 269
# ? "Genau eine Bedingung ist wahr"
    push $1
    push $29
    push $__dbase_wfm_output_text_83
    call DBaseQtConsoleWrite
    addl $12, %esp
# Quellcode Zeile: 270
__dbase_wfm_flow_if_false_169:
__dbase_wfm_flow_if_end_170:
# Quellcode Zeile: 271
__dbase_wfm_flow_method_exit_161:
    ret
# END WFM PROCEDURE/FUNCTION: TestAndNotXor

# Stage 460: shared dynamic variant helpers
.section $.text
__dbase_wfm_assign_numeric_header:
    movl %edx, (%eax)
    movl $0, 12(%eax)
    movl $0, 16(%eax)
    ret
__dbase_wfm_copy_variant:
    movl (%eax), %ecx
    movl %ecx, (%edx)
    fldl 4(%eax)
    fstpl 4(%edx)
    movl 12(%eax), %ecx
    movl %ecx, 12(%edx)
    movl 16(%eax), %ecx
    movl %ecx, 16(%edx)
    ret

# Stage 127 WFM initialized data
.section $.data
__dbase_wfm_qt_output_marker:
    .byte 68, 54, 52, 68, 66, 65, 83, 69, 95, 87, 70, 77, 95, 81, 84, 95, 79, 85, 84, 80, 85, 84, 95, 86, 49, 0
__dbase_wfm_text_0:
    .byte 70, 111, 114, 109, 49, 92, 48
__dbase_wfm_text_1:
    .byte 80, 85, 83, 72, 66, 85, 84, 84, 79, 78, 92, 48
__dbase_wfm_text_2:
    .byte 79, 110, 67, 108, 105, 99, 107, 92, 48
__dbase_wfm_text_69:
    .byte 122, 92, 48
__dbase_wfm_output_text_3:
    .byte 115, 104, 101, 108, 108, 51, 50, 46, 100, 108, 108
__dbase_wfm_flow_ffi_ansi_4:
    .byte 111, 112, 101, 110, 0
__dbase_wfm_flow_ffi_ansi_6:
    .byte 110, 111, 116, 101, 112, 97, 100, 46, 101, 120, 101, 0
__dbase_wfm_output_text_4:
    .byte 78
__dbase_wfm_output_text_5:
    .byte 67
__dbase_wfm_output_text_6:
    .byte 79
__dbase_wfm_output_text_7:
    .byte 76
__dbase_wfm_output_text_8:
    .byte 68
__dbase_wfm_output_text_9:
    .byte 85
__dbase_wfm_output_text_10:
    .byte 78
__dbase_wfm_output_text_11:
    .byte 67
__dbase_wfm_output_text_12:
    .byte 79
__dbase_wfm_output_text_13:
    .byte 76
__dbase_wfm_output_text_14:
    .byte 68
__dbase_wfm_output_text_15:
    .byte 85
__dbase_wfm_output_text_16:
    .byte 120, 121, 122, 32, 105, 115, 116, 32, 110, 117, 109, 101, 114, 105, 115, 99, 104
__dbase_wfm_output_text_17:
    .byte 72, 97, 108, 108, 111
__dbase_wfm_output_text_18:
    .byte 78
__dbase_wfm_output_text_19:
    .byte 67
__dbase_wfm_output_text_20:
    .byte 79
__dbase_wfm_output_text_21:
    .byte 76
__dbase_wfm_output_text_22:
    .byte 68
__dbase_wfm_output_text_23:
    .byte 85
__dbase_wfm_output_text_24:
    .byte 78
__dbase_wfm_output_text_25:
    .byte 67
__dbase_wfm_output_text_26:
    .byte 79
__dbase_wfm_output_text_27:
    .byte 76
__dbase_wfm_output_text_28:
    .byte 68
__dbase_wfm_output_text_29:
    .byte 85
__dbase_wfm_output_text_30:
    .byte 78
__dbase_wfm_output_text_31:
    .byte 67
__dbase_wfm_output_text_32:
    .byte 79
__dbase_wfm_output_text_33:
    .byte 76
__dbase_wfm_output_text_34:
    .byte 68
__dbase_wfm_output_text_35:
    .byte 85
__dbase_wfm_output_text_36:
    .byte 112, 49, 32, 61, 32
__dbase_wfm_output_text_37:
    .byte 53, 49
__dbase_wfm_output_text_38:
    .byte 112, 50, 32, 61, 32
__dbase_wfm_output_text_39:
    .byte 52
__dbase_wfm_output_text_40:
    .byte 78
__dbase_wfm_output_text_41:
    .byte 67
__dbase_wfm_output_text_42:
    .byte 79
__dbase_wfm_output_text_43:
    .byte 76
__dbase_wfm_output_text_44:
    .byte 68
__dbase_wfm_output_text_45:
    .byte 85
__dbase_wfm_output_text_46:
    .byte 78
__dbase_wfm_output_text_47:
    .byte 67
__dbase_wfm_output_text_48:
    .byte 79
__dbase_wfm_output_text_49:
    .byte 76
__dbase_wfm_output_text_50:
    .byte 68
__dbase_wfm_output_text_51:
    .byte 85
__dbase_wfm_output_text_52:
    .byte 49, 58, 32
__dbase_wfm_output_text_53:
    .byte 49, 48, 49, 46, 52, 50
__dbase_wfm_output_text_54:
    .byte 50, 58, 32
__dbase_wfm_output_text_55:
    .byte 49, 48, 49
__dbase_wfm_output_text_56:
    .byte 51, 58, 32
__dbase_wfm_output_text_57:
    .byte 90, 101, 105, 99, 104, 101, 110, 115, 116, 114, 105, 110, 103
__dbase_wfm_output_text_58:
    .byte 52, 58, 32
__dbase_wfm_output_text_59:
    .byte 53, 58, 32
__dbase_wfm_output_text_60:
    .byte 69, 105, 110, 101, 32, 77, 97, 117, 115, 32, 105, 115, 116, 32, 118, 111, 114, 104, 97, 110, 100, 101, 110, 46
__dbase_wfm_output_text_61:
    .byte 75, 101, 105, 110, 101, 32, 77, 97, 117, 115, 32, 101, 114, 107, 97, 110, 110, 116, 46
__dbase_wfm_output_text_62:
    .byte 77, 97, 117, 115, 32, 107, 97, 110, 110, 32, 118, 101, 114, 119, 101, 110, 100, 101, 116, 32, 119, 101, 114, 100, 101, 110, 46
__dbase_wfm_output_text_63:
    .byte 69, 105, 110, 101, 32, 84, 97, 115, 116, 97, 116, 117, 114, 32, 105, 115, 116, 32, 118, 111, 114, 104, 97, 110, 100, 101, 110, 46
__dbase_wfm_output_text_64:
    .byte 75, 101, 105, 110, 101, 32, 84, 97, 115, 116, 97, 116, 117, 114, 32, 101, 114, 107, 97, 110, 110, 116, 46
__dbase_wfm_output_text_65:
    .byte 77, 97, 117, 115, 32, 117, 110, 100, 32, 84, 97, 115, 116, 97, 116, 117, 114, 32, 115, 105, 110, 100, 32, 118, 111, 114, 104, 97, 110, 100, 101, 110, 46
__dbase_wfm_output_text_66:
    .byte 75, 101, 105, 110, 101, 32, 84, 97, 115, 116, 97, 116, 117, 114, 32, 103, 101, 102, 117, 110, 100, 101, 110, 46
__dbase_wfm_output_text_67:
    .byte 65
__dbase_wfm_output_text_68:
    .byte 71, 114, 111, 115, 115, 98, 117, 99, 104, 115, 116, 97, 98, 101, 32, 101, 114, 107, 97, 110, 110, 116
__dbase_wfm_output_text_70:
    .byte 75, 108, 101, 105, 110, 98, 117, 99, 104, 115, 116, 97, 98, 101, 32, 101, 114, 107, 97, 110, 110, 116
__dbase_wfm_output_text_71:
    .byte 69, 105, 110, 32, 83, 116, 114, 105, 110, 103
__dbase_wfm_output_text_72:
    .byte 32, 32, 32, 72, 97, 108, 108, 111, 32, 87, 101, 108, 116, 32, 32, 32
__dbase_wfm_output_text_73:
    .byte 91
__dbase_wfm_output_text_74:
    .byte 0
__dbase_wfm_output_text_75:
    .byte 93
__dbase_wfm_output_text_76:
    .byte 91
__dbase_wfm_output_text_77:
    .byte 0
__dbase_wfm_output_text_78:
    .byte 93
__dbase_wfm_output_text_79:
    .byte 0
__dbase_wfm_output_text_80:
    .byte 66, 101, 105, 100, 101, 32, 66, 101, 100, 105, 110, 103, 117, 110, 103, 101, 110, 32, 101, 114, 102, 195, 188, 108, 108, 116
__dbase_wfm_output_text_81:
    .byte 66, 101, 100, 105, 110, 103, 117, 110, 103, 32, 110, 105, 99, 104, 116, 32, 101, 114, 102, 195, 188, 108, 108, 116
__dbase_wfm_output_text_82:
    .byte 78, 79, 84, 32, 117, 110, 100, 32, 79, 82, 32, 102, 117, 110, 107, 116, 105, 111, 110, 105, 101, 114, 101, 110
__dbase_wfm_output_text_83:
    .byte 71, 101, 110, 97, 117, 32, 101, 105, 110, 101, 32, 66, 101, 100, 105, 110, 103, 117, 110, 103, 32, 105, 115, 116, 32, 119, 97, 104, 114

# Stage 456: one embedded JSON document per WFM FORM
__dbase_wfm_external_ui_slots:
    .long __dbase_wfm_form
    .long __dbase_wfm_obj_THIS_PushButton1
__dbase_wfm_external_ui_payload:
    %include "Form1.generated.pe32.payload.inc"
# Stage 460: fixed numeric WFM internal slot (__wfm_ismouse_print)
__dbase_wfm_mem___wfm_ismouse_print_type:
    .long 1
__dbase_wfm_mem___wfm_ismouse_print_num:
    .quad 0
__dbase_wfm_mem___wfm_ismouse_print_ptr:
    .long 0
__dbase_wfm_mem___wfm_ismouse_print_len:
    .long 0
# Stage 460: fixed numeric WFM internal slot (__wfm_iskeyboard_print)
__dbase_wfm_mem___wfm_iskeyboard_print_type:
    .long 1
__dbase_wfm_mem___wfm_iskeyboard_print_num:
    .quad 0
__dbase_wfm_mem___wfm_iskeyboard_print_ptr:
    .long 0
__dbase_wfm_mem___wfm_iskeyboard_print_len:
    .long 0
# Stage 460: fixed numeric WFM internal slot (__wfm_len_6)
__dbase_wfm_mem___wfm_len_6_type:
    .long 1
__dbase_wfm_mem___wfm_len_6_num:
    .quad 0
__dbase_wfm_mem___wfm_len_6_ptr:
    .long 0
__dbase_wfm_mem___wfm_len_6_len:
    .long 0
# Stage 460: fixed numeric WFM internal slot (__wfm_len_7)
__dbase_wfm_mem___wfm_len_7_type:
    .long 1
__dbase_wfm_mem___wfm_len_7_num:
    .quad 0
__dbase_wfm_mem___wfm_len_7_ptr:
    .long 0
__dbase_wfm_mem___wfm_len_7_len:
    .long 0
# Stage 460: fixed numeric WFM internal slot (__wfm_len_11)
__dbase_wfm_mem___wfm_len_11_type:
    .long 1
__dbase_wfm_mem___wfm_len_11_num:
    .quad 0
__dbase_wfm_mem___wfm_len_11_ptr:
    .long 0
__dbase_wfm_mem___wfm_len_11_len:
    .long 0

# Stage 192: WFM numeric STORE constants
__dbase_wfm_numconst_0:
    .long 0, 1075970048
__dbase_wfm_numconst_1:
    .long 0, 1074790400
__dbase_wfm_numconst_2:
    .long 3435973837, 1079958732
__dbase_wfm_numconst_3:
    .long 1202590843, 1079597793
__dbase_wfm_numconst_4:
    .long 0, 1075838976
__dbase_wfm_numconst_5:
    .long 0, 1075314688
__dbase_wfm_numconst_6:
    .long 0, 1076101120

# Stage 223 WFM zero-initialized storage
.section $.bss
__dbase_wfm_form:
    .d64_resd 1
__dbase_wfm_obj_THIS_PushButton1:
    .d64_resd 1

# Stage 223: WFM runtime parameter slots (.bss)
__dbase_wfm_param___init___p1:
    .d64_resd 1
__dbase_wfm_param___init___p2:
    .d64_resd 1
__dbase_wfm_param_CheckLower_c:
    .d64_resd 1
__dbase_wfm_param_PushButton1_onClick_Sender:
    .d64_resd 1

# Stage 449: shared WFM formatter's output (ptr, length)
__dbase_wfm_format_result:
    .d64_resd 1
__dbase_wfm_format_result_len:
    .d64_resd 1

# Stage 223: typed dBase WFM memory variables (.bss)
__dbase_wfm_mem_result_type:
    .d64_resd 1
__dbase_wfm_mem_result_num:
    .d64_resq 1
__dbase_wfm_mem_result_ptr:
    .d64_resd 1
__dbase_wfm_mem_result_len:
    .d64_resd 1
__dbase_wfm_mem_xyz_type:
    .d64_resd 1
__dbase_wfm_mem_xyz_num:
    .d64_resq 1
__dbase_wfm_mem_xyz_ptr:
    .d64_resd 1
__dbase_wfm_mem_xyz_len:
    .d64_resd 1
__dbase_wfm_mem_Ausdruck_type:
    .d64_resd 1
__dbase_wfm_mem_Ausdruck_num:
    .d64_resq 1
__dbase_wfm_mem_Ausdruck_ptr:
    .d64_resd 1
__dbase_wfm_mem_Ausdruck_len:
    .d64_resd 1
__dbase_wfm_mem_SpeicherVar_type:
    .d64_resd 1
__dbase_wfm_mem_SpeicherVar_num:
    .d64_resq 1
__dbase_wfm_mem_SpeicherVar_ptr:
    .d64_resd 1
__dbase_wfm_mem_SpeicherVar_len:
    .d64_resd 1
__dbase_wfm_mem_HatMaus_type:
    .d64_resd 1
__dbase_wfm_mem_HatMaus_num:
    .d64_resq 1
__dbase_wfm_mem_HatMaus_ptr:
    .d64_resd 1
__dbase_wfm_mem_HatMaus_len:
    .d64_resd 1
__dbase_wfm_mem_HatTastatur_type:
    .d64_resd 1
__dbase_wfm_mem_HatTastatur_num:
    .d64_resq 1
__dbase_wfm_mem_HatTastatur_ptr:
    .d64_resd 1
__dbase_wfm_mem_HatTastatur_len:
    .d64_resd 1
__dbase_wfm_mem_Zeichen_type:
    .d64_resd 1
__dbase_wfm_mem_Zeichen_num:
    .d64_resq 1
__dbase_wfm_mem_Zeichen_ptr:
    .d64_resd 1
__dbase_wfm_mem_Zeichen_len:
    .d64_resd 1
__dbase_wfm_mem_Text_type:
    .d64_resd 1
__dbase_wfm_mem_Text_num:
    .d64_resq 1
__dbase_wfm_mem_Text_ptr:
    .d64_resd 1
__dbase_wfm_mem_Text_len:
    .d64_resd 1
__dbase_wfm_mem_Ergebnis_type:
    .d64_resd 1
__dbase_wfm_mem_Ergebnis_num:
    .d64_resq 1
__dbase_wfm_mem_Ergebnis_ptr:
    .d64_resd 1
__dbase_wfm_mem_Ergebnis_len:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_type:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_num:
    .d64_resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_ptr:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_2_len:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_type:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_num:
    .d64_resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_ptr:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_3_len:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_type:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_num:
    .d64_resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_ptr:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_5_len:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_type:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_num:
    .d64_resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_ptr:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_7_len:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_type:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_num:
    .d64_resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_ptr:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_8_len:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_type:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_num:
    .d64_resq 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_ptr:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_ffi_arg_9_len:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_14_type:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_14_num:
    .d64_resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_14_ptr:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_14_len:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_27_type:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_27_num:
    .d64_resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_27_ptr:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_27_len:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_48_type:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_48_num:
    .d64_resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_48_ptr:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_48_len:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_61_type:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_61_num:
    .d64_resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_61_ptr:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_61_len:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_74_type:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_74_num:
    .d64_resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_74_ptr:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_74_len:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_83_type:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_83_num:
    .d64_resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_83_ptr:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_83_len:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_96_type:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_96_num:
    .d64_resq 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_96_ptr:
    .d64_resd 1
__dbase_wfm_mem___dbase_wfm_flow_type_print_96_len:
    .d64_resd 1
__dbase_wfm_mem___wfm_arg_CheckLower_c_type:
    .d64_resd 1
__dbase_wfm_mem___wfm_arg_CheckLower_c_num:
    .d64_resq 1
__dbase_wfm_mem___wfm_arg_CheckLower_c_ptr:
    .d64_resd 1
__dbase_wfm_mem___wfm_arg_CheckLower_c_len:
    .d64_resd 1
__dbase_wfm_mem___string_arg_1_type:
    .d64_resd 1
__dbase_wfm_mem___string_arg_1_num:
    .d64_resq 1
__dbase_wfm_mem___string_arg_1_ptr:
    .d64_resd 1
__dbase_wfm_mem___string_arg_1_len:
    .d64_resd 1
__dbase_wfm_mem___string_arg_2_type:
    .d64_resd 1
__dbase_wfm_mem___string_arg_2_num:
    .d64_resq 1
__dbase_wfm_mem___string_arg_2_ptr:
    .d64_resd 1
__dbase_wfm_mem___string_arg_2_len:
    .d64_resd 1
__dbase_wfm_mem___string_arg_3_type:
    .d64_resd 1
__dbase_wfm_mem___string_arg_3_num:
    .d64_resq 1
__dbase_wfm_mem___string_arg_3_ptr:
    .d64_resd 1
__dbase_wfm_mem___string_arg_3_len:
    .d64_resd 1
__dbase_wfm_mem___string_arg_4_type:
    .d64_resd 1
__dbase_wfm_mem___string_arg_4_num:
    .d64_resq 1
__dbase_wfm_mem___string_arg_4_ptr:
    .d64_resd 1
__dbase_wfm_mem___string_arg_4_len:
    .d64_resd 1
__dbase_wfm_mem___wfm_text_literal_5_type:
    .d64_resd 1
__dbase_wfm_mem___wfm_text_literal_5_num:
    .d64_resq 1
__dbase_wfm_mem___wfm_text_literal_5_ptr:
    .d64_resd 1
__dbase_wfm_mem___wfm_text_literal_5_len:
    .d64_resd 1
__dbase_wfm_mem___wfm_ltrim_8_type:
    .d64_resd 1
__dbase_wfm_mem___wfm_ltrim_8_num:
    .d64_resq 1
__dbase_wfm_mem___wfm_ltrim_8_ptr:
    .d64_resd 1
__dbase_wfm_mem___wfm_ltrim_8_len:
    .d64_resd 1
__dbase_wfm_mem___wfm_trim_9_type:
    .d64_resd 1
__dbase_wfm_mem___wfm_trim_9_num:
    .d64_resq 1
__dbase_wfm_mem___wfm_trim_9_ptr:
    .d64_resd 1
__dbase_wfm_mem___wfm_trim_9_len:
    .d64_resd 1
__dbase_wfm_mem___wfm_trim_10_type:
    .d64_resd 1
__dbase_wfm_mem___wfm_trim_10_num:
    .d64_resq 1
__dbase_wfm_mem___wfm_trim_10_ptr:
    .d64_resd 1
__dbase_wfm_mem___wfm_trim_10_len:
    .d64_resd 1
__dbase_wfm_mem_A_type:
    .d64_resd 1
__dbase_wfm_mem_A_num:
    .d64_resq 1
__dbase_wfm_mem_A_ptr:
    .d64_resd 1
__dbase_wfm_mem_A_len:
    .d64_resd 1
__dbase_wfm_mem_C_type:
    .d64_resd 1
__dbase_wfm_mem_C_num:
    .d64_resq 1
__dbase_wfm_mem_C_ptr:
    .d64_resd 1
__dbase_wfm_mem_C_len:
    .d64_resd 1
__dbase_wfm_local___dbase_top_level___a_type:
    .d64_resd 1
__dbase_wfm_local___dbase_top_level___a_num:
    .d64_resq 1
__dbase_wfm_local___dbase_top_level___a_ptr:
    .d64_resd 1
__dbase_wfm_local___dbase_top_level___a_len:
    .d64_resd 1
__dbase_wfm_local___dbase_top_level___c_type:
    .d64_resd 1
__dbase_wfm_local___dbase_top_level___c_num:
    .d64_resq 1
__dbase_wfm_local___dbase_top_level___c_ptr:
    .d64_resd 1
__dbase_wfm_local___dbase_top_level___c_len:
    .d64_resd 1
