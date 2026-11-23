%include "App001.generated.pe32.extern.inc"
bits 32

; __d64_dbase_startup_begin__
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
    mov dword ptr [__dbase_output_debug_override], 1
    mov dword ptr [__dbase_output_debug_visible], 1
    push 1
    call DBaseQtSetDebugVisible
    add esp, 4
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov dword ptr [__dbase_output_format_screen], 1
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    fld qword ptr [__dbase_num_0]
    fistp dword ptr [__dbase_background_arg_11_num]
    fld qword ptr [__dbase_num_1]
    fistp dword ptr [__dbase_background_arg_12_num]
    fld qword ptr [__dbase_num_2]
    fistp dword ptr [__dbase_background_arg_13_num]
    push dword ptr [__dbase_background_arg_13_num]
    push dword ptr [__dbase_background_arg_12_num]
    push dword ptr [__dbase_background_arg_11_num]
    call DBaseQtFillBackground
    add esp, 12
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push __dbase_output_debug_visible
    push dword ptr [__dbase_output_format_screen]
    push dword ptr [__dbase_output_debug_override]
    push 4
    push __dbase_text_1
    call DBaseQtRuntimeWrite
    add esp, 20
    ; O1: zentraler Ausgabeaufruf
__dbase_output_show_done_16:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_already_visible_18:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_console_15:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_done_17:
    push __dbase_output_debug_visible
    push dword ptr [__dbase_output_format_screen]
    push dword ptr [__dbase_output_debug_override]
    push 2
    push __dbase_text_2
    call DBaseQtRuntimeWrite
    add esp, 20
    ; O1: zentraler Ausgabeaufruf
__dbase_output_show_done_21:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_already_visible_23:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_console_20:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_done_22:
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    push __dbase_output_debug_visible
    push dword ptr [__dbase_output_format_screen]
    push dword ptr [__dbase_output_debug_override]
    push 5
    push __dbase_text_3
    call DBaseQtRuntimeWrite
    add esp, 20
    ; O1: zentraler Ausgabeaufruf
__dbase_output_show_done_26:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_already_visible_28:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_console_25:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_done_27:
    push __dbase_output_debug_visible
    push dword ptr [__dbase_output_format_screen]
    push dword ptr [__dbase_output_debug_override]
    push 2
    push __dbase_text_2
    call DBaseQtRuntimeWrite
    add esp, 20
    ; O1: zentraler Ausgabeaufruf
__dbase_output_show_done_31:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_already_visible_33:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_console_30:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_done_32:
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    mov eax, __dbase_text_4
    mov dword ptr [__dbase_exception_message_ptr], eax
    mov dword ptr [__dbase_exception_message_len], 10
    mov dword ptr [__dbase_exception_message_type], 2
    mov eax, __dbase_text_5
    mov dword ptr [__dbase_exception_class_ptr], eax
    mov dword ptr [__dbase_exception_class_len], 9
    mov dword ptr [__dbase_exception_class_type], 2
    mov dword ptr [__dbase_exception_id], 2
    mov dword ptr [__dbase_exception_code], 0
    mov ecx, dword ptr [__dbase_exception_message_len]
    inc ecx
    push ecx
    call __dbase_malloc
    add esp, 4
    mov dword ptr [__dbase_exception_cstr_ptr], eax
    test eax, eax
    je __dbase_exception_oom_34
    push dword ptr [__dbase_exception_message_len]
    push dword ptr [__dbase_exception_message_ptr]
    push eax
    call __dbase_memcpy
    add esp, 12
    mov edx, dword ptr [__dbase_exception_cstr_ptr]
    mov eax, dword ptr [__dbase_exception_message_len]
    mov byte ptr [edx+eax], 0
__dbase_exception_oom_34:
    call __dbase_cls_exception_create
    mov dword ptr [__dbase_exception_object_ptr], eax
    cmp dword ptr [__dbase_exception_object_ptr], 0
    je __dbase_exception_no_object_35
    push dword ptr [__dbase_exception_cstr_ptr]
    push dword ptr [__dbase_exception_object_ptr]
    call __dbase_cls_exception_set_message
    add esp, 8
__dbase_exception_no_object_35:
    cmp dword ptr [__dbase_exception_object_ptr], 0
    je __dbase_exception_message_ready_36
    push dword ptr [__dbase_exception_object_ptr]
    call __dbase_cls_exception_get_message
    add esp, 4
    test eax, eax
    jz __dbase_exception_message_ready_36
    mov dword ptr [__dbase_exception_message_ptr], eax
    push eax
    call __dbase_exc_strlenA
    add esp, 4
    mov dword ptr [__dbase_exception_message_len], eax
__dbase_exception_message_ready_36:
    cmp dword ptr [__dbase_exception_object_ptr], 0
    je __dbase_exception_track_done_37
    push 8
    call __dbase_malloc
    add esp, 4
    test eax, eax
    jz __dbase_exception_track_done_37
    mov ecx, dword ptr [__dbase_exception_object_ptr]
    mov dword ptr [eax], ecx
    mov ecx, dword ptr [__dbase_exception_objects_head]
    mov dword ptr [eax+4], ecx
    mov dword ptr [__dbase_exception_objects_head], eax
__dbase_exception_track_done_37:
    push dword ptr [__dbase_exception_cstr_ptr]
    call __dbase_exc_free
    add esp, 4
    mov dword ptr [__dbase_exception_cstr_ptr], 0
    jmp __dbase_catch_dispatch_8
    ; O1: entfallene Instruktion
__dbase_catch_dispatch_8:
    cmp dword ptr [__dbase_exception_id], 2
    je __dbase_catch_handler_38
    cmp dword ptr [__dbase_exception_id], 1
    je __dbase_catch_handler_38
    cmp dword ptr [__dbase_exception_id], 3
    je __dbase_catch_handler_38
    cmp dword ptr [__dbase_exception_id], 4
    jne __dbase_catch_next_39
    ; O1: entfallene Instruktion
__dbase_catch_handler_38:
    push esi
    push edi
    lea esi, [__dbase_exception_message_type]
    lea edi, [__dbase_caught_13_5_message_type]
    mov ecx, 10
    rep movsd
    pop edi
    pop esi
    mov eax, dword ptr [__dbase_exception_object_ptr]
    mov dword ptr [__dbase_caught_13_5_object_ptr], eax
    mov dword ptr [__dbase_exception_object_ptr], 0
    mov eax, dword ptr [__dbase_exception_id]
    mov dword ptr [__dbase_caught_13_5_id_num], eax
    fild dword ptr [__dbase_exception_code]
    fstp qword ptr [__dbase_caught_13_5_code_num]
    mov dword ptr [__dbase_caught_13_5_code_type], 1
    mov dword ptr [__dbase_exception_id], 0
    cmp dword ptr [__dbase_output_debug_override], -1
    jne __dbase_output_override_ready_40
    cmp dword ptr [__dbase_output_format_screen], 0
    je __dbase_output_console_41
    jmp __dbase_output_show_done_42
__dbase_output_override_ready_40:
    cmp dword ptr [__dbase_output_debug_override], 0
    je __dbase_output_console_41
__dbase_output_show_done_42:
    cmp dword ptr [__dbase_output_debug_visible], 0
    jne __dbase_output_already_visible_44
    mov dword ptr [__dbase_output_debug_visible], 1
    push 1
    call DBaseQtSetDebugVisible
    add esp, 4
__dbase_output_already_visible_44:
    push dword ptr [__dbase_caught_13_5_message_len]
    push dword ptr [__dbase_caught_13_5_message_ptr]
    call DBaseQtAppendDebug
    add esp, 8
    jmp __dbase_output_done_43
__dbase_output_console_41:
    push dword ptr [__dbase_caught_13_5_message_len]
    push dword ptr [__dbase_caught_13_5_message_ptr]
    call DBaseConsoleWrite
    add esp, 8
__dbase_output_done_43:
    push __dbase_output_debug_visible
    push dword ptr [__dbase_output_format_screen]
    push dword ptr [__dbase_output_debug_override]
    push 2
    push __dbase_text_2
    call DBaseQtRuntimeWrite
    add esp, 20
    ; O1: zentraler Ausgabeaufruf
__dbase_output_show_done_47:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_already_visible_49:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_console_46:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_done_48:
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    jmp __dbase_exception_finally_9
__dbase_catch_next_39:
__dbase_exception_finally_9:
    cmp dword ptr [__dbase_exception_id], 0
    je __dbase_exception_clear_50
    fninit
    jmp __dbase_catch_dispatch_5
__dbase_exception_clear_50:
__dbase_exception_after_10:
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    jmp __dbase_exception_finally_6
__dbase_catch_dispatch_5:
__dbase_exception_finally_6:
    push __dbase_output_debug_visible
    push dword ptr [__dbase_output_format_screen]
    push dword ptr [__dbase_output_debug_override]
    push 8
    push __dbase_text_6
    call DBaseQtRuntimeWrite
    add esp, 20
    ; O1: zentraler Ausgabeaufruf
__dbase_output_show_done_53:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_already_visible_55:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_console_52:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_done_54:
    push __dbase_output_debug_visible
    push dword ptr [__dbase_output_format_screen]
    push dword ptr [__dbase_output_debug_override]
    push 2
    push __dbase_text_2
    call DBaseQtRuntimeWrite
    add esp, 20
    ; O1: zentraler Ausgabeaufruf
__dbase_output_show_done_58:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_already_visible_60:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_console_57:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_done_59:
    call DBaseQtProcessEvents
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    cmp dword ptr [__dbase_exception_id], 0
    je __dbase_exception_clear_61
    fninit
    jmp __dbase_exception_unhandled_3
__dbase_exception_clear_61:
__dbase_exception_after_7:
    call DBaseQtShutdownRequested
    test eax, eax
    jne __dbase_program_cleanup_1
    jmp __dbase_exception_continue_4
__dbase_exception_unhandled_3:
    push __dbase_output_debug_visible
    push dword ptr [__dbase_output_format_screen]
    push dword ptr [__dbase_output_debug_override]
    push 24
    push __dbase_text_7
    call DBaseQtRuntimeWrite
    add esp, 20
    ; O1: zentraler Ausgabeaufruf
__dbase_output_show_done_64:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_already_visible_66:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_console_63:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_done_65:
    cmp dword ptr [__dbase_output_debug_override], -1
    jne __dbase_output_override_ready_67
    cmp dword ptr [__dbase_output_format_screen], 0
    je __dbase_output_console_68
    jmp __dbase_output_show_done_69
__dbase_output_override_ready_67:
    cmp dword ptr [__dbase_output_debug_override], 0
    je __dbase_output_console_68
__dbase_output_show_done_69:
    cmp dword ptr [__dbase_output_debug_visible], 0
    jne __dbase_output_already_visible_71
    mov dword ptr [__dbase_output_debug_visible], 1
    push 1
    call DBaseQtSetDebugVisible
    add esp, 4
__dbase_output_already_visible_71:
    push dword ptr [__dbase_exception_class_len]
    push dword ptr [__dbase_exception_class_ptr]
    call DBaseQtAppendDebug
    add esp, 8
    jmp __dbase_output_done_70
__dbase_output_console_68:
    push dword ptr [__dbase_exception_class_len]
    push dword ptr [__dbase_exception_class_ptr]
    call DBaseConsoleWrite
    add esp, 8
__dbase_output_done_70:
    push __dbase_output_debug_visible
    push dword ptr [__dbase_output_format_screen]
    push dword ptr [__dbase_output_debug_override]
    push 2
    push __dbase_text_8
    call DBaseQtRuntimeWrite
    add esp, 20
    ; O1: zentraler Ausgabeaufruf
__dbase_output_show_done_74:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_already_visible_76:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_console_73:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_done_75:
    cmp dword ptr [__dbase_output_debug_override], -1
    jne __dbase_output_override_ready_77
    cmp dword ptr [__dbase_output_format_screen], 0
    je __dbase_output_console_78
    jmp __dbase_output_show_done_79
__dbase_output_override_ready_77:
    cmp dword ptr [__dbase_output_debug_override], 0
    je __dbase_output_console_78
__dbase_output_show_done_79:
    cmp dword ptr [__dbase_output_debug_visible], 0
    jne __dbase_output_already_visible_81
    mov dword ptr [__dbase_output_debug_visible], 1
    push 1
    call DBaseQtSetDebugVisible
    add esp, 4
__dbase_output_already_visible_81:
    push dword ptr [__dbase_exception_message_len]
    push dword ptr [__dbase_exception_message_ptr]
    call DBaseQtAppendDebug
    add esp, 8
    jmp __dbase_output_done_80
__dbase_output_console_78:
    push dword ptr [__dbase_exception_message_len]
    push dword ptr [__dbase_exception_message_ptr]
    call DBaseConsoleWrite
    add esp, 8
__dbase_output_done_80:
    push __dbase_output_debug_visible
    push dword ptr [__dbase_output_format_screen]
    push dword ptr [__dbase_output_debug_override]
    push 2
    push __dbase_text_2
    call DBaseQtRuntimeWrite
    add esp, 20
    ; O1: zentraler Ausgabeaufruf
__dbase_output_show_done_84:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_already_visible_86:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_console_83:
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
    ; O1: zentraler Ausgabeaufruf
__dbase_output_done_85:
    call DBaseQtProcessEvents
__dbase_exception_continue_4:
    call DBaseQtMarkProgramFinished
    call DBaseQtExec
    mov dword ptr [__dbase_exit_code], eax
__dbase_program_cleanup_1:
    call __dbase_exception_cleanup_all
    call DBaseConsoleShutdown
    push __dbase_format_buffer
    call DBaseQtRuntimeShutdown
    add esp, 4
    push dword ptr [__dbase_exit_code]
    call ExitProcess
; __d64_dbase_startup_end__

__dbase_exception_cleanup_all:
    push ebp
    mov ebp, esp
    push ebx
__dbase_exception_cleanup_next:
    mov ebx, dword ptr [__dbase_exception_objects_head]
    test ebx, ebx
    jz __dbase_exception_cleanup_done
    mov eax, dword ptr [ebx+4]
    mov dword ptr [__dbase_exception_objects_head], eax
    mov eax, dword ptr [ebx]
    test eax, eax
    jz __dbase_exception_cleanup_node
    push eax
    call __dbase_exc_object_free
    add esp, 4
__dbase_exception_cleanup_node:
    push ebx
    call __dbase_exc_free
    add esp, 4
    jmp __dbase_exception_cleanup_next
__dbase_exception_cleanup_done:
    pop ebx
    mov esp, ebp
    pop ebp
    ret
; Stage 602: dBASE source methods / JitVmt C ABI
__dbase_cls_tobject___ini__:
    ret
__dbase_cls_tobject___del__:
    ret
__dbase_cls_tobject_free:
    push dword ptr [esp+4]
    call __dbase_obj_jit_object_free
    add esp, 4
    ret
__dbase_cls_tobject_freeinstance:
    push dword ptr [esp+4]
    call __dbase_obj_jit_object_instance_free
    add esp, 4
    ret
__dbase_cls_tobject_classtype:
    push dword ptr [esp+4]
    call __dbase_obj_jit_object_class_type
    add esp, 4
    ret
__dbase_cls_tobject_classparent:
    push dword ptr [esp+4]
    call __dbase_obj_jit_object_class_type
    add esp, 4
    push eax
    call __dbase_obj_jit_class_parent
    add esp, 4
    ret
__dbase_cls_tobject_classnameaddress:
    push dword ptr [esp+4]
    call __dbase_obj_jit_object_class_type
    add esp, 4
    push eax
    call __dbase_obj_jit_class_name
    add esp, 4
    ret
__dbase_cls_tobject_classname:
    push dword ptr [esp+4]
    call __dbase_obj_jit_object_class_type
    add esp, 4
    push eax
    call __dbase_obj_jit_class_name
    add esp, 4
    ret
__dbase_cls_tobject_instancesize:
    push dword ptr [esp+4]
    call __dbase_obj_jit_object_class_type
    add esp, 4
    push eax
    call __dbase_obj_jit_class_instance_size
    add esp, 4
    ret
__dbase_cls_tobject_inheritsfrom:
    push dword ptr [esp+8]
    push dword ptr [esp+8]
    call __dbase_obj_jit_inherits_from_object
    add esp, 8
    ret
__dbase_cls_exception_fields_init:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    mov edx, __dbase_cls_exception_default_message
    mov dword ptr [eax+4], edx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_exception_fields_done:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [ebp+8]
    cmp dword ptr [eax+8], 0
    je __dbase_cls_exception_fields_done_message_skip
    push dword ptr [eax+4]
    call __dbase_cls_api_LocalFree
__dbase_cls_exception_fields_done_message_skip:
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_exception_get_message:
    mov eax, dword ptr [esp+4]
    mov eax, dword ptr [eax+4]
    ret
__dbase_cls_exception_set_message:
    push ebp
    mov ebp, esp
    push ebx
    push __dbase_cls_empty
    push __dbase_cls_empty
    push dword ptr [ebp+12]
    call __dbase_cls_concat3
    add esp, 12
    mov ebx, eax
    mov eax, dword ptr [ebp+8]
    cmp dword ptr [eax+8], 0
    je __dbase_cls_exception_set_message_store
    push dword ptr [eax+4]
    call __dbase_cls_api_LocalFree
__dbase_cls_exception_set_message_store:
    mov eax, dword ptr [ebp+8]
    mov dword ptr [eax+4], ebx
    mov dword ptr [eax+8], 1
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_exception_get_code:
    mov eax, dword ptr [esp+4]
    mov eax, dword ptr [eax+12]
    ret
__dbase_cls_exception_set_code:
    mov eax, dword ptr [esp+4]
    mov edx, dword ptr [esp+8]
    mov dword ptr [eax+12], edx
    ret
global __dbase_cls_exception_create
__dbase_cls_exception_create:
    push __dbase_vmt_exception
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    ret
__dbase_cls_dbexception_fields_init:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_init
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_dbexception_fields_done:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_done
    add esp, 4
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_dbexception_create
__dbase_cls_dbexception_create:
    push __dbase_vmt_dbexception
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    ret
__dbase_cls_win32exception_fields_init:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_init
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_win32exception_fields_done:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_exception_fields_done
    add esp, 4
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_win32exception_create
__dbase_cls_win32exception_create:
    push __dbase_vmt_win32exception
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    ret
__dbase_cls_win32fileexception_fields_init:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_win32exception_fields_init
    add esp, 4
    mov eax, dword ptr [ebp+8]
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_win32fileexception_fields_done:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __dbase_cls_win32exception_fields_done
    add esp, 4
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_win32fileexception_create
__dbase_cls_win32fileexception_create:
    push __dbase_vmt_win32fileexception
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    ret
__dbase_cls_concat3:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov esi, dword ptr [ebp+8]
    mov edi, dword ptr [ebp+12]
    mov edx, dword ptr [ebp+16]
    test esi, esi
    jnz __dbase_cls_concat3_first
    mov esi, __dbase_cls_empty
__dbase_cls_concat3_first:
    test edi, edi
    jnz __dbase_cls_concat3_second
    mov edi, __dbase_cls_empty
__dbase_cls_concat3_second:
    test edx, edx
    jnz __dbase_cls_concat3_third
    mov edx, __dbase_cls_empty
__dbase_cls_concat3_third:
    push edx
    push esi
    call __dbase_cls_api_lstrlenA
    mov ebx, eax
    push edi
    call __dbase_cls_api_lstrlenA
    add ebx, eax
    push dword ptr [esp]
    call __dbase_cls_api_lstrlenA
    add ebx, eax
    add ebx, 1
    push ebx
    push 64
    call __dbase_cls_api_LocalAlloc
    mov ebx, eax
    test eax, eax
    jz __dbase_cls_concat3_done
    push esi
    push ebx
    call __dbase_cls_api_lstrcpyA
    push edi
    push ebx
    call __dbase_cls_api_lstrcatA
    push dword ptr [esp]
    push ebx
    call __dbase_cls_api_lstrcatA
__dbase_cls_concat3_done:
    add esp, 4
    mov eax, ebx
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret
__dbase_cls_u32toa:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    push 16
    push 64
    call __dbase_cls_api_LocalAlloc
    mov edi, eax
    test eax, eax
    jz __dbase_cls_u32toa32_done
    lea esi, [edi+15]
    mov byte ptr [esi], 0
    mov eax, dword ptr [ebp+8]
    mov ebx, 10
__dbase_cls_u32toa32_digits:
    xor edx, edx
    div ebx
    add edx, 48
    dec esi
    mov byte ptr [esi], dl
    test eax, eax
    jne __dbase_cls_u32toa32_digits
    mov edx, edi
__dbase_cls_u32toa32_copy:
    movzx ebx, byte ptr [esi]
    mov byte ptr [edx], bl
    inc esi
    inc edx
    test ebx, ebx
    jne __dbase_cls_u32toa32_copy
    mov eax, edi
__dbase_cls_u32toa32_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret
global __dbase_cls_tobject_create
__dbase_cls_tobject_create:
    push __dbase_vmt_tobject
    call __dbase_obj_jit_object_instance_new
    add esp, 4
    ret

section .data
; Stage 600: JitVmt headers: parent, name, instance_size, init, finalize, destroy
__dbase_cls_exception_default_message:
    db 69, 114, 114, 111, 114, 46, 0
__dbase_cls_empty:
    db 0
; Stage 670: shared VMT method tables
__dbase_class_object:
    dd __dbase_cls_tobject___del__
    dd __dbase_cls_tobject_free
    dd __dbase_cls_tobject_freeinstance
    dd __dbase_cls_tobject_classtype
    dd __dbase_cls_tobject_classparent
    dd __dbase_cls_tobject_classnameaddress
    dd __dbase_cls_tobject_classname
    dd __dbase_cls_tobject_instancesize
    dd __dbase_cls_tobject_inheritsfrom
global __dbase_vmt_tobject
__dbase_vmt_tobject:
    dd 0
    dd __dbase_vmt_tobject_name
    dd 0x80000004
    dd __dbase_cls_tobject___ini__
    dd 0
    dd __dbase_class_object
__dbase_vmt_tobject_name:
    db 84, 79, 98, 106, 101, 99, 116, 0
global __dbase_vmt_exception
__dbase_vmt_exception:
    dd __dbase_vmt_tobject
    dd __dbase_vmt_exception_name
    dd 0x80000014
    dd __dbase_cls_exception_fields_init
    dd __dbase_cls_exception_fields_done
    dd __dbase_class_object
__dbase_vmt_exception_name:
    db 69, 120, 99, 101, 112, 116, 105, 111, 110, 0
global __dbase_vmt_dbexception
__dbase_vmt_dbexception:
    dd __dbase_vmt_exception
    dd __dbase_vmt_dbexception_name
    dd 0x80000014
    dd __dbase_cls_dbexception_fields_init
    dd __dbase_cls_dbexception_fields_done
    dd __dbase_class_object
__dbase_vmt_dbexception_name:
    db 68, 98, 69, 120, 99, 101, 112, 116, 105, 111, 110, 0
global __dbase_vmt_win32exception
__dbase_vmt_win32exception:
    dd __dbase_vmt_exception
    dd __dbase_vmt_win32exception_name
    dd 0x80000014
    dd __dbase_cls_win32exception_fields_init
    dd __dbase_cls_win32exception_fields_done
    dd __dbase_class_object
__dbase_vmt_win32exception_name:
    db 87, 105, 110, 51, 50, 69, 120, 99, 101, 112, 116, 105, 111, 110, 0
global __dbase_vmt_win32fileexception
__dbase_vmt_win32fileexception:
    dd __dbase_vmt_win32exception
    dd __dbase_vmt_win32fileexception_name
    dd 0x80000014
    dd __dbase_cls_win32fileexception_fields_init
    dd __dbase_cls_win32fileexception_fields_done
    dd __dbase_class_object
__dbase_vmt_win32fileexception_name:
    db 87, 105, 110, 51, 50, 70, 105, 108, 101, 69, 120, 99, 101, 112, 116, 105, 111, 110, 0

__dbase_num_0:
    dd 0, 1072693248
__dbase_num_1:
    dd 0, 1076625408
__dbase_num_2:
    dd 0, 1080426496
__dbase_text_0:
    db 100, 66, 97, 115, 101, 32, 81, 116, 53, 32, 67, 111, 110, 115, 111, 108, 101, 32, 47, 32, 68, 69, 66, 85
    db 71, 0
__dbase_text_1:
    db 104, 105, 104, 105
__dbase_text_2:
    db 13, 10
__dbase_text_3:
    db 104, 97, 108, 246, 111
__dbase_text_4:
    db 69, 105, 110, 32, 70, 101, 104, 108, 101, 114
__dbase_text_5:
    db 69, 120, 99, 101, 112, 116, 105, 111, 110
__dbase_text_6:
    db 68, 97, 115, 32, 69, 110, 100, 101
__dbase_text_7:
    db 85, 110, 98, 101, 104, 97, 110, 100, 101, 108, 116, 101, 32, 69, 120, 99, 101, 112, 116, 105, 111, 110, 58, 32
__dbase_text_8:
    db 58, 32
__dbase_output_format_screen:
    dd 1
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
__dbase_output_debug_visible:
    resd 1
__dbase_console_number_len:
    resd 1
__dbase_exception_id:
    resd 1
__dbase_exception_code:
    resd 1
__dbase_caught_13_5_message_type:
    resd 1
__dbase_caught_13_5_message_num:
    resq 1
__dbase_caught_13_5_message_ptr:
    resd 1
__dbase_caught_13_5_message_len:
    resd 1
__dbase_caught_13_5_class_type:
    resd 1
__dbase_caught_13_5_class_num:
    resq 1
__dbase_caught_13_5_class_ptr:
    resd 1
__dbase_caught_13_5_class_len:
    resd 1
__dbase_caught_13_5_id_type:
    resd 1
__dbase_caught_13_5_id_num:
    resq 1
__dbase_caught_13_5_id_ptr:
    resd 1
__dbase_caught_13_5_id_len:
    resd 1
__dbase_caught_13_5_object_type:
    resd 1
__dbase_caught_13_5_object_num:
    resq 1
__dbase_caught_13_5_object_ptr:
    resd 1
__dbase_caught_13_5_object_len:
    resd 1
__dbase_caught_13_5_code_type:
    resd 1
__dbase_caught_13_5_code_num:
    resq 1
__dbase_caught_13_5_code_ptr:
    resd 1
__dbase_caught_13_5_code_len:
    resd 1
__dbase_background_arg_11_type:
    resd 1
__dbase_background_arg_11_num:
    resq 1
__dbase_background_arg_11_ptr:
    resd 1
__dbase_background_arg_11_len:
    resd 1
__dbase_background_arg_12_type:
    resd 1
__dbase_background_arg_12_num:
    resq 1
__dbase_background_arg_12_ptr:
    resd 1
__dbase_background_arg_12_len:
    resd 1
__dbase_background_arg_13_type:
    resd 1
__dbase_background_arg_13_num:
    resq 1
__dbase_background_arg_13_ptr:
    resd 1
__dbase_background_arg_13_len:
    resd 1
__dbase_exception_message_type:
    resd 1
__dbase_exception_message_num:
    resq 1
__dbase_exception_message_ptr:
    resd 1
__dbase_exception_message_len:
    resd 1
__dbase_exception_class_type:
    resd 1
__dbase_exception_class_num:
    resq 1
__dbase_exception_class_ptr:
    resd 1
__dbase_exception_class_len:
    resd 1
__dbase_exception_object_type:
    resd 1
__dbase_exception_object_num:
    resq 1
__dbase_exception_object_ptr:
    resd 1
__dbase_exception_object_len:
    resd 1
__dbase_exception_cstr_type:
    resd 1
__dbase_exception_cstr_num:
    resq 1
__dbase_exception_cstr_ptr:
    resd 1
__dbase_exception_cstr_len:
    resd 1
__dbase_exception_objects_head:
    resd 1
; Stage 673 / O1: Ausgabe-Verteilung in libd64_qt5.dll
import DBaseQtRuntimeWrite, "libd64_qt5.dll", "DBaseQtRuntimeWrite"
