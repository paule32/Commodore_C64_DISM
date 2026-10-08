bits 32

import AllocConsole, "kernel32.dll", "#26"
import GetConsoleWindow, "kernel32.dll", "#562"
import FreeConsole, "kernel32.dll", "#467"
import GetCommandLineA, "kernel32.dll", "#513"
import LoadLibraryA, "kernel32.dll", "#1016"
import GetProcAddress, "kernel32.dll", "#734"
import GetStdHandle, "kernel32.dll", "#772"
import SetConsoleCP, "kernel32.dll", "#1317"
import SetConsoleOutputCP, "kernel32.dll", "#1339"
import MessageBoxA, "user32.dll", "#2151"
import WriteFile, "kernel32.dll", "#1622"
import ReadFile, "kernel32.dll", "#1196"
import CreateFileA, "kernel32.dll", "#230"
import CloseHandle, "kernel32.dll", "#165"
import FlushFileBuffers, "kernel32.dll", "#458"
import MoveFileExA, "kernel32.dll", "#1055"
import DeleteFileA, "kernel32.dll", "#314"
import GetTickCount, "kernel32.dll", "#830"
import VirtualAlloc, "kernel32.dll", "#1546"
import ExitProcess, "kernel32.dll", "#392"
import wsprintfA, "user32.dll", "#2547"
import __prolog_strtod, "msvcrt.dll", "#1364"
import __prolog_gcvt, "msvcrt.dll", "#448"
global _start
entry _start

section .text

__rt_node_ptr:
    mov edi, dword ptr [__prolog_arena]
    mov ecx, eax
    shl ecx, 4
    add edi, ecx
    ret

__rt_dyn_ptr:
    mov edi, dword ptr [__prolog_dyn_base]
    mov ecx, eax
    shl ecx, 4
    add edi, ecx
    ret

__rt_fatal:
    push 2
    call ExitProcess
    ret

__rt_random_u32:
    mov eax, dword ptr [__prolog_random_state]
    mov ecx, eax
    shl ecx, 13
    xor eax, ecx
    mov ecx, eax
    shr ecx, 17
    xor eax, ecx
    mov ecx, eax
    shl ecx, 5
    xor eax, ecx
    mov dword ptr [__prolog_random_state], eax
    ret

__rt_random_bounded:
    push ebx
    push esi
    mov ebx, ecx
    test ebx, ebx
    je __rt_random_bounded_full
    mov eax, ebx
    neg eax
    xor edx, edx
    div ebx
    mov esi, edx
__rt_random_bounded_retry:
    call __rt_random_u32
    cmp eax, esi
    jb __rt_random_bounded_retry
    xor edx, edx
    div ebx
    mov eax, edx
    jmp __rt_random_bounded_done
__rt_random_bounded_full:
    call __rt_random_u32
__rt_random_bounded_done:
    pop esi
    pop ebx
    ret

__rt_new_node:
    mov eax, dword ptr [__prolog_heap_top]
    cmp eax, 16384
    jb __rt_new_node_ok
    call __rt_fatal
__rt_new_node_ok:
    inc dword ptr [__prolog_heap_top]
    call __rt_node_ptr
    mov dword ptr [edi], 0
    mov dword ptr [edi+4], 0
    mov dword ptr [edi+8], 4294967295
    mov dword ptr [edi+12], 4294967295
    ret

__rt_new_dyn_node:
    mov eax, dword ptr [__prolog_dyn_heap_top]
    cmp eax, 16384
    jb __rt_new_dyn_node_ok
    call __rt_fatal
__rt_new_dyn_node_ok:
    inc dword ptr [__prolog_dyn_heap_top]
    call __rt_dyn_ptr
    mov dword ptr [edi], 0
    mov dword ptr [edi+4], 0
    mov dword ptr [edi+8], 4294967295
    mov dword ptr [edi+12], 4294967295
    ret

__rt_build_vars_reset:
    push ebp
    mov ebp, esp
    push edi
    mov ecx, dword ptr [ebp+8]
    mov edi, dword ptr [__prolog_arena]
    add edi, 737280
    xor eax, eax
__rt_build_vars_reset_loop:
    cmp eax, ecx
    jae __rt_build_vars_reset_done
    mov dword ptr [edi+eax*4], 4294967295
    inc eax
    jmp __rt_build_vars_reset_loop
__rt_build_vars_reset_done:
    pop edi
    mov esp, ebp
    pop ebp
    ret

__rt_make_var:
    push ebp
    mov ebp, esp
    push ebx
    push edi
    mov ebx, dword ptr [ebp+8]
    mov edi, dword ptr [__prolog_arena]
    add edi, 737280
    mov eax, dword ptr [edi+ebx*4]
    cmp eax, 4294967295
    jne __rt_make_var_done
    call __rt_new_node
    mov dword ptr [edi], 1
    mov dword ptr [edi+4], eax
    mov ecx, eax
    mov edi, dword ptr [__prolog_arena]
    add edi, 737280
    mov dword ptr [edi+ebx*4], ecx
    mov eax, ecx
__rt_make_var_done:
    pop edi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_make_atom:
    push ebp
    mov ebp, esp
    push ebx
    mov ebx, dword ptr [ebp+8]
    call __rt_new_node
    mov dword ptr [edi], 2
    mov dword ptr [edi+4], ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_make_int:
    push ebp
    mov ebp, esp
    push ebx
    mov ebx, dword ptr [ebp+8]
    call __rt_new_node
    mov dword ptr [edi], 3
    mov dword ptr [edi+4], ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_make_string:
    push ebp
    mov ebp, esp
    push ebx
    mov ebx, dword ptr [ebp+8]
    call __rt_new_node
    mov dword ptr [edi], 4
    mov dword ptr [edi+4], ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_make_float_bits:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    mov ebx, dword ptr [ebp+8]
    mov esi, dword ptr [ebp+12]
    call __rt_new_node
    mov dword ptr [edi], 9
    mov dword ptr [edi+4], ebx
    mov dword ptr [edi+8], esi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_make_float_from_st0:
    call __rt_new_node
    mov dword ptr [edi], 9
    fstp qword ptr [edi+4]
    ret

__rt_make_nil:
    call __rt_new_node
    mov dword ptr [edi], 5
    ret

__rt_make_list:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    mov ebx, dword ptr [ebp+8]
    mov esi, dword ptr [ebp+12]
    call __rt_new_node
    mov dword ptr [edi], 6
    mov dword ptr [edi+8], ebx
    mov dword ptr [edi+12], esi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_make_link:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    mov ebx, dword ptr [ebp+8]
    mov esi, dword ptr [ebp+12]
    call __rt_new_node
    mov dword ptr [edi], 8
    mov dword ptr [edi+8], ebx
    mov dword ptr [edi+12], esi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_make_goal_link:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    mov ebx, dword ptr [ebp+8]
    mov esi, dword ptr [ebp+12]
    mov ecx, dword ptr [ebp+16]
    push ecx
    push esi
    push ebx
    call __rt_make_link
    add esp, 8
    pop ecx
    call __rt_node_ptr
    mov dword ptr [edi+4], ecx
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_make_struct:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    mov ebx, dword ptr [ebp+8]
    mov esi, dword ptr [ebp+12]
    mov ecx, dword ptr [ebp+16]
    push ecx
    call __rt_new_node
    pop ecx
    mov dword ptr [edi], 7
    mov dword ptr [edi+4], ebx
    mov dword ptr [edi+8], esi
    mov dword ptr [edi+12], ecx
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_deref:
__rt_deref_loop:
    call __rt_node_ptr
    cmp dword ptr [edi], 1
    jne __rt_deref_done
    mov ecx, dword ptr [edi+4]
    cmp ecx, eax
    je __rt_deref_done
    mov eax, ecx
    jmp __rt_deref_loop
__rt_deref_done:
    ret

__rt_trail_push:
    push ebp
    mov ebp, esp
    push ebx
    push edi
    mov ebx, dword ptr [ebp+8]
    mov eax, dword ptr [__prolog_trail_top]
    cmp eax, 16384
    jb __rt_trail_push_ok
    call __rt_fatal
__rt_trail_push_ok:
    mov edi, dword ptr [__prolog_arena]
    add edi, 524288
    mov dword ptr [edi+eax*4], ebx
    inc dword ptr [__prolog_trail_top]
    pop edi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_untrail_to:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [ebp+8]
__rt_untrail_loop:
    mov eax, dword ptr [__prolog_trail_top]
    cmp eax, ebx
    jbe __rt_untrail_done
    dec eax
    mov dword ptr [__prolog_trail_top], eax
    mov edi, dword ptr [__prolog_arena]
    add edi, 524288
    mov esi, dword ptr [edi+eax*4]
    mov eax, esi
    call __rt_node_ptr
    mov dword ptr [edi+4], esi
    jmp __rt_untrail_loop
__rt_untrail_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_occurs:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [ebp+8]
    mov eax, dword ptr [ebp+12]
    call __rt_deref
    mov esi, eax
    cmp eax, ebx
    je __rt_occurs_yes
    call __rt_node_ptr
    mov ecx, dword ptr [edi]
    cmp ecx, 6
    je __rt_occurs_list
    cmp ecx, 7
    je __rt_occurs_struct
    xor eax, eax
    jmp __rt_occurs_done
__rt_occurs_list:
    mov ecx, dword ptr [edi+8]
    mov edx, dword ptr [edi+12]
    push edx
    push ecx
    push ebx
    call __rt_occurs
    add esp, 8
    pop edx
    test eax, eax
    jne __rt_occurs_yes
    push edx
    push ebx
    call __rt_occurs
    add esp, 8
    jmp __rt_occurs_done
__rt_occurs_struct:
    mov esi, dword ptr [edi+8]
    mov edx, dword ptr [edi+12]
__rt_occurs_struct_loop:
    test esi, esi
    je __rt_occurs_no
    cmp edx, 4294967295
    je __rt_occurs_no
    mov eax, edx
    call __rt_node_ptr
    mov ecx, dword ptr [edi+8]
    mov edx, dword ptr [edi+12]
    push edx
    push ecx
    push ebx
    call __rt_occurs
    add esp, 8
    pop edx
    test eax, eax
    jne __rt_occurs_yes
    dec esi
    jmp __rt_occurs_struct_loop
__rt_occurs_no:
    xor eax, eax
    jmp __rt_occurs_done
__rt_occurs_yes:
    mov eax, 1
__rt_occurs_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_bind_var:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [ebp+8]
    mov esi, dword ptr [ebp+12]
    push esi
    push ebx
    call __rt_occurs
    add esp, 8
    test eax, eax
    jne __rt_bind_var_occurs_fail
    push ebx
    call __rt_trail_push
    add esp, 4
    mov eax, ebx
    call __rt_node_ptr
    mov dword ptr [edi+4], esi
    mov eax, 1
    jmp __rt_bind_var_done
__rt_bind_var_occurs_fail:
    xor eax, eax
__rt_bind_var_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_choice_push:
    push ebp
    mov ebp, esp
    push edi
    mov eax, dword ptr [__prolog_choice_top]
    cmp eax, 4096
    jb __rt_choice_push_ok
    call __rt_fatal
__rt_choice_push_ok:
    mov edi, dword ptr [__prolog_arena]
    add edi, 589824
    mov ecx, eax
    shl ecx, 4
    add edi, ecx
    mov ecx, dword ptr [__prolog_heap_top]
    mov dword ptr [edi], ecx
    mov ecx, dword ptr [__prolog_trail_top]
    mov dword ptr [edi+4], ecx
    inc dword ptr [__prolog_choice_top]
    pop edi
    mov esp, ebp
    pop ebp
    ret

__rt_choice_restore_pop:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov eax, dword ptr [__prolog_choice_top]
    test eax, eax
    je __rt_choice_restore_done
    dec eax
    mov dword ptr [__prolog_choice_top], eax
    mov edi, dword ptr [__prolog_arena]
    add edi, 589824
    mov ecx, eax
    shl ecx, 4
    add edi, ecx
    mov ebx, dword ptr [edi]
    mov esi, dword ptr [edi+4]
    push esi
    call __rt_untrail_to
    add esp, 4
    mov dword ptr [__prolog_heap_top], ebx
__rt_choice_restore_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_choice_restore_slot:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [ebp+8]
    cmp ebx, 4096
    jae __rt_choice_restore_slot_done
    mov edi, dword ptr [__prolog_arena]
    add edi, 589824
    mov ecx, ebx
    shl ecx, 4
    add edi, ecx
    mov esi, dword ptr [edi]
    mov ecx, dword ptr [edi+4]
    push ecx
    call __rt_untrail_to
    add esp, 4
    mov dword ptr [__prolog_heap_top], esi
    mov dword ptr [__prolog_choice_top], ebx
__rt_choice_restore_slot_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_choice_commit_pop:
    mov eax, dword ptr [__prolog_choice_top]
    test eax, eax
    je __rt_choice_commit_done
    dec eax
    mov dword ptr [__prolog_choice_top], eax
__rt_choice_commit_done:
    ret

__rt_unify:
    push ebp
    mov ebp, esp
    sub esp, 4
    mov eax, dword ptr [__prolog_trail_top]
    mov dword ptr [ebp-4], eax
    push ebx
    push esi
    push edi
    mov eax, dword ptr [ebp+8]
    call __rt_deref
    mov esi, eax
    mov eax, dword ptr [ebp+12]
    call __rt_deref
    mov ebx, eax
    cmp esi, ebx
    je __rt_unify_success
    mov eax, esi
    call __rt_node_ptr
    mov edx, dword ptr [edi]
    cmp edx, 1
    jne __rt_unify_check_right_var
    push ebx
    push esi
    call __rt_bind_var
    add esp, 8
    test eax, eax
    je __rt_unify_fail
    jmp __rt_unify_success
__rt_unify_check_right_var:
    mov eax, ebx
    call __rt_node_ptr
    cmp dword ptr [edi], 1
    jne __rt_unify_nonvar
    push esi
    push ebx
    call __rt_bind_var
    add esp, 8
    test eax, eax
    je __rt_unify_fail
    jmp __rt_unify_success
__rt_unify_nonvar:
    mov eax, esi
    call __rt_node_ptr
    mov edx, dword ptr [edi]
    mov eax, ebx
    call __rt_node_ptr
    cmp edx, dword ptr [edi]
    jne __rt_unify_fail
    cmp edx, 2
    je __rt_unify_scalar
    cmp edx, 3
    je __rt_unify_scalar
    cmp edx, 4
    je __rt_unify_scalar
    cmp edx, 9
    je __rt_unify_float
    cmp edx, 5
    je __rt_unify_success
    cmp edx, 6
    je __rt_unify_list
    cmp edx, 7
    je __rt_unify_struct
    jmp __rt_unify_fail
__rt_unify_scalar:
    mov edx, dword ptr [edi+4]
    mov eax, esi
    call __rt_node_ptr
    cmp dword ptr [edi+4], edx
    jne __rt_unify_fail
    jmp __rt_unify_success
__rt_unify_float:
    mov edx, dword ptr [edi+4]
    mov ecx, dword ptr [edi+8]
    push ecx
    push edx
    mov eax, esi
    call __rt_node_ptr
    pop edx
    pop ecx
    cmp dword ptr [edi+4], edx
    jne __rt_unify_fail
    cmp dword ptr [edi+8], ecx
    jne __rt_unify_fail
    jmp __rt_unify_success
__rt_unify_list:
    mov eax, esi
    call __rt_node_ptr
    mov eax, dword ptr [edi+8]
    mov edx, dword ptr [edi+12]
    push edx
    push eax
    mov eax, ebx
    call __rt_node_ptr
    mov eax, dword ptr [edi+8]
    mov edx, dword ptr [edi+12]
    pop esi
    push edx
    push eax
    push esi
    call __rt_unify
    add esp, 8
    test eax, eax
    je __rt_unify_fail_pop_tails
    pop edx
    pop esi
    push edx
    push esi
    call __rt_unify
    add esp, 8
    test eax, eax
    je __rt_unify_fail
    jmp __rt_unify_success
__rt_unify_fail_pop_tails:
    pop edx
    pop esi
    jmp __rt_unify_fail
__rt_unify_struct:
    push ebx
    mov eax, esi
    call __rt_node_ptr
    mov ebx, dword ptr [edi+4]
    mov esi, dword ptr [edi+8]
    mov edx, dword ptr [edi+12]
    pop ecx
    mov eax, ecx
    call __rt_node_ptr
    cmp ebx, dword ptr [edi+4]
    jne __rt_unify_fail
    cmp esi, dword ptr [edi+8]
    jne __rt_unify_fail
    mov ecx, dword ptr [edi+12]
    mov ebx, esi
__rt_unify_struct_loop:
    test ebx, ebx
    je __rt_unify_success
    push ecx
    mov eax, edx
    call __rt_node_ptr
    mov esi, dword ptr [edi+8]
    mov edx, dword ptr [edi+12]
    pop ecx
    push edx
    mov eax, ecx
    call __rt_node_ptr
    mov eax, dword ptr [edi+8]
    mov ecx, dword ptr [edi+12]
    push ecx
    push eax
    push esi
    call __rt_unify
    add esp, 8
    test eax, eax
    je __rt_unify_struct_fail_stack
    pop ecx
    pop edx
    dec ebx
    jmp __rt_unify_struct_loop
__rt_unify_struct_fail_stack:
    pop ecx
    pop edx
    jmp __rt_unify_fail
__rt_unify_success:
    mov eax, 1
    jmp __rt_unify_done
__rt_unify_fail:
    push dword ptr [ebp-4]
    call __rt_untrail_to
    add esp, 4
    xor eax, eax
__rt_unify_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_equal_terms:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov eax, dword ptr [ebp+8]
    call __rt_deref
    mov ebx, eax
    mov eax, dword ptr [ebp+12]
    call __rt_deref
    mov esi, eax
    cmp ebx, esi
    je __rt_equal_yes
    mov eax, ebx
    call __rt_node_ptr
    mov edx, dword ptr [edi]
    mov ecx, dword ptr [edi+4]
    push ecx
    push edx
    mov eax, esi
    call __rt_node_ptr
    pop edx
    pop ecx
    cmp edx, dword ptr [edi]
    jne __rt_equal_no
    cmp edx, 1
    je __rt_equal_no
    cmp edx, 2
    je __rt_equal_scalar
    cmp edx, 3
    je __rt_equal_scalar
    cmp edx, 4
    je __rt_equal_scalar
    cmp edx, 9
    je __rt_equal_float
    cmp edx, 5
    je __rt_equal_yes
    cmp edx, 6
    je __rt_equal_list
    cmp edx, 7
    je __rt_equal_struct
    jmp __rt_equal_no
__rt_equal_scalar:
    cmp ecx, dword ptr [edi+4]
    je __rt_equal_yes
    jmp __rt_equal_no
__rt_equal_float:
    mov eax, ebx
    call __rt_node_ptr
    mov edx, dword ptr [edi+4]
    mov ecx, dword ptr [edi+8]
    push ecx
    push edx
    mov eax, esi
    call __rt_node_ptr
    pop edx
    pop ecx
    cmp dword ptr [edi+4], edx
    jne __rt_equal_no
    cmp dword ptr [edi+8], ecx
    je __rt_equal_yes
    jmp __rt_equal_no
__rt_equal_list:
    mov eax, ebx
    call __rt_node_ptr
    mov ecx, dword ptr [edi+8]
    mov edx, dword ptr [edi+12]
    push edx
    push ecx
    mov eax, esi
    call __rt_node_ptr
    mov ecx, dword ptr [edi+8]
    mov edx, dword ptr [edi+12]
    push edx
    push ecx
    pop ecx
    pop edx
    pop eax
    pop esi
    push esi
    push edx
    push ecx
    push eax
    call __rt_equal_terms
    add esp, 8
    pop edx
    pop esi
    test eax, eax
    je __rt_equal_no
    push edx
    push esi
    call __rt_equal_terms
    add esp, 8
    jmp __rt_equal_done
__rt_equal_struct:
    mov eax, ebx
    call __rt_node_ptr
    mov ebx, dword ptr [edi+4]
    mov ecx, dword ptr [edi+8]
    mov edx, dword ptr [edi+12]
    push edx
    push ecx
    mov eax, esi
    call __rt_node_ptr
    cmp ebx, dword ptr [edi+4]
    jne __rt_equal_struct_fail_pop
    pop ecx
    cmp ecx, dword ptr [edi+8]
    jne __rt_equal_struct_fail_one
    mov esi, dword ptr [edi+12]
    pop edx
__rt_equal_struct_loop:
    test ecx, ecx
    je __rt_equal_yes
    mov eax, edx
    call __rt_node_ptr
    mov ebx, dword ptr [edi+8]
    mov edx, dword ptr [edi+12]
    push edx
    mov eax, esi
    call __rt_node_ptr
    mov eax, dword ptr [edi+8]
    mov esi, dword ptr [edi+12]
    push ecx
    push esi
    push eax
    push ebx
    call __rt_equal_terms
    add esp, 8
    pop esi
    pop ecx
    pop edx
    test eax, eax
    je __rt_equal_no
    dec ecx
    jmp __rt_equal_struct_loop
__rt_equal_struct_fail_pop:
    pop ecx
__rt_equal_struct_fail_one:
    pop edx
    jmp __rt_equal_no
__rt_equal_yes:
    mov eax, 1
    jmp __rt_equal_done
__rt_equal_no:
    xor eax, eax
__rt_equal_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_struct_arg:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov eax, dword ptr [ebp+8]
    call __rt_deref
    call __rt_node_ptr
    cmp dword ptr [edi], 7
    jne __rt_struct_arg_fail
    mov esi, dword ptr [edi+12]
    mov ebx, dword ptr [ebp+12]
__rt_struct_arg_loop:
    cmp esi, 4294967295
    je __rt_struct_arg_fail
    mov eax, esi
    call __rt_node_ptr
    test ebx, ebx
    je __rt_struct_arg_found
    mov esi, dword ptr [edi+12]
    dec ebx
    jmp __rt_struct_arg_loop
__rt_struct_arg_found:
    mov eax, dword ptr [edi+8]
    jmp __rt_struct_arg_done
__rt_struct_arg_fail:
    mov eax, 4294967295
__rt_struct_arg_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_goal_expr_to_chain:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [ebp+8]
    mov esi, dword ptr [ebp+12]
    mov eax, ebx
    call __rt_deref
    mov ebx, eax
    call __rt_node_ptr
    cmp dword ptr [edi], 7
    jne __rt_goal_expr_single
    cmp dword ptr [edi+4], 3
    jne __rt_goal_expr_single
    cmp dword ptr [edi+8], 2
    jne __rt_goal_expr_single
    push 1
    push ebx
    call __rt_struct_arg
    add esp, 8
    push dword ptr [ebp+16]
    push esi
    push eax
    call __rt_goal_expr_to_chain
    add esp, 12
    mov esi, eax
    push 0
    push ebx
    call __rt_struct_arg
    add esp, 8
    push dword ptr [ebp+16]
    push esi
    push eax
    call __rt_goal_expr_to_chain
    add esp, 12
    jmp __rt_goal_expr_done
__rt_goal_expr_single:
    push dword ptr [ebp+16]
    push esi
    push ebx
    call __rt_make_goal_link
    add esp, 12
__rt_goal_expr_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_make_binary_term:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    mov ebx, dword ptr [ebp+8]
    mov esi, dword ptr [ebp+12]
    mov ecx, dword ptr [ebp+16]
    push 4294967295
    push ecx
    call __rt_make_link
    add esp, 8
    mov ecx, eax
    push ecx
    push esi
    call __rt_make_link
    add esp, 8
    mov ecx, eax
    push ecx
    push 2
    push ebx
    call __rt_make_struct
    add esp, 12
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_make_unary_term:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    mov ebx, dword ptr [ebp+8]
    mov esi, dword ptr [ebp+12]
    push 4294967295
    push esi
    call __rt_make_link
    add esp, 8
    push eax
    push 1
    push ebx
    call __rt_make_struct
    add esp, 12
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_load_number:
    push ebp
    mov ebp, esp
    push ebx
    push edi
    mov eax, dword ptr [ebp+8]
    call __rt_deref
    mov ebx, eax
    call __rt_node_ptr
    cmp dword ptr [edi], 3
    je __rt_load_number_int
    cmp dword ptr [edi], 9
    je __rt_load_number_float
    xor eax, eax
    jmp __rt_load_number_done
__rt_load_number_int:
    fild dword ptr [edi+4]
    mov eax, 1
    jmp __rt_load_number_done
__rt_load_number_float:
    fld qword ptr [edi+4]
    mov eax, 1
__rt_load_number_done:
    pop edi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_numeric_zero:
    push ebp
    mov ebp, esp
    push edi
    mov eax, dword ptr [ebp+8]
    call __rt_deref
    call __rt_node_ptr
    cmp dword ptr [edi], 3
    je __rt_numeric_zero_int
    cmp dword ptr [edi], 9
    je __rt_numeric_zero_float
    xor eax, eax
    xor edx, edx
    jmp __rt_numeric_zero_done
__rt_numeric_zero_int:
    xor eax, eax
    cmp dword ptr [edi+4], 0
    sete al
    mov edx, 1
    jmp __rt_numeric_zero_done
__rt_numeric_zero_float:
    mov eax, dword ptr [edi+4]
    mov ecx, dword ptr [edi+8]
    and ecx, 2147483647
    or eax, ecx
    sete al
    and eax, 1
    mov edx, 1
__rt_numeric_zero_done:
    pop edi
    mov esp, ebp
    pop ebp
    ret

__rt_numeric_compare:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+12]
    call __rt_load_number
    add esp, 4
    test eax, eax
    je __rt_numeric_compare_fail
    push dword ptr [ebp+8]
    call __rt_load_number
    add esp, 4
    test eax, eax
    jne __rt_numeric_compare_have
    fstp st0
    jmp __rt_numeric_compare_fail
__rt_numeric_compare_have:
    fucomip st0, st1
    fstp st0
    jp __rt_numeric_compare_fail
    je __rt_numeric_compare_equal
    jb __rt_numeric_compare_less
    mov eax, 1
    mov edx, 1
    jmp __rt_numeric_compare_done
__rt_numeric_compare_less:
    mov eax, -1
    mov edx, 1
    jmp __rt_numeric_compare_done
__rt_numeric_compare_equal:
    xor eax, eax
    mov edx, 1
    jmp __rt_numeric_compare_done
__rt_numeric_compare_fail:
    xor eax, eax
    xor edx, edx
__rt_numeric_compare_done:
    mov esp, ebp
    pop ebp
    ret

__rt_eval_arith:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov eax, dword ptr [ebp+8]
    call __rt_deref
    mov ebx, eax
    call __rt_node_ptr
    cmp dword ptr [edi], 3
    je __rt_eval_numeric_leaf
    cmp dword ptr [edi], 9
    je __rt_eval_numeric_leaf
    cmp dword ptr [edi], 7
    jne __rt_eval_fail
    mov esi, dword ptr [edi+4]
    mov ecx, dword ptr [edi+8]
    cmp esi, 31
    jne __rt_eval_float_next
    cmp ecx, 1
    je __rt_eval_float
__rt_eval_float_next:
    cmp esi, 18
    jne __rt_eval_uplus_next
    cmp ecx, 1
    je __rt_eval_uplus
__rt_eval_uplus_next:
    cmp esi, 19
    jne __rt_eval_uminus_next
    cmp ecx, 1
    je __rt_eval_uminus
__rt_eval_uminus_next:
    cmp esi, 18
    jne __rt_eval_add_next
    cmp ecx, 2
    je __rt_eval_add
__rt_eval_add_next:
    cmp esi, 19
    jne __rt_eval_sub_next
    cmp ecx, 2
    je __rt_eval_sub
__rt_eval_sub_next:
    cmp esi, 20
    jne __rt_eval_mul_next
    cmp ecx, 2
    je __rt_eval_mul
__rt_eval_mul_next:
    cmp esi, 21
    jne __rt_eval_div_next
    cmp ecx, 2
    je __rt_eval_div
__rt_eval_div_next:
    cmp esi, 22
    jne __rt_eval_mod_next
    cmp ecx, 2
    je __rt_eval_mod
__rt_eval_mod_next:
    jmp __rt_eval_fail
__rt_eval_numeric_leaf:
    mov eax, ebx
    mov edx, 1
    jmp __rt_eval_done
__rt_eval_float:
    push 0
    push ebx
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_eval_fail
    push eax
    call __rt_load_number
    add esp, 4
    test eax, eax
    je __rt_eval_fail
    call __rt_make_float_from_st0
    mov edx, 1
    jmp __rt_eval_done
__rt_eval_uplus:
    push 0
    push ebx
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_eval_fail
    mov ebx, eax
    mov eax, ebx
    mov edx, 1
    jmp __rt_eval_done
__rt_eval_uminus:
    push 0
    push ebx
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_eval_fail
    mov ebx, eax
    mov eax, ebx
    call __rt_node_ptr
    cmp dword ptr [edi], 3
    jne __rt_eval_uminus_float
    mov eax, dword ptr [edi+4]
    neg eax
    push eax
    call __rt_make_int
    add esp, 4
    mov edx, 1
    jmp __rt_eval_done
__rt_eval_uminus_float:
    push ebx
    call __rt_load_number
    add esp, 4
    test eax, eax
    je __rt_eval_fail
    fchs
    call __rt_make_float_from_st0
    mov edx, 1
    jmp __rt_eval_done
__rt_eval_add:
    push 0
    push ebx
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_eval_fail
    push eax
    push 1
    push ebx
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_eval_fail_pop
    mov esi, eax
    pop ebx
    mov eax, ebx
    call __rt_node_ptr
    cmp dword ptr [edi], 3
    jne __rt_eval_add_float
    mov eax, esi
    call __rt_node_ptr
    cmp dword ptr [edi], 3
    jne __rt_eval_add_float
    mov eax, ebx
    call __rt_node_ptr
    mov ebx, dword ptr [edi+4]
    mov eax, esi
    call __rt_node_ptr
    mov ecx, dword ptr [edi+4]
    mov eax, ebx
    add eax, ecx
    push eax
    call __rt_make_int
    add esp, 4
    mov edx, 1
    jmp __rt_eval_done
__rt_eval_add_float:
    push ebx
    call __rt_load_number
    add esp, 4
    test eax, eax
    je __rt_eval_fail
    push esi
    call __rt_load_number
    add esp, 4
    test eax, eax
    jne __rt_eval_add_fpu
    fstp st0
    jmp __rt_eval_fail
__rt_eval_add_fpu:
    faddp
    call __rt_make_float_from_st0
    mov edx, 1
    jmp __rt_eval_done
__rt_eval_sub:
    push 0
    push ebx
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_eval_fail
    push eax
    push 1
    push ebx
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_eval_fail_pop
    mov esi, eax
    pop ebx
    mov eax, ebx
    call __rt_node_ptr
    cmp dword ptr [edi], 3
    jne __rt_eval_sub_float
    mov eax, esi
    call __rt_node_ptr
    cmp dword ptr [edi], 3
    jne __rt_eval_sub_float
    mov eax, ebx
    call __rt_node_ptr
    mov ebx, dword ptr [edi+4]
    mov eax, esi
    call __rt_node_ptr
    mov ecx, dword ptr [edi+4]
    mov eax, ebx
    sub eax, ecx
    push eax
    call __rt_make_int
    add esp, 4
    mov edx, 1
    jmp __rt_eval_done
__rt_eval_sub_float:
    push ebx
    call __rt_load_number
    add esp, 4
    test eax, eax
    je __rt_eval_fail
    push esi
    call __rt_load_number
    add esp, 4
    test eax, eax
    jne __rt_eval_sub_fpu
    fstp st0
    jmp __rt_eval_fail
__rt_eval_sub_fpu:
    fsubp
    call __rt_make_float_from_st0
    mov edx, 1
    jmp __rt_eval_done
__rt_eval_mul:
    push 0
    push ebx
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_eval_fail
    push eax
    push 1
    push ebx
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_eval_fail_pop
    mov esi, eax
    pop ebx
    mov eax, ebx
    call __rt_node_ptr
    cmp dword ptr [edi], 3
    jne __rt_eval_mul_float
    mov eax, esi
    call __rt_node_ptr
    cmp dword ptr [edi], 3
    jne __rt_eval_mul_float
    mov eax, ebx
    call __rt_node_ptr
    mov ebx, dword ptr [edi+4]
    mov eax, esi
    call __rt_node_ptr
    mov ecx, dword ptr [edi+4]
    mov eax, ebx
    imul eax, ecx
    push eax
    call __rt_make_int
    add esp, 4
    mov edx, 1
    jmp __rt_eval_done
__rt_eval_mul_float:
    push ebx
    call __rt_load_number
    add esp, 4
    test eax, eax
    je __rt_eval_fail
    push esi
    call __rt_load_number
    add esp, 4
    test eax, eax
    jne __rt_eval_mul_fpu
    fstp st0
    jmp __rt_eval_fail
__rt_eval_mul_fpu:
    fmulp
    call __rt_make_float_from_st0
    mov edx, 1
    jmp __rt_eval_done
__rt_eval_div:
    push 0
    push ebx
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_eval_fail
    push eax
    push 1
    push ebx
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_eval_fail_pop
    mov esi, eax
    pop ebx
    push esi
    call __rt_numeric_zero
    add esp, 4
    test edx, edx
    je __rt_eval_fail
    test eax, eax
    jne __rt_eval_fail
    push ebx
    call __rt_load_number
    add esp, 4
    test eax, eax
    je __rt_eval_fail
    push esi
    call __rt_load_number
    add esp, 4
    test eax, eax
    jne __rt_eval_div_fpu
    fstp st0
    jmp __rt_eval_fail
__rt_eval_div_fpu:
    fdivp
    call __rt_make_float_from_st0
    mov edx, 1
    jmp __rt_eval_done
__rt_eval_mod:
    push 0
    push ebx
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_eval_fail
    push eax
    push 1
    push ebx
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_eval_fail_pop
    mov esi, eax
    pop ebx
    mov eax, ebx
    call __rt_node_ptr
    cmp dword ptr [edi], 3
    jne __rt_eval_fail
    mov ebx, dword ptr [edi+4]
    mov eax, esi
    call __rt_node_ptr
    cmp dword ptr [edi], 3
    jne __rt_eval_fail
    mov ecx, dword ptr [edi+4]
    test ecx, ecx
    je __rt_eval_fail
    mov eax, ebx
    cdq
    idiv ecx
    mov eax, edx
    push eax
    call __rt_make_int
    add esp, 4
    mov edx, 1
    jmp __rt_eval_done
__rt_eval_fail_pop:
    pop ebx
__rt_eval_fail:
    xor eax, eax
    xor edx, edx
__rt_eval_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_dyn_copy_ground:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov eax, dword ptr [ebp+8]
    call __rt_deref
    mov ebx, eax
    call __rt_node_ptr
    mov esi, dword ptr [edi]
    cmp esi, 1
    je __rt_dyn_copy_var
    cmp esi, 2
    je __rt_dyn_copy_scalar
    cmp esi, 3
    je __rt_dyn_copy_scalar
    cmp esi, 4
    je __rt_dyn_copy_scalar
    cmp esi, 5
    je __rt_dyn_copy_scalar
    cmp esi, 9
    je __rt_dyn_copy_float
    cmp esi, 6
    je __rt_dyn_copy_list
    cmp esi, 7
    je __rt_dyn_copy_struct
    jmp __rt_dyn_copy_fail
__rt_dyn_copy_var:
    xor ecx, ecx
__rt_dyn_copy_var_scan:
    cmp ecx, dword ptr [__prolog_dyn_copy_var_count]
    jae __rt_dyn_copy_var_new
    mov edi, dword ptr [__prolog_arena]
    add edi, 751616
    cmp dword ptr [edi+ecx*4], ebx
    jne __rt_dyn_copy_var_scan_next
    mov edi, dword ptr [__prolog_arena]
    add edi, 752640
    mov eax, dword ptr [edi+ecx*4]
    jmp __rt_dyn_copy_done
__rt_dyn_copy_var_scan_next:
    inc ecx
    jmp __rt_dyn_copy_var_scan
__rt_dyn_copy_var_new:
    cmp ecx, 256
    jae __rt_dyn_copy_fail
    push ecx
    call __rt_new_dyn_node
    pop ecx
    mov edx, eax
    mov dword ptr [edi], 1
    mov dword ptr [edi+4], edx
    mov edi, dword ptr [__prolog_arena]
    add edi, 751616
    mov dword ptr [edi+ecx*4], ebx
    mov edi, dword ptr [__prolog_arena]
    add edi, 752640
    mov dword ptr [edi+ecx*4], edx
    inc dword ptr [__prolog_dyn_copy_var_count]
    mov eax, edx
    jmp __rt_dyn_copy_done
__rt_dyn_copy_scalar:
    mov ebx, dword ptr [edi+4]
    call __rt_new_dyn_node
    mov dword ptr [edi], esi
    mov dword ptr [edi+4], ebx
    jmp __rt_dyn_copy_done
__rt_dyn_copy_float:
    mov ebx, dword ptr [edi+4]
    mov ecx, dword ptr [edi+8]
    push ecx
    call __rt_new_dyn_node
    pop ecx
    mov dword ptr [edi], 9
    mov dword ptr [edi+4], ebx
    mov dword ptr [edi+8], ecx
    jmp __rt_dyn_copy_done
__rt_dyn_copy_list:
    mov eax, ebx
    call __rt_node_ptr
    mov esi, dword ptr [edi+8]
    mov ebx, dword ptr [edi+12]
    push esi
    call __rt_dyn_copy_ground
    add esp, 4
    cmp eax, 4294967295
    je __rt_dyn_copy_fail
    push eax
    push ebx
    call __rt_dyn_copy_ground
    add esp, 4
    cmp eax, 4294967295
    je __rt_dyn_copy_list_fail_stack
    mov ebx, eax
    pop esi
    call __rt_new_dyn_node
    mov dword ptr [edi], 6
    mov dword ptr [edi+8], esi
    mov dword ptr [edi+12], ebx
    jmp __rt_dyn_copy_done
__rt_dyn_copy_list_fail_stack:
    pop esi
    jmp __rt_dyn_copy_fail
__rt_dyn_copy_struct:
    mov eax, ebx
    call __rt_node_ptr
    mov ebx, dword ptr [edi+4]
    mov esi, dword ptr [edi+8]
    mov ecx, dword ptr [edi+12]
    push esi
    push ecx
    call __rt_dyn_copy_links
    add esp, 8
    cmp eax, 4294967295
    je __rt_dyn_copy_fail
    mov ecx, eax
    push ecx
    call __rt_new_dyn_node
    pop ecx
    mov dword ptr [edi], 7
    mov dword ptr [edi+4], ebx
    mov dword ptr [edi+8], esi
    mov dword ptr [edi+12], ecx
    jmp __rt_dyn_copy_done
__rt_dyn_copy_fail:
    mov eax, 4294967295
__rt_dyn_copy_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_dyn_copy_links:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [ebp+8]
    mov esi, dword ptr [ebp+12]
    test esi, esi
    jne __rt_dyn_copy_links_some
    mov eax, 4294967295
    jmp __rt_dyn_copy_links_done
__rt_dyn_copy_links_some:
    mov eax, ebx
    call __rt_node_ptr
    mov eax, dword ptr [edi+8]
    mov ebx, dword ptr [edi+12]
    push eax
    dec esi
    push esi
    push ebx
    call __rt_dyn_copy_links
    add esp, 8
    mov ecx, eax
    pop eax
    push ecx
    push eax
    call __rt_dyn_copy_ground
    add esp, 4
    pop ecx
    cmp eax, 4294967295
    je __rt_dyn_copy_links_fail
    push ecx
    push eax
    call __rt_new_dyn_link
    add esp, 8
    jmp __rt_dyn_copy_links_done
__rt_dyn_copy_links_fail:
    mov eax, 4294967295
__rt_dyn_copy_links_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_new_dyn_link:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    mov ebx, dword ptr [ebp+8]
    mov esi, dword ptr [ebp+12]
    call __rt_new_dyn_node
    mov dword ptr [edi], 8
    mov dword ptr [edi+8], ebx
    mov dword ptr [edi+12], esi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_dyn_clone:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov eax, dword ptr [ebp+8]
    cmp eax, 4294967295
    je __rt_dyn_clone_fail
    cmp eax, 16384
    jae __rt_dyn_clone_fail
    mov ebx, eax
    call __rt_dyn_ptr
    mov esi, dword ptr [edi]
    cmp esi, 1
    je __rt_dyn_clone_var
    cmp esi, 2
    je __rt_dyn_clone_scalar
    cmp esi, 3
    je __rt_dyn_clone_scalar
    cmp esi, 4
    je __rt_dyn_clone_scalar
    cmp esi, 5
    je __rt_dyn_clone_scalar
    cmp esi, 9
    je __rt_dyn_clone_float
    cmp esi, 6
    je __rt_dyn_clone_list
    cmp esi, 7
    je __rt_dyn_clone_struct
    mov eax, 4294967295
    jmp __rt_dyn_clone_done
__rt_dyn_clone_var:
    xor ecx, ecx
__rt_dyn_clone_var_scan:
    cmp ecx, dword ptr [__prolog_dyn_clone_var_count]
    jae __rt_dyn_clone_var_new
    mov edi, dword ptr [__prolog_arena]
    add edi, 754688
    cmp dword ptr [edi+ecx*4], ebx
    jne __rt_dyn_clone_var_scan_next
    mov edi, dword ptr [__prolog_arena]
    add edi, 755712
    mov eax, dword ptr [edi+ecx*4]
    jmp __rt_dyn_clone_done
__rt_dyn_clone_var_scan_next:
    inc ecx
    jmp __rt_dyn_clone_var_scan
__rt_dyn_clone_var_new:
    cmp ecx, 256
    jae __rt_dyn_clone_fail
    push ecx
    call __rt_new_node
    pop ecx
    mov edx, eax
    mov dword ptr [edi], 1
    mov dword ptr [edi+4], edx
    mov edi, dword ptr [__prolog_arena]
    add edi, 754688
    mov dword ptr [edi+ecx*4], ebx
    mov edi, dword ptr [__prolog_arena]
    add edi, 755712
    mov dword ptr [edi+ecx*4], edx
    inc dword ptr [__prolog_dyn_clone_var_count]
    mov eax, edx
    jmp __rt_dyn_clone_done
__rt_dyn_clone_scalar:
    mov ebx, dword ptr [edi+4]
    call __rt_new_node
    mov dword ptr [edi], esi
    mov dword ptr [edi+4], ebx
    jmp __rt_dyn_clone_done
__rt_dyn_clone_float:
    mov ebx, dword ptr [edi+4]
    mov ecx, dword ptr [edi+8]
    push ecx
    call __rt_new_node
    pop ecx
    mov dword ptr [edi], 9
    mov dword ptr [edi+4], ebx
    mov dword ptr [edi+8], ecx
    jmp __rt_dyn_clone_done
__rt_dyn_clone_list:
    mov eax, ebx
    call __rt_dyn_ptr
    mov esi, dword ptr [edi+8]
    mov ebx, dword ptr [edi+12]
    push esi
    call __rt_dyn_clone
    add esp, 4
    push eax
    push ebx
    call __rt_dyn_clone
    add esp, 4
    mov ebx, eax
    pop esi
    push ebx
    push esi
    call __rt_make_list
    add esp, 8
    jmp __rt_dyn_clone_done
__rt_dyn_clone_struct:
    mov eax, ebx
    call __rt_dyn_ptr
    mov ebx, dword ptr [edi+4]
    mov esi, dword ptr [edi+8]
    mov ecx, dword ptr [edi+12]
    push esi
    push ecx
    call __rt_dyn_clone_links
    add esp, 8
    mov ecx, eax
    push ecx
    push esi
    push ebx
    call __rt_make_struct
    add esp, 12
    jmp __rt_dyn_clone_done
__rt_dyn_clone_fail:
    mov eax, 4294967295
__rt_dyn_clone_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_dyn_clone_links:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [ebp+8]
    mov esi, dword ptr [ebp+12]
    test esi, esi
    jne __rt_dyn_clone_links_some
    mov eax, 4294967295
    jmp __rt_dyn_clone_links_done
__rt_dyn_clone_links_some:
    mov eax, ebx
    call __rt_dyn_ptr
    mov eax, dword ptr [edi+8]
    mov ebx, dword ptr [edi+12]
    push eax
    dec esi
    push esi
    push ebx
    call __rt_dyn_clone_links
    add esp, 8
    mov ecx, eax
    pop eax
    push ecx
    push eax
    call __rt_dyn_clone
    add esp, 4
    pop ecx
    push ecx
    push eax
    call __rt_make_link
    add esp, 8
__rt_dyn_clone_links_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_assert:
    push dword ptr [ebp+8]
    call __rt_assertz
    add esp, 4
    ret

__rt_assertz:
    push ebp
    mov ebp, esp
    push 0
    push dword ptr [ebp+8]
    call __rt_assert_common
    add esp, 8
    mov esp, ebp
    pop ebp
    ret

__rt_asserta:
    push ebp
    mov ebp, esp
    push 1
    push dword ptr [ebp+8]
    call __rt_assert_common
    add esp, 8
    mov esp, ebp
    pop ebp
    ret

__rt_assert_common:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [ebp+8]
    mov esi, dword ptr [ebp+12]
    mov eax, dword ptr [__prolog_current_db]
    test eax, eax
    je __rt_assert_modify_ok
    cmp dword ptr [__prolog_db_loading], 0
    jne __rt_assert_modify_ok
    push eax
    call __rt_db_can_modify_id
    add esp, 4
    test eax, eax
    je __rt_assert_common_fail
__rt_assert_modify_ok:
    cmp dword ptr [__prolog_dyn_count], 512
    jb __rt_assert_count_ok
    call __rt_dyn_db_compact
__rt_assert_count_ok:
    cmp dword ptr [__prolog_dyn_count], 512
    jae __rt_assert_common_fail
    cmp dword ptr [__prolog_dyn_heap_top], 12288
    jb __rt_assert_heap_ok
    call __rt_gc_dynamic
__rt_assert_heap_ok:
    mov eax, ebx
    call __rt_deref
    mov ebx, eax
    call __rt_node_ptr
    cmp dword ptr [edi], 7
    jne __rt_assert_head_ready_root
    cmp dword ptr [edi+4], 5
    jne __rt_assert_head_ready_root
    cmp dword ptr [edi+8], 2
    jne __rt_assert_head_ready_root
    push 0
    push ebx
    call __rt_struct_arg
    add esp, 8
    mov ecx, eax
    jmp __rt_assert_head_ready
__rt_assert_head_ready_root:
    mov ecx, ebx
__rt_assert_head_ready:
    mov eax, ecx
    call __rt_deref
    mov ecx, eax
    call __rt_node_ptr
    mov edx, dword ptr [edi]
    cmp edx, 2
    je __rt_assert_common_atom
    cmp edx, 7
    jne __rt_assert_common_fail
    mov edx, dword ptr [edi+4]
    mov ecx, dword ptr [edi+8]
    jmp __rt_assert_common_copy
__rt_assert_common_atom:
    mov edx, dword ptr [edi+4]
    xor ecx, ecx
__rt_assert_common_copy:
    push esi
    push ecx
    push edx
    mov dword ptr [__prolog_dyn_copy_var_count], 0
    push ebx
    call __rt_dyn_copy_ground
    add esp, 4
    mov ebx, eax
    pop edx
    pop ecx
    pop esi
    cmp ebx, 4294967295
    je __rt_assert_common_fail
    push ecx
    push edx
    mov eax, dword ptr [__prolog_dyn_count]
    test esi, esi
    je __rt_assert_store
    mov esi, eax
__rt_asserta_shift_loop:
    test esi, esi
    je __rt_asserta_shift_done
    mov edi, dword ptr [__prolog_arena]
    add edi, 743424
    mov eax, esi
    dec eax
    shl eax, 4
    add edi, eax
    mov eax, dword ptr [edi]
    mov ecx, dword ptr [edi+4]
    mov edx, dword ptr [edi+8]
    push ebx
    mov ebx, dword ptr [edi+12]
    add edi, 16
    mov dword ptr [edi], eax
    mov dword ptr [edi+4], ecx
    mov dword ptr [edi+8], edx
    mov dword ptr [edi+12], ebx
    pop ebx
    mov edi, dword ptr [__prolog_arena]
    add edi, 759808
    mov eax, esi
    dec eax
    mov ecx, dword ptr [edi+eax*4]
    mov dword ptr [edi+esi*4], ecx
    dec esi
    jmp __rt_asserta_shift_loop
__rt_asserta_shift_done:
    xor eax, eax
__rt_assert_store:
    pop edx
    pop ecx
    push eax
    mov edi, dword ptr [__prolog_arena]
    add edi, 743424
    shl eax, 4
    add edi, eax
    mov dword ptr [edi], 1
    mov dword ptr [edi+4], edx
    mov dword ptr [edi+8], ecx
    mov dword ptr [edi+12], ebx
    pop eax
    mov edi, dword ptr [__prolog_arena]
    add edi, 759808
    mov edx, dword ptr [__prolog_current_db]
    mov dword ptr [edi+eax*4], edx
    inc dword ptr [__prolog_dyn_count]
    test edx, edx
    je __rt_assert_store_no_dirty
    push edx
    call __rt_db_mark_modified_id
    add esp, 4
__rt_assert_store_no_dirty:
    mov eax, 1
    jmp __rt_assert_common_done
__rt_assert_common_fail:
    xor eax, eax
__rt_assert_common_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_retract:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [ebp+8]
    mov eax, dword ptr [__prolog_current_db]
    test eax, eax
    je __rt_retract_modify_ok
    push eax
    call __rt_db_can_modify_id
    add esp, 4
    test eax, eax
    je __rt_retract_fail
__rt_retract_modify_ok:
    xor esi, esi
__rt_retract_loop:
    cmp esi, dword ptr [__prolog_dyn_count]
    jae __rt_retract_fail
    mov edi, dword ptr [__prolog_arena]
    add edi, 743424
    mov eax, esi
    shl eax, 4
    add edi, eax
    cmp dword ptr [edi], 0
    je __rt_retract_next
    mov edx, dword ptr [__prolog_current_db]
    mov edi, dword ptr [__prolog_arena]
    add edi, 759808
    cmp dword ptr [edi+esi*4], edx
    jne __rt_retract_next
    mov edi, dword ptr [__prolog_arena]
    add edi, 743424
    mov eax, esi
    shl eax, 4
    add edi, eax
    mov eax, dword ptr [edi+12]
    push eax
    call __rt_choice_push
    pop eax
    mov dword ptr [__prolog_dyn_clone_var_count], 0
    push eax
    call __rt_dyn_clone
    add esp, 4
    push eax
    push ebx
    call __rt_unify
    add esp, 8
    test eax, eax
    je __rt_retract_restore_next
    mov edi, dword ptr [__prolog_arena]
    add edi, 743424
    mov eax, esi
    shl eax, 4
    add edi, eax
    mov dword ptr [edi], 0
    mov edi, dword ptr [__prolog_arena]
    add edi, 759808
    mov edx, dword ptr [edi+esi*4]
    test edx, edx
    je __rt_retract_no_dirty
    push edx
    call __rt_db_mark_modified_id
    add esp, 4
__rt_retract_no_dirty:
    call __rt_choice_commit_pop
    mov eax, 1
    jmp __rt_retract_done
__rt_retract_restore_next:
    call __rt_choice_restore_pop
__rt_retract_next:
    inc esi
    jmp __rt_retract_loop
__rt_retract_fail:
    xor eax, eax
__rt_retract_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_dyn_db_compact:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    xor esi, esi
    xor ebx, ebx
__rt_dyn_compact_loop:
    cmp esi, dword ptr [__prolog_dyn_count]
    jae __rt_dyn_compact_done
    mov edi, dword ptr [__prolog_arena]
    add edi, 743424
    mov eax, esi
    shl eax, 4
    add edi, eax
    cmp dword ptr [edi], 0
    je __rt_dyn_compact_next
    cmp esi, ebx
    je __rt_dyn_compact_kept
    push esi
    mov eax, dword ptr [edi+4]
    push eax
    mov eax, dword ptr [edi+8]
    push eax
    mov eax, dword ptr [edi+12]
    push eax
    mov edi, dword ptr [__prolog_arena]
    add edi, 743424
    mov eax, ebx
    shl eax, 4
    add edi, eax
    pop eax
    pop edx
    pop ecx
    pop esi
    mov dword ptr [edi], 1
    mov dword ptr [edi+4], ecx
    mov dword ptr [edi+8], edx
    mov dword ptr [edi+12], eax
    mov edi, dword ptr [__prolog_arena]
    add edi, 759808
    mov eax, dword ptr [edi+esi*4]
    mov dword ptr [edi+ebx*4], eax
__rt_dyn_compact_kept:
    inc ebx
__rt_dyn_compact_next:
    inc esi
    jmp __rt_dyn_compact_loop
__rt_dyn_compact_done:
    mov dword ptr [__prolog_dyn_count], ebx
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_gc_dynamic:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    call __rt_dyn_db_compact
    mov eax, dword ptr [__prolog_heap_top]
    mov dword ptr [__prolog_gc_heap_mark], eax
    xor esi, esi
__rt_gc_clone_loop:
    cmp esi, dword ptr [__prolog_dyn_count]
    jae __rt_gc_flip
    mov edi, dword ptr [__prolog_arena]
    add edi, 743424
    mov eax, esi
    shl eax, 4
    add edi, eax
    mov eax, dword ptr [edi+12]
    mov dword ptr [__prolog_dyn_clone_var_count], 0
    push eax
    call __rt_dyn_clone
    add esp, 4
    mov edi, dword ptr [__prolog_arena]
    add edi, 757760
    mov dword ptr [edi+esi*4], eax
    inc esi
    jmp __rt_gc_clone_loop
__rt_gc_flip:
    mov eax, dword ptr [__prolog_dyn_base]
    mov edi, dword ptr [__prolog_dyn_alt_base]
    mov dword ptr [__prolog_dyn_base], edi
    mov dword ptr [__prolog_dyn_alt_base], eax
    mov dword ptr [__prolog_dyn_heap_top], 0
    xor esi, esi
__rt_gc_copy_loop:
    cmp esi, dword ptr [__prolog_dyn_count]
    jae __rt_gc_done
    mov edi, dword ptr [__prolog_arena]
    add edi, 757760
    mov eax, dword ptr [edi+esi*4]
    mov dword ptr [__prolog_dyn_copy_var_count], 0
    push eax
    call __rt_dyn_copy_ground
    add esp, 4
    mov ebx, eax
    mov edi, dword ptr [__prolog_arena]
    add edi, 743424
    mov eax, esi
    shl eax, 4
    add edi, eax
    mov dword ptr [edi+12], ebx
    inc esi
    jmp __rt_gc_copy_loop
__rt_gc_done:
    mov eax, dword ptr [__prolog_gc_heap_mark]
    mov dword ptr [__prolog_heap_top], eax
    mov eax, 1
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_strlen:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [ebp+8]
    xor eax, eax
__rt_strlen_loop:
    movzx ecx, byte ptr [esi+eax]
    test ecx, ecx
    je __rt_strlen_done
    inc eax
    jmp __rt_strlen_loop
__rt_strlen_done:
    pop esi
    mov esp, ebp
    pop ebp
    ret

__rt_emit_text:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov esi, dword ptr [ebp+8]
    cmp dword ptr [__prolog_emit_to_file], 0
    je __rt_emit_text_normal
    push esi
    call __rt_strlen
    add esp, 4
    mov ebx, eax
    push 0
    push __prolog_written
    push ebx
    push esi
    push dword ptr [__prolog_emit_file_handle]
    call WriteFile
    test eax, eax
    jne __rt_emit_text_done
    mov dword ptr [__prolog_emit_file_error], 1
    jmp __rt_emit_text_done
__rt_emit_text_normal:
    cmp dword ptr [__prolog_start_mode], 1
    jne __rt_emit_text_console
    push esi
    call __rt_strlen
    add esp, 4
    mov ebx, eax
    xor edi, edi
    mov eax, __prolog_text_false_line
    cmp esi, eax
    jne __rt_emit_text_gui_style_ready
    mov edi, 1
__rt_emit_text_gui_style_ready:
    push edi
    push ebx
    push esi
    mov eax, dword ptr [__prolog_qt_write_fn]
    call eax
    add esp, 12
    jmp __rt_emit_text_done
__rt_emit_text_console:
    push esi
    call __rt_strlen
    add esp, 4
    mov ebx, eax
    push 0
    push __prolog_written
    push ebx
    push esi
    push dword ptr [__prolog_stdout]
    call WriteFile
__rt_emit_text_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_atom_ptr:
    push ebp
    mov ebp, esp
    push ebx
    push edi
    mov ebx, dword ptr [ebp+8]
    cmp ebx, 289
    ja __rt_atom_ptr_dynamic
    test ebx, ebx
    je __rt_atom_ptr_fail
    dec ebx
    mov edi, __prolog_static_atom_offsets
    movzx eax, word ptr [edi+ebx*2]
    mov edi, __prolog_static_atom_blob
    add eax, edi
    jmp __rt_atom_ptr_done
__rt_atom_ptr_dynamic:
    sub ebx, 290
    cmp ebx, dword ptr [__prolog_dyn_atom_count]
    jae __rt_atom_ptr_fail
    mov edi, dword ptr [__prolog_arena]
    add edi, 739328
    mov eax, dword ptr [edi+ebx*4]
    jmp __rt_atom_ptr_done
__rt_atom_ptr_fail:
    xor eax, eax
__rt_atom_ptr_done:
    pop edi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_emit_atom_id:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __rt_atom_ptr
    add esp, 4
    push eax
    call __rt_emit_text
    add esp, 4
    mov esp, ebp
    pop ebp
    ret

__rt_emit_int:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    push __prolog_fmt_int
    push __prolog_format_buffer
    call wsprintfA
    add esp, 12
    push __prolog_format_buffer
    call __rt_emit_text
    add esp, 4
    mov esp, ebp
    pop ebp
    ret

__rt_emit_float:
    push ebp
    mov ebp, esp
    push edi
    mov eax, dword ptr [ebp+8]
    call __rt_deref
    call __rt_node_ptr
    push __prolog_format_buffer
    push 15
    push dword ptr [edi+8]
    push dword ptr [edi+4]
    call __prolog_gcvt
    add esp, 16
    push eax
    call __rt_emit_text
    add esp, 4
    pop edi
    mov esp, ebp
    pop ebp
    ret

__rt_emit_term:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov eax, dword ptr [ebp+8]
    call __rt_deref
    mov ebx, eax
    call __rt_node_ptr
    mov esi, dword ptr [edi]
    cmp esi, 1
    je __rt_emit_term_var
    cmp esi, 2
    je __rt_emit_term_atom
    cmp esi, 4
    je __rt_emit_term_string
    cmp esi, 3
    je __rt_emit_term_int
    cmp esi, 9
    je __rt_emit_term_float
    cmp esi, 5
    je __rt_emit_term_nil
    cmp esi, 6
    je __rt_emit_term_list
    cmp esi, 7
    je __rt_emit_term_struct
    jmp __rt_emit_term_done
__rt_emit_term_var:
    cmp dword ptr [__prolog_emit_to_file], 0
    je __rt_emit_term_var_plain
    push ebx
    call __rt_emit_saved_var
    add esp, 4
    jmp __rt_emit_term_done
__rt_emit_term_var_plain:
    push __prolog_text_underscore
    call __rt_emit_text
    add esp, 4
    jmp __rt_emit_term_done
__rt_emit_term_atom:
    push dword ptr [edi+4]
    call __rt_emit_atom_id
    add esp, 4
    jmp __rt_emit_term_done
__rt_emit_term_string:
    push __prolog_text_quote
    call __rt_emit_text
    add esp, 4
    push dword ptr [edi+4]
    call __rt_emit_atom_id
    add esp, 4
    push __prolog_text_quote
    call __rt_emit_text
    add esp, 4
    jmp __rt_emit_term_done
__rt_emit_term_int:
    push dword ptr [edi+4]
    call __rt_emit_int
    add esp, 4
    jmp __rt_emit_term_done
__rt_emit_term_float:
    push ebx
    call __rt_emit_float
    add esp, 4
    jmp __rt_emit_term_done
__rt_emit_term_nil:
    push __prolog_text_nil
    call __rt_emit_text
    add esp, 4
    jmp __rt_emit_term_done
__rt_emit_term_list:
    push __prolog_text_lbrack
    call __rt_emit_text
    add esp, 4
    mov esi, ebx
    xor ebx, ebx
__rt_emit_term_list_loop:
    mov eax, esi
    call __rt_deref
    mov esi, eax
    call __rt_node_ptr
    cmp dword ptr [edi], 5
    je __rt_emit_term_list_close
    cmp dword ptr [edi], 6
    jne __rt_emit_term_list_tail
    test ebx, ebx
    je __rt_emit_term_list_no_comma
    push __prolog_text_comma_space
    call __rt_emit_text
    add esp, 4
__rt_emit_term_list_no_comma:
    mov eax, dword ptr [edi+8]
    mov esi, dword ptr [edi+12]
    push esi
    push eax
    call __rt_emit_term
    add esp, 4
    pop esi
    mov ebx, 1
    jmp __rt_emit_term_list_loop
__rt_emit_term_list_tail:
    push __prolog_text_bar
    call __rt_emit_text
    add esp, 4
    push esi
    call __rt_emit_term
    add esp, 4
__rt_emit_term_list_close:
    push __prolog_text_rbrack
    call __rt_emit_text
    add esp, 4
    jmp __rt_emit_term_done
__rt_emit_term_struct:
    mov esi, dword ptr [edi+4]
    mov ebx, dword ptr [edi+8]
    mov ecx, dword ptr [edi+12]
    push ecx
    push esi
    call __rt_emit_atom_id
    add esp, 4
    push __prolog_text_lparen
    call __rt_emit_text
    add esp, 4
    pop ecx
    xor esi, esi
__rt_emit_term_struct_loop:
    cmp esi, ebx
    jae __rt_emit_term_struct_close
    test esi, esi
    je __rt_emit_term_struct_no_comma
    push ecx
    push __prolog_text_comma_space
    call __rt_emit_text
    add esp, 4
    pop ecx
__rt_emit_term_struct_no_comma:
    mov eax, ecx
    call __rt_node_ptr
    mov eax, dword ptr [edi+8]
    mov ecx, dword ptr [edi+12]
    push ecx
    push eax
    call __rt_emit_term
    add esp, 4
    pop ecx
    inc esi
    jmp __rt_emit_term_struct_loop
__rt_emit_term_struct_close:
    push __prolog_text_rparen
    call __rt_emit_text
    add esp, 4
__rt_emit_term_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_emit_solution:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    cmp dword ptr [__prolog_direct_eval], 0
    jne __rt_emit_solution_direct
    cmp dword ptr [__prolog_interactive_mode], 0
    je __rt_emit_solution_accept
    cmp dword ptr [__prolog_solution_count], 0
    je __rt_emit_solution_accept
__rt_emit_solution_prompt_next:
    push __prolog_text_more_prompt
    call __rt_emit_text
    add esp, 4
    call __rt_read_line
    movzx ecx, byte ptr [eax]
    test ecx, ecx
    je __rt_emit_solution_accept_redo
    cmp ecx, 59
    je __rt_emit_solution_accept_redo
    cmp ecx, 110
    je __rt_emit_solution_accept_redo
    cmp ecx, 78
    je __rt_emit_solution_accept_redo
    cmp ecx, 114
    je __rt_emit_solution_accept_redo
    cmp ecx, 82
    je __rt_emit_solution_accept_redo
    cmp ecx, 32
    je __rt_emit_solution_accept_redo
    cmp ecx, 9
    je __rt_emit_solution_accept_redo
    cmp ecx, 113
    je __rt_emit_solution_stop
    cmp ecx, 81
    je __rt_emit_solution_stop
    cmp ecx, 46
    je __rt_emit_solution_stop
    cmp ecx, 58
    je __rt_emit_solution_stop
    cmp ecx, 99
    je __rt_emit_solution_stop
    cmp ecx, 67
    je __rt_emit_solution_stop
    cmp ecx, 97
    je __rt_emit_solution_stop
    cmp ecx, 65
    je __rt_emit_solution_stop
__rt_emit_solution_stop:
    mov dword ptr [__prolog_stop_search], 1
    jmp __rt_emit_solution_return
__rt_emit_solution_accept_redo:
    mov dword ptr [__prolog_requested_more], 1
__rt_emit_solution_accept:
    inc dword ptr [__prolog_solution_count]
    cmp dword ptr [__prolog_verbose], 0
    jne __rt_emit_solution_return
    mov ebx, dword ptr [__prolog_query_var_count]
    test ebx, ebx
    jne __rt_emit_solution_vars
    push __prolog_text_true_line
    call __rt_emit_text
    add esp, 4
    jmp __rt_emit_solution_return
__rt_emit_solution_vars:
    xor esi, esi
__rt_emit_solution_loop:
    cmp esi, ebx
    jae __rt_emit_solution_line_done
    test esi, esi
    je __rt_emit_solution_no_sep
    push __prolog_text_comma_space
    call __rt_emit_text
    add esp, 4
__rt_emit_solution_no_sep:
    mov edi, dword ptr [__prolog_arena]
    add edi, 738560
    mov eax, dword ptr [edi+esi*4]
    push eax
    call __rt_emit_text
    add esp, 4
    push __prolog_text_equals
    call __rt_emit_text
    add esp, 4
    mov edi, dword ptr [__prolog_arena]
    add edi, 738304
    mov eax, dword ptr [edi+esi*4]
    push eax
    call __rt_emit_term
    add esp, 4
    inc esi
    jmp __rt_emit_solution_loop
__rt_emit_solution_line_done:
    push __prolog_text_dot_nl
    call __rt_emit_text
    add esp, 4
    jmp __rt_emit_solution_return
__rt_emit_solution_direct:
    inc dword ptr [__prolog_solution_count]
    mov dword ptr [__prolog_direct_eval], 0
    mov dword ptr [__prolog_stop_search], 1
__rt_emit_solution_return:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_parse_skip_ws:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [__prolog_arena]
    add esi, 720896
__rt_parse_skip_ws_loop:
    mov ecx, dword ptr [__prolog_parse_pos]
    movzx eax, byte ptr [esi+ecx]
    cmp eax, 32
    je __rt_parse_skip_ws_one
    cmp eax, 9
    je __rt_parse_skip_ws_one
    cmp eax, 13
    je __rt_parse_skip_ws_one
    cmp eax, 10
    je __rt_parse_skip_ws_one
    cmp eax, 37
    je __rt_parse_skip_ws_line_comment
    cmp eax, 47
    jne __rt_parse_skip_ws_done
    mov ecx, dword ptr [__prolog_parse_pos]
    movzx eax, byte ptr [esi+ecx+1]
    cmp eax, 42
    jne __rt_parse_skip_ws_done
    add dword ptr [__prolog_parse_pos], 2
__rt_parse_skip_ws_block_comment:
    mov ecx, dword ptr [__prolog_parse_pos]
    movzx eax, byte ptr [esi+ecx]
    test eax, eax
    je __rt_parse_skip_ws_done
    cmp eax, 42
    jne __rt_parse_skip_ws_block_next
    movzx eax, byte ptr [esi+ecx+1]
    cmp eax, 47
    jne __rt_parse_skip_ws_block_next
    add dword ptr [__prolog_parse_pos], 2
    jmp __rt_parse_skip_ws_loop
__rt_parse_skip_ws_block_next:
    inc dword ptr [__prolog_parse_pos]
    jmp __rt_parse_skip_ws_block_comment
__rt_parse_skip_ws_line_comment:
    inc dword ptr [__prolog_parse_pos]
    mov ecx, dword ptr [__prolog_parse_pos]
    movzx eax, byte ptr [esi+ecx]
    test eax, eax
    je __rt_parse_skip_ws_done
    cmp eax, 10
    je __rt_parse_skip_ws_loop
    cmp eax, 13
    je __rt_parse_skip_ws_loop
    jmp __rt_parse_skip_ws_line_comment
__rt_parse_skip_ws_one:
    inc dword ptr [__prolog_parse_pos]
    jmp __rt_parse_skip_ws_loop
__rt_parse_skip_ws_done:
    pop esi
    mov esp, ebp
    pop ebp
    ret

__rt_parse_consume:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    mov ebx, dword ptr [ebp+8]
    call __rt_parse_skip_ws
    cmp eax, ebx
    jne __rt_parse_consume_fail
    inc dword ptr [__prolog_parse_pos]
    mov eax, 1
    jmp __rt_parse_consume_done
__rt_parse_consume_fail:
    xor eax, eax
__rt_parse_consume_done:
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_parse_token:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov esi, dword ptr [__prolog_arena]
    add esi, 720896
    mov edi, dword ptr [__prolog_arena]
    add edi, 724992
    mov ebx, dword ptr [__prolog_parse_pos]
    xor ecx, ecx
__rt_parse_token_loop:
    movzx eax, byte ptr [esi+ebx]
    cmp eax, 48
    jb __rt_parse_token_check_alpha
    cmp eax, 57
    jbe __rt_parse_token_store
__rt_parse_token_check_alpha:
    cmp eax, 65
    jb __rt_parse_token_check_lower
    cmp eax, 90
    jbe __rt_parse_token_store
__rt_parse_token_check_lower:
    cmp eax, 97
    jb __rt_parse_token_check_us
    cmp eax, 122
    jbe __rt_parse_token_store
__rt_parse_token_check_us:
    cmp eax, 95
    je __rt_parse_token_store
    cmp eax, 128
    jb __rt_parse_token_done
    cmp eax, 195
    jne __rt_parse_token_store
    movzx edx, byte ptr [esi+ebx+1]
    cmp edx, 164
    je __rt_parse_token_utf8_228
    cmp edx, 182
    je __rt_parse_token_utf8_246
    cmp edx, 188
    je __rt_parse_token_utf8_252
    cmp edx, 132
    je __rt_parse_token_utf8_196
    cmp edx, 150
    je __rt_parse_token_utf8_214
    cmp edx, 156
    je __rt_parse_token_utf8_220
    cmp edx, 159
    je __rt_parse_token_utf8_223
    jmp __rt_parse_token_store
__rt_parse_token_utf8_228:
    mov eax, 228
    inc ebx
    jmp __rt_parse_token_store
__rt_parse_token_utf8_246:
    mov eax, 246
    inc ebx
    jmp __rt_parse_token_store
__rt_parse_token_utf8_252:
    mov eax, 252
    inc ebx
    jmp __rt_parse_token_store
__rt_parse_token_utf8_196:
    mov eax, 196
    inc ebx
    jmp __rt_parse_token_store
__rt_parse_token_utf8_214:
    mov eax, 214
    inc ebx
    jmp __rt_parse_token_store
__rt_parse_token_utf8_220:
    mov eax, 220
    inc ebx
    jmp __rt_parse_token_store
__rt_parse_token_utf8_223:
    mov eax, 223
    inc ebx
    jmp __rt_parse_token_store
__rt_parse_token_store:
    cmp ecx, 4095
    jae __rt_parse_token_done
    mov byte ptr [edi+ecx], al
    inc ecx
    inc ebx
    jmp __rt_parse_token_loop
__rt_parse_token_done:
    xor eax, eax
    mov byte ptr [edi+ecx], al
    mov dword ptr [__prolog_parse_pos], ebx
    mov eax, edi
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_token_eq:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov esi, dword ptr [ebp+8]
    mov edi, dword ptr [ebp+16]
    mov ebx, dword ptr [ebp+12]
    xor ecx, ecx
__rt_token_eq_loop:
    cmp ecx, ebx
    jae __rt_token_eq_endcheck
    movzx eax, byte ptr [esi+ecx]
    movzx edx, byte ptr [edi+ecx]
    cmp eax, edx
    jne __rt_token_eq_fail
    inc ecx
    jmp __rt_token_eq_loop
__rt_token_eq_endcheck:
    movzx eax, byte ptr [edi+ecx]
    test eax, eax
    jne __rt_token_eq_fail
    mov eax, 1
    jmp __rt_token_eq_done
__rt_token_eq_fail:
    xor eax, eax
__rt_token_eq_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_intern_atom:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov esi, dword ptr [ebp+8]
    mov ebx, dword ptr [ebp+12]
    xor ecx, ecx
__rt_intern_static_loop:
    cmp ecx, 289
    jae __rt_intern_dynamic_scan
    push ecx
    mov edi, __prolog_static_atom_offsets
    movzx eax, word ptr [edi+ecx*2]
    mov edi, __prolog_static_atom_blob
    add eax, edi
    push eax
    push ebx
    push esi
    call __rt_token_eq
    add esp, 12
    pop ecx
    test eax, eax
    jne __rt_intern_static_found
    inc ecx
    jmp __rt_intern_static_loop
__rt_intern_static_found:
    lea eax, [ecx+1]
    jmp __rt_intern_done
__rt_intern_dynamic_scan:
    xor ecx, ecx
__rt_intern_dynamic_loop:
    cmp ecx, dword ptr [__prolog_dyn_atom_count]
    jae __rt_intern_create
    push ecx
    mov edi, dword ptr [__prolog_arena]
    add edi, 739328
    mov eax, dword ptr [edi+ecx*4]
    push eax
    push ebx
    push esi
    call __rt_token_eq
    add esp, 12
    pop ecx
    test eax, eax
    jne __rt_intern_dynamic_found
    inc ecx
    jmp __rt_intern_dynamic_loop
__rt_intern_dynamic_found:
    add ecx, 290
    mov eax, ecx
    jmp __rt_intern_done
__rt_intern_create:
    cmp ecx, 512
    jae __rt_intern_fail
    mov edi, dword ptr [__prolog_arena]
    add edi, 655360
    mov edx, dword ptr [__prolog_atom_pool_top]
    mov eax, edx
    add eax, ebx
    inc eax
    cmp eax, 65536
    jae __rt_intern_fail
    add edi, edx
    push edi
    xor eax, eax
__rt_intern_copy_loop:
    cmp eax, ebx
    jae __rt_intern_copy_done
    movzx edx, byte ptr [esi+eax]
    mov byte ptr [edi+eax], dl
    inc eax
    jmp __rt_intern_copy_loop
__rt_intern_copy_done:
    xor edx, edx
    mov byte ptr [edi+eax], dl
    inc eax
    add dword ptr [__prolog_atom_pool_top], eax
    pop esi
    mov ecx, dword ptr [__prolog_dyn_atom_count]
    mov edi, dword ptr [__prolog_arena]
    add edi, 739328
    mov dword ptr [edi+ecx*4], esi
    inc dword ptr [__prolog_dyn_atom_count]
    add ecx, 290
    mov eax, ecx
    jmp __rt_intern_done
__rt_intern_fail:
    xor eax, eax
__rt_intern_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_query_var:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov esi, dword ptr [ebp+8]
    mov ebx, dword ptr [ebp+12]
    xor edx, edx
__rt_query_var_scan:
    cmp edx, dword ptr [__prolog_query_var_count]
    jae __rt_query_var_new
    push edx
    mov edi, dword ptr [__prolog_arena]
    add edi, 738560
    mov eax, dword ptr [edi+edx*4]
    push eax
    push ebx
    push esi
    call __rt_token_eq
    add esp, 12
    pop edx
    test eax, eax
    jne __rt_query_var_found
    inc edx
    jmp __rt_query_var_scan
__rt_query_var_found:
    mov edi, dword ptr [__prolog_arena]
    add edi, 738304
    mov eax, dword ptr [edi+edx*4]
    jmp __rt_query_var_done
__rt_query_var_new:
    mov ecx, dword ptr [__prolog_query_var_count]
    cmp ecx, 64
    jae __rt_query_var_fail
    push ecx
    call __rt_new_node
    pop ecx
    mov edx, eax
    mov dword ptr [edi], 1
    mov dword ptr [edi+4], edx
    mov edi, dword ptr [__prolog_arena]
    add edi, 738304
    mov dword ptr [edi+ecx*4], edx
    mov edi, dword ptr [__prolog_arena]
    add edi, 729088
    mov eax, dword ptr [__prolog_qname_top]
    add edi, eax
    push edi
    xor eax, eax
__rt_query_var_copy:
    cmp eax, ebx
    jae __rt_query_var_copy_done
    movzx edx, byte ptr [esi+eax]
    mov byte ptr [edi+eax], dl
    inc eax
    jmp __rt_query_var_copy
__rt_query_var_copy_done:
    xor edx, edx
    mov byte ptr [edi+eax], dl
    inc eax
    add dword ptr [__prolog_qname_top], eax
    pop esi
    mov edi, dword ptr [__prolog_arena]
    add edi, 738560
    mov dword ptr [edi+ecx*4], esi
    inc dword ptr [__prolog_query_var_count]
    mov edi, dword ptr [__prolog_arena]
    add edi, 738304
    mov eax, dword ptr [edi+ecx*4]
    jmp __rt_query_var_done
__rt_query_var_fail:
    mov eax, 4294967295
__rt_query_var_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_db_parser_var:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov esi, dword ptr [ebp+8]
    mov ebx, dword ptr [ebp+12]
    xor edx, edx
__rt_db_parser_var_scan:
    cmp edx, dword ptr [__prolog_db_parser_var_count]
    jae __rt_db_parser_var_new
    push edx
    mov edi, dword ptr [__prolog_arena]
    add edi, 753920
    mov eax, dword ptr [edi+edx*4]
    push eax
    push ebx
    push esi
    call __rt_token_eq
    add esp, 12
    pop edx
    test eax, eax
    jne __rt_db_parser_var_found
    inc edx
    jmp __rt_db_parser_var_scan
__rt_db_parser_var_found:
    mov edi, dword ptr [__prolog_arena]
    add edi, 753664
    mov eax, dword ptr [edi+edx*4]
    jmp __rt_db_parser_var_done
__rt_db_parser_var_new:
    mov ecx, dword ptr [__prolog_db_parser_var_count]
    cmp ecx, 64
    jae __rt_db_parser_var_fail
    push ecx
    call __rt_new_node
    pop ecx
    mov edx, eax
    mov dword ptr [edi], 1
    mov dword ptr [edi+4], edx
    mov edi, dword ptr [__prolog_arena]
    add edi, 753664
    mov dword ptr [edi+ecx*4], edx
    mov edi, dword ptr [__prolog_arena]
    add edi, 761856
    mov eax, dword ptr [__prolog_db_parser_name_top]
    mov edx, eax
    add eax, ebx
    inc eax
    cmp eax, 4096
    jae __rt_db_parser_var_fail
    add edi, edx
    push edi
    xor eax, eax
__rt_db_parser_var_copy:
    cmp eax, ebx
    jae __rt_db_parser_var_copy_done
    movzx edx, byte ptr [esi+eax]
    mov byte ptr [edi+eax], dl
    inc eax
    jmp __rt_db_parser_var_copy
__rt_db_parser_var_copy_done:
    xor edx, edx
    mov byte ptr [edi+eax], dl
    inc eax
    add dword ptr [__prolog_db_parser_name_top], eax
    pop esi
    mov edi, dword ptr [__prolog_arena]
    add edi, 753920
    mov dword ptr [edi+ecx*4], esi
    inc dword ptr [__prolog_db_parser_var_count]
    mov edi, dword ptr [__prolog_arena]
    add edi, 753664
    mov eax, dword ptr [edi+ecx*4]
    jmp __rt_db_parser_var_done
__rt_db_parser_var_fail:
    mov eax, 4294967295
__rt_db_parser_var_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_parse_term:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    call __rt_parse_skip_ws
    cmp eax, 40
    je __rt_parse_term_paren
    cmp eax, 91
    je __rt_parse_term_list
    cmp eax, 33
    je __rt_parse_term_cut
    cmp eax, 34
    je __rt_parse_term_string
    cmp eax, 39
    je __rt_parse_term_quoted
    cmp eax, 45
    je __rt_parse_term_number
    cmp eax, 48
    jb __rt_parse_term_identifier
    cmp eax, 57
    jbe __rt_parse_term_number
__rt_parse_term_identifier:
    cmp eax, 65
    jb __rt_parse_term_fail
    cmp eax, 90
    jbe __rt_parse_term_variable
    cmp eax, 95
    je __rt_parse_term_variable
    cmp eax, 97
    jb __rt_parse_term_fail
    cmp eax, 122
    jbe __rt_parse_term_atom
    cmp eax, 128
    jae __rt_parse_term_atom
    jmp __rt_parse_term_fail
__rt_parse_term_paren:
    inc dword ptr [__prolog_parse_pos]
    call __rt_parse_rule_expr
    cmp eax, 4294967295
    je __rt_parse_term_fail
    push eax
    push 41
    call __rt_parse_consume
    add esp, 4
    pop ecx
    test eax, eax
    je __rt_parse_term_fail
    mov eax, ecx
    jmp __rt_parse_term_done
__rt_parse_term_cut:
    inc dword ptr [__prolog_parse_pos]
    push 9
    call __rt_make_atom
    add esp, 4
    jmp __rt_parse_term_done
__rt_parse_term_variable:
    call __rt_parse_token
    push ecx
    push eax
    cmp dword ptr [__prolog_parser_db_mode], 0
    jne __rt_parse_term_variable_db
    call __rt_query_var
    add esp, 8
    jmp __rt_parse_term_done
__rt_parse_term_variable_db:
    call __rt_db_parser_var
    add esp, 8
    jmp __rt_parse_term_done
__rt_parse_term_atom:
    call __rt_parse_token
    push ecx
    push eax
    call __rt_intern_atom
    add esp, 8
    mov ebx, eax
    call __rt_parse_skip_ws
    cmp eax, 40
    jne __rt_parse_term_atom_simple
    inc dword ptr [__prolog_parse_pos]
    call __rt_parse_args
    push eax
    push ecx
    push ebx
    call __rt_make_struct
    add esp, 12
    jmp __rt_parse_term_done
__rt_parse_term_atom_simple:
    push ebx
    call __rt_make_atom
    add esp, 4
    jmp __rt_parse_term_done
__rt_parse_term_number:
    mov esi, dword ptr [__prolog_arena]
    add esi, 720896
    mov ecx, dword ptr [__prolog_parse_pos]
    push ecx
    xor ebx, ebx
    xor edx, edx
    movzx eax, byte ptr [esi+ecx]
    cmp eax, 45
    jne __rt_parse_number_loop
    mov edx, 1
    inc ecx
__rt_parse_number_loop:
    movzx eax, byte ptr [esi+ecx]
    cmp eax, 48
    jb __rt_parse_number_integer_end
    cmp eax, 57
    ja __rt_parse_number_integer_end
    mov edi, ebx
    shl ebx, 3
    shl edi, 1
    add ebx, edi
    sub eax, 48
    add ebx, eax
    inc ecx
    jmp __rt_parse_number_loop
__rt_parse_number_integer_end:
    xor edi, edi
    cmp eax, 46
    jne __rt_parse_number_exp_check
    movzx eax, byte ptr [esi+ecx+1]
    cmp eax, 48
    jb __rt_parse_number_exp_check
    cmp eax, 57
    ja __rt_parse_number_exp_check
    mov edi, 1
    inc ecx
__rt_parse_number_frac_loop:
    movzx eax, byte ptr [esi+ecx]
    cmp eax, 48
    jb __rt_parse_number_exp_check
    cmp eax, 57
    ja __rt_parse_number_exp_check
    inc ecx
    jmp __rt_parse_number_frac_loop
__rt_parse_number_exp_check:
    movzx eax, byte ptr [esi+ecx]
    cmp eax, 101
    je __rt_parse_number_exp_candidate
    cmp eax, 69
    jne __rt_parse_number_finish
__rt_parse_number_exp_candidate:
    mov eax, ecx
    inc eax
    movzx ebx, byte ptr [esi+eax]
    cmp ebx, 43
    je __rt_parse_number_exp_sign
    cmp ebx, 45
    jne __rt_parse_number_exp_digit_check
__rt_parse_number_exp_sign:
    inc eax
    movzx ebx, byte ptr [esi+eax]
__rt_parse_number_exp_digit_check:
    cmp ebx, 48
    jb __rt_parse_number_finish
    cmp ebx, 57
    ja __rt_parse_number_finish
    mov edi, 1
    mov ecx, eax
__rt_parse_number_exp_loop:
    movzx eax, byte ptr [esi+ecx]
    cmp eax, 48
    jb __rt_parse_number_finish
    cmp eax, 57
    ja __rt_parse_number_finish
    inc ecx
    jmp __rt_parse_number_exp_loop
__rt_parse_number_finish:
    mov dword ptr [__prolog_parse_pos], ecx
    test edi, edi
    jne __rt_parse_number_float
    pop eax
    test edx, edx
    je __rt_parse_number_emit_int
    neg ebx
__rt_parse_number_emit_int:
    push ebx
    call __rt_make_int
    add esp, 4
    jmp __rt_parse_term_done
__rt_parse_number_float:
    pop eax
    add esi, eax
    push 0
    push esi
    call __prolog_strtod
    add esp, 8
    call __rt_make_float_from_st0
    jmp __rt_parse_term_done
__rt_parse_term_string:
    mov ebx, 34
    mov edx, 1
    jmp __rt_parse_quoted_common
__rt_parse_term_quoted:
    mov ebx, 39
    xor edx, edx
__rt_parse_quoted_common:
    inc dword ptr [__prolog_parse_pos]
    push edx
    mov esi, dword ptr [__prolog_arena]
    add esi, 720896
    mov edi, dword ptr [__prolog_arena]
    add edi, 724992
    mov ecx, dword ptr [__prolog_parse_pos]
    xor eax, eax
__rt_parse_quoted_loop:
    movzx edx, byte ptr [esi+ecx]
    test edx, edx
    je __rt_parse_quoted_unclosed
    cmp edx, ebx
    je __rt_parse_quoted_done
    mov byte ptr [edi+eax], dl
    inc eax
    inc ecx
    jmp __rt_parse_quoted_loop
__rt_parse_quoted_unclosed:
    pop edx
    jmp __rt_parse_term_fail
__rt_parse_quoted_done:
    inc ecx
    mov dword ptr [__prolog_parse_pos], ecx
    xor ecx, ecx
    mov byte ptr [edi+eax], cl
    mov ecx, eax
    pop edx
    push edx
    push ecx
    push edi
    call __rt_intern_atom
    add esp, 8
    pop edx
    push eax
    test edx, edx
    je __rt_parse_quoted_make_atom
    call __rt_make_string
    add esp, 4
    jmp __rt_parse_term_done
__rt_parse_quoted_make_atom:
    call __rt_make_atom
    add esp, 4
    jmp __rt_parse_term_done
__rt_parse_term_list:
    inc dword ptr [__prolog_parse_pos]
    call __rt_parse_skip_ws
    cmp eax, 93
    jne __rt_parse_list_nonempty
    inc dword ptr [__prolog_parse_pos]
    call __rt_make_nil
    jmp __rt_parse_term_done
__rt_parse_list_nonempty:
    call __rt_parse_list_elements
    jmp __rt_parse_term_done
__rt_parse_term_fail:
    mov eax, 4294967295
__rt_parse_term_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_parse_args:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    call __rt_parse_skip_ws
    cmp eax, 41
    jne __rt_parse_args_some
    inc dword ptr [__prolog_parse_pos]
    mov eax, 4294967295
    xor ecx, ecx
    jmp __rt_parse_args_done
__rt_parse_args_some:
    call __rt_parse_relation
    cmp eax, 4294967295
    je __rt_parse_args_fail
    mov ebx, eax
    call __rt_parse_skip_ws
    cmp eax, 44
    jne __rt_parse_args_last
    inc dword ptr [__prolog_parse_pos]
    call __rt_parse_args
    mov esi, ecx
    mov ecx, eax
    push ecx
    push ebx
    call __rt_make_link
    add esp, 8
    mov ecx, esi
    inc ecx
    jmp __rt_parse_args_done
__rt_parse_args_last:
    cmp eax, 41
    jne __rt_parse_args_fail
    inc dword ptr [__prolog_parse_pos]
    push 4294967295
    push ebx
    call __rt_make_link
    add esp, 8
    mov ecx, 1
    jmp __rt_parse_args_done
__rt_parse_args_fail:
    mov eax, 4294967295
    xor ecx, ecx
__rt_parse_args_done:
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_parse_list_elements:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    call __rt_parse_relation
    cmp eax, 4294967295
    je __rt_parse_list_fail
    mov ebx, eax
    call __rt_parse_skip_ws
    cmp eax, 44
    je __rt_parse_list_more
    cmp eax, 124
    je __rt_parse_list_tail
    cmp eax, 93
    jne __rt_parse_list_fail
    inc dword ptr [__prolog_parse_pos]
    call __rt_make_nil
    mov ecx, eax
    jmp __rt_parse_list_cons
__rt_parse_list_more:
    inc dword ptr [__prolog_parse_pos]
    call __rt_parse_list_elements
    mov ecx, eax
    jmp __rt_parse_list_cons
__rt_parse_list_tail:
    inc dword ptr [__prolog_parse_pos]
    call __rt_parse_relation
    cmp eax, 4294967295
    je __rt_parse_list_fail
    mov ecx, eax
    push ecx
    push 93
    call __rt_parse_consume
    add esp, 4
    pop ecx
    test eax, eax
    je __rt_parse_list_fail
__rt_parse_list_cons:
    push ecx
    push ebx
    call __rt_make_list
    add esp, 8
    jmp __rt_parse_list_done
__rt_parse_list_fail:
    mov eax, 4294967295
__rt_parse_list_done:
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_parse_unary:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    call __rt_parse_skip_ws
    cmp eax, 43
    je __rt_parse_unary_plus
    cmp eax, 45
    jne __rt_parse_unary_primary
    mov esi, dword ptr [__prolog_arena]
    add esi, 720896
    mov ecx, dword ptr [__prolog_parse_pos]
    movzx edx, byte ptr [esi+ecx+1]
    cmp edx, 48
    jb __rt_parse_unary_minus
    cmp edx, 57
    jbe __rt_parse_unary_primary
__rt_parse_unary_minus:
    inc dword ptr [__prolog_parse_pos]
    call __rt_parse_unary
    cmp eax, 4294967295
    je __rt_parse_unary_fail
    push eax
    push 19
    call __rt_make_unary_term
    add esp, 8
    jmp __rt_parse_unary_done
__rt_parse_unary_plus:
    inc dword ptr [__prolog_parse_pos]
    call __rt_parse_unary
    cmp eax, 4294967295
    je __rt_parse_unary_fail
    push eax
    push 18
    call __rt_make_unary_term
    add esp, 8
    jmp __rt_parse_unary_done
__rt_parse_unary_primary:
    call __rt_parse_term
    jmp __rt_parse_unary_done
__rt_parse_unary_fail:
    mov eax, 4294967295
__rt_parse_unary_done:
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_parse_fraction:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    call __rt_parse_unary
    cmp eax, 4294967295
    je __rt_parse_fraction_fail
    mov ebx, eax
    mov eax, ebx
    call __rt_node_ptr
    cmp dword ptr [edi], 3
    je __rt_parse_fraction_numeric
    cmp dword ptr [edi], 9
    jne __rt_parse_fraction_done
__rt_parse_fraction_numeric:
    call __rt_parse_skip_ws
    cmp eax, 47
    jne __rt_parse_fraction_done
    mov esi, dword ptr [__prolog_parse_pos]
    inc dword ptr [__prolog_parse_pos]
    call __rt_parse_skip_ws
    cmp eax, 48
    jb __rt_parse_fraction_sign_check
    cmp eax, 57
    jbe __rt_parse_fraction_rhs
__rt_parse_fraction_sign_check:
    cmp eax, 45
    jne __rt_parse_fraction_restore
    mov edi, dword ptr [__prolog_arena]
    add edi, 720896
    mov ecx, dword ptr [__prolog_parse_pos]
    movzx eax, byte ptr [edi+ecx+1]
    cmp eax, 48
    jb __rt_parse_fraction_restore
    cmp eax, 57
    ja __rt_parse_fraction_restore
__rt_parse_fraction_rhs:
    call __rt_parse_unary
    cmp eax, 4294967295
    je __rt_parse_fraction_restore
    mov edi, eax
    push edi
    push ebx
    push 21
    call __rt_make_binary_term
    add esp, 12
    jmp __rt_parse_fraction_exit
__rt_parse_fraction_restore:
    mov dword ptr [__prolog_parse_pos], esi
__rt_parse_fraction_done:
    mov eax, ebx
    jmp __rt_parse_fraction_exit
__rt_parse_fraction_fail:
    mov eax, 4294967295
__rt_parse_fraction_exit:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_parse_mul:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    call __rt_parse_fraction
    cmp eax, 4294967295
    je __rt_parse_mul_fail
    mov ebx, eax
__rt_parse_mul_loop:
    call __rt_parse_skip_ws
    cmp eax, 42
    je __rt_parse_mul_star
    cmp eax, 47
    je __rt_parse_mul_slash
    cmp eax, 109
    jne __rt_parse_mul_done
    mov esi, dword ptr [__prolog_arena]
    add esi, 720896
    mov ecx, dword ptr [__prolog_parse_pos]
    movzx eax, byte ptr [esi+ecx+1]
    cmp eax, 111
    jne __rt_parse_mul_done
    movzx eax, byte ptr [esi+ecx+2]
    cmp eax, 100
    jne __rt_parse_mul_done
    add dword ptr [__prolog_parse_pos], 3
    mov esi, 22
    jmp __rt_parse_mul_rhs
__rt_parse_mul_star:
    inc dword ptr [__prolog_parse_pos]
    mov esi, 20
    jmp __rt_parse_mul_rhs
__rt_parse_mul_slash:
    inc dword ptr [__prolog_parse_pos]
    mov esi, 21
__rt_parse_mul_rhs:
    call __rt_parse_fraction
    cmp eax, 4294967295
    je __rt_parse_mul_fail
    push eax
    push ebx
    push esi
    call __rt_make_binary_term
    add esp, 12
    mov ebx, eax
    jmp __rt_parse_mul_loop
__rt_parse_mul_done:
    mov eax, ebx
    jmp __rt_parse_mul_exit
__rt_parse_mul_fail:
    mov eax, 4294967295
__rt_parse_mul_exit:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_parse_add:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    call __rt_parse_mul
    cmp eax, 4294967295
    je __rt_parse_add_fail
    mov ebx, eax
__rt_parse_add_loop:
    call __rt_parse_skip_ws
    cmp eax, 43
    je __rt_parse_add_plus
    cmp eax, 45
    je __rt_parse_add_minus
    jmp __rt_parse_add_done
__rt_parse_add_plus:
    inc dword ptr [__prolog_parse_pos]
    mov esi, 18
    jmp __rt_parse_add_rhs
__rt_parse_add_minus:
    inc dword ptr [__prolog_parse_pos]
    mov esi, 19
__rt_parse_add_rhs:
    call __rt_parse_mul
    cmp eax, 4294967295
    je __rt_parse_add_fail
    push eax
    push ebx
    push esi
    call __rt_make_binary_term
    add esp, 12
    mov ebx, eax
    jmp __rt_parse_add_loop
__rt_parse_add_done:
    mov eax, ebx
    jmp __rt_parse_add_exit
__rt_parse_add_fail:
    mov eax, 4294967295
__rt_parse_add_exit:
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_parse_relation:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    call __rt_parse_add
    cmp eax, 4294967295
    je __rt_parse_rel_fail
    mov ebx, eax
    call __rt_parse_skip_ws
    cmp eax, 105
    jne __rt_parse_rel_symbol
    mov esi, dword ptr [__prolog_arena]
    add esi, 720896
    mov ecx, dword ptr [__prolog_parse_pos]
    movzx eax, byte ptr [esi+ecx+1]
    cmp eax, 115
    jne __rt_parse_rel_none
    add dword ptr [__prolog_parse_pos], 2
    mov esi, 13
    jmp __rt_parse_rel_rhs
__rt_parse_rel_symbol:
    cmp eax, 61
    je __rt_parse_rel_eq
    cmp eax, 92
    je __rt_parse_rel_ne
    cmp eax, 60
    je __rt_parse_rel_lt
    cmp eax, 62
    je __rt_parse_rel_gt
    jmp __rt_parse_rel_none
__rt_parse_rel_eq:
    inc dword ptr [__prolog_parse_pos]
    call __rt_parse_skip_ws
    mov esi, 10
    cmp eax, 61
    jne __rt_parse_rel_eq_le
    inc dword ptr [__prolog_parse_pos]
    mov esi, 12
    jmp __rt_parse_rel_rhs
__rt_parse_rel_eq_le:
    cmp eax, 60
    jne __rt_parse_rel_rhs
    inc dword ptr [__prolog_parse_pos]
    mov esi, 15
    jmp __rt_parse_rel_rhs
__rt_parse_rel_ne:
    inc dword ptr [__prolog_parse_pos]
    push 61
    call __rt_parse_consume
    add esp, 4
    test eax, eax
    je __rt_parse_rel_none
    mov esi, 11
    jmp __rt_parse_rel_rhs
__rt_parse_rel_lt:
    inc dword ptr [__prolog_parse_pos]
    call __rt_parse_skip_ws
    mov esi, 14
    cmp eax, 61
    jne __rt_parse_rel_rhs
    inc dword ptr [__prolog_parse_pos]
    mov esi, 15
    jmp __rt_parse_rel_rhs
__rt_parse_rel_gt:
    inc dword ptr [__prolog_parse_pos]
    call __rt_parse_skip_ws
    mov esi, 16
    cmp eax, 61
    jne __rt_parse_rel_rhs
    inc dword ptr [__prolog_parse_pos]
    mov esi, 17
__rt_parse_rel_rhs:
    call __rt_parse_add
    cmp eax, 4294967295
    je __rt_parse_rel_fail
    push eax
    push ebx
    push esi
    call __rt_make_binary_term
    add esp, 12
    jmp __rt_parse_rel_done
__rt_parse_rel_none:
    mov eax, ebx
    jmp __rt_parse_rel_done
__rt_parse_rel_fail:
    mov eax, 4294967295
__rt_parse_rel_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_parse_conjunction:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    call __rt_parse_relation
    cmp eax, 4294967295
    je __rt_parse_conjunction_fail
    mov ebx, eax
    call __rt_parse_skip_ws
    cmp eax, 44
    jne __rt_parse_conjunction_done
    inc dword ptr [__prolog_parse_pos]
    call __rt_parse_conjunction
    cmp eax, 4294967295
    je __rt_parse_conjunction_fail
    push eax
    push ebx
    push 3
    call __rt_make_binary_term
    add esp, 12
    jmp __rt_parse_conjunction_exit
__rt_parse_conjunction_done:
    mov eax, ebx
    jmp __rt_parse_conjunction_exit
__rt_parse_conjunction_fail:
    mov eax, 4294967295
__rt_parse_conjunction_exit:
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_parse_disjunction:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    call __rt_parse_conjunction
    cmp eax, 4294967295
    je __rt_parse_disjunction_fail
    mov ebx, eax
    call __rt_parse_skip_ws
    cmp eax, 59
    jne __rt_parse_disjunction_done
    inc dword ptr [__prolog_parse_pos]
    call __rt_parse_disjunction
    cmp eax, 4294967295
    je __rt_parse_disjunction_fail
    push eax
    push ebx
    push 4
    call __rt_make_binary_term
    add esp, 12
    jmp __rt_parse_disjunction_exit
__rt_parse_disjunction_done:
    mov eax, ebx
    jmp __rt_parse_disjunction_exit
__rt_parse_disjunction_fail:
    mov eax, 4294967295
__rt_parse_disjunction_exit:
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_parse_rule_expr:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    call __rt_parse_disjunction
    cmp eax, 4294967295
    je __rt_parse_rule_fail
    mov ebx, eax
    call __rt_parse_skip_ws
    cmp eax, 58
    jne __rt_parse_rule_done
    mov esi, dword ptr [__prolog_arena]
    add esi, 720896
    mov ecx, dword ptr [__prolog_parse_pos]
    movzx eax, byte ptr [esi+ecx+1]
    cmp eax, 45
    jne __rt_parse_rule_done
    add dword ptr [__prolog_parse_pos], 2
    call __rt_parse_disjunction
    cmp eax, 4294967295
    je __rt_parse_rule_fail
    push eax
    push ebx
    push 5
    call __rt_make_binary_term
    add esp, 12
    jmp __rt_parse_rule_exit
__rt_parse_rule_done:
    mov eax, ebx
    jmp __rt_parse_rule_exit
__rt_parse_rule_fail:
    mov eax, 4294967295
__rt_parse_rule_exit:
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_parse_goal:
    jmp __rt_parse_relation

__rt_parse_goal_list:
    push ebp
    mov ebp, esp
    call __rt_parse_disjunction
    cmp eax, 4294967295
    je __rt_parse_goal_list_done
    push 0
    push 4294967295
    push eax
    call __rt_goal_expr_to_chain
    add esp, 12
    push eax
    call __rt_parse_skip_ws
    cmp eax, 46
    jne __rt_parse_goal_list_after_dot
    inc dword ptr [__prolog_parse_pos]
__rt_parse_goal_list_after_dot:
    call __rt_parse_skip_ws
    test eax, eax
    je __rt_parse_goal_list_valid_end
    pop ecx
    mov eax, 4294967295
    jmp __rt_parse_goal_list_done
__rt_parse_goal_list_valid_end:
    pop eax
__rt_parse_goal_list_done:
    mov esp, ebp
    pop ebp
    ret

__rt_is_knowledge_start:
    push ebp
    mov ebp, esp
    push esi
    mov esi, dword ptr [__prolog_arena]
    add esi, 720896
    mov ecx, dword ptr [__prolog_parse_pos]
    movzx eax, byte ptr [esi+ecx]
    cmp eax, 95
    jne __rt_is_knowledge_start_no
    movzx eax, byte ptr [esi+ecx+1]
    cmp eax, 97
    jb __rt_is_knowledge_start_latin1
    cmp eax, 122
    jbe __rt_is_knowledge_start_yes
__rt_is_knowledge_start_latin1:
    cmp eax, 223
    je __rt_is_knowledge_start_yes
    cmp eax, 228
    je __rt_is_knowledge_start_yes
    cmp eax, 246
    je __rt_is_knowledge_start_yes
    cmp eax, 252
    je __rt_is_knowledge_start_yes
    cmp eax, 195
    jne __rt_is_knowledge_start_no
    movzx eax, byte ptr [esi+ecx+2]
    cmp eax, 159
    je __rt_is_knowledge_start_yes
    cmp eax, 164
    je __rt_is_knowledge_start_yes
    cmp eax, 182
    je __rt_is_knowledge_start_yes
    cmp eax, 188
    je __rt_is_knowledge_start_yes
    jmp __rt_is_knowledge_start_no
__rt_is_knowledge_start_yes:
    mov eax, 1
    jmp __rt_is_knowledge_start_done
__rt_is_knowledge_start_no:
    xor eax, eax
__rt_is_knowledge_start_done:
    pop esi
    mov esp, ebp
    pop ebp
    ret

__rt_parse_knowledge_string_expr:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov esi, dword ptr [__prolog_parse_pos]
    xor ebx, ebx
    mov edi, dword ptr [__prolog_arena]
    add edi, 779776
    xor eax, eax
    mov byte ptr [edi], al
__rt_parse_knowledge_string_operand:
    call __rt_parse_skip_ws
    cmp eax, 34
    je __rt_parse_knowledge_string_literal
    cmp eax, 95
    jne __rt_parse_knowledge_string_fail
    call __rt_is_knowledge_start
    test eax, eax
    je __rt_parse_knowledge_string_fail
    call __rt_parse_token
    cmp ecx, 2
    jb __rt_parse_knowledge_string_fail
    dec ecx
    inc eax
    push ecx
    push eax
    call __rt_intern_atom
    add esp, 8
    push eax
    call __rt_db_lookup_knowledge_string
    add esp, 4
    test edx, edx
    je __rt_parse_knowledge_string_fail
    jmp __rt_parse_knowledge_string_append
__rt_parse_knowledge_string_literal:
    call __rt_parse_term
    cmp eax, 4294967295
    je __rt_parse_knowledge_string_fail
    push eax
    call __rt_term_cstr
    add esp, 4
    test edx, edx
    je __rt_parse_knowledge_string_fail
__rt_parse_knowledge_string_append:
    push ebx
    push eax
    call __rt_knowledge_concat_append
    add esp, 8
    test edx, edx
    je __rt_parse_knowledge_string_fail
    mov ebx, eax
    call __rt_parse_skip_ws
    cmp eax, 43
    jne __rt_parse_knowledge_string_finish
    inc dword ptr [__prolog_parse_pos]
    jmp __rt_parse_knowledge_string_operand
__rt_parse_knowledge_string_finish:
    mov edi, dword ptr [__prolog_arena]
    add edi, 779776
    push ebx
    push edi
    call __rt_intern_atom
    add esp, 8
    push eax
    call __rt_make_string
    add esp, 4
    jmp __rt_parse_knowledge_string_done
__rt_parse_knowledge_string_fail:
    mov dword ptr [__prolog_parse_pos], esi
    mov eax, 4294967295
__rt_parse_knowledge_string_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_parse_knowledge_assignment:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [__prolog_parse_pos]
    call __rt_parse_skip_ws
    call __rt_is_knowledge_start
    test eax, eax
    je __rt_parse_knowledge_fail
    call __rt_parse_token
    cmp ecx, 2
    jb __rt_parse_knowledge_fail
    dec ecx
    inc eax
    push ecx
    push eax
    call __rt_intern_atom
    add esp, 8
    mov edi, eax
    call __rt_parse_skip_ws
    cmp eax, 61
    jne __rt_parse_knowledge_fail
    mov esi, dword ptr [__prolog_arena]
    add esi, 720896
    mov ecx, dword ptr [__prolog_parse_pos]
    movzx eax, byte ptr [esi+ecx+1]
    cmp eax, 61
    je __rt_parse_knowledge_fail
    cmp eax, 60
    je __rt_parse_knowledge_fail
    inc dword ptr [__prolog_parse_pos]
    call __rt_parse_skip_ws
    cmp eax, 34
    je __rt_parse_knowledge_string_required
    cmp eax, 95
    jne __rt_parse_knowledge_generic_rhs
    call __rt_is_knowledge_start
    test eax, eax
    je __rt_parse_knowledge_generic_rhs
__rt_parse_knowledge_string_required:
    call __rt_parse_knowledge_string_expr
    cmp eax, 4294967295
    je __rt_parse_knowledge_fail
    mov esi, eax
    jmp __rt_parse_knowledge_build
__rt_parse_knowledge_generic_rhs:
    push edi
    call __rt_parse_disjunction
    pop edi
    cmp eax, 4294967295
    je __rt_parse_knowledge_fail
    mov esi, eax
__rt_parse_knowledge_build:
    push edi
    call __rt_make_atom
    add esp, 4
    push esi
    push eax
    push 75
    call __rt_make_binary_term
    add esp, 12
    jmp __rt_parse_knowledge_done
__rt_parse_knowledge_fail:
    mov dword ptr [__prolog_parse_pos], ebx
    mov eax, 4294967295
__rt_parse_knowledge_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_parse_query:
    push ebp
    mov ebp, esp
    push esi
    call __rt_parse_skip_ws
    cmp eax, 63
    jne __rt_parse_query_goals
    inc dword ptr [__prolog_parse_pos]
    push 45
    call __rt_parse_consume
    add esp, 4
    test eax, eax
    je __rt_parse_query_fail
__rt_parse_query_goals:
    call __rt_parse_goal_list
    jmp __rt_parse_query_done
__rt_parse_query_fail:
    mov eax, 4294967295
__rt_parse_query_done:
    pop esi
    mov esp, ebp
    pop ebp
    ret

__rt_term_int:
    push ebp
    mov ebp, esp
    push edi
    mov eax, dword ptr [ebp+8]
    call __rt_deref
    call __rt_node_ptr
    cmp dword ptr [edi], 3
    jne __rt_term_int_fail
    mov eax, dword ptr [edi+4]
    mov edx, 1
    jmp __rt_term_int_done
__rt_term_int_fail:
    xor eax, eax
    xor edx, edx
__rt_term_int_done:
    pop edi
    mov esp, ebp
    pop ebp
    ret

__rt_term_atom_id:
    push ebp
    mov ebp, esp
    push edi
    mov eax, dword ptr [ebp+8]
    call __rt_deref
    call __rt_node_ptr
    cmp dword ptr [edi], 2
    jne __rt_term_atom_id_fail
    mov eax, dword ptr [edi+4]
    mov edx, 1
    jmp __rt_term_atom_id_done
__rt_term_atom_id_fail:
    xor eax, eax
    xor edx, edx
__rt_term_atom_id_done:
    pop edi
    mov esp, ebp
    pop ebp
    ret

__rt_term_cstr:
    push ebp
    mov ebp, esp
    push edi
    mov eax, dword ptr [ebp+8]
    call __rt_deref
    call __rt_node_ptr
    cmp dword ptr [edi], 2
    je __rt_term_cstr_have_id
    cmp dword ptr [edi], 4
    jne __rt_term_cstr_fail
__rt_term_cstr_have_id:
    push dword ptr [edi+4]
    call __rt_atom_ptr
    add esp, 4
    test eax, eax
    je __rt_term_cstr_fail
    mov edx, 1
    jmp __rt_term_cstr_done
__rt_term_cstr_fail:
    xor eax, eax
    xor edx, edx
__rt_term_cstr_done:
    pop edi
    mov esp, ebp
    pop ebp
    ret

__rt_cstr_copy_limit:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov esi, dword ptr [ebp+8]
    mov edi, dword ptr [ebp+12]
    mov ebx, dword ptr [ebp+16]
    test ebx, ebx
    je __rt_cstr_copy_fail
    xor ecx, ecx
__rt_cstr_copy_loop:
    mov eax, ebx
    dec eax
    cmp ecx, eax
    jae __rt_cstr_copy_last
    movzx eax, byte ptr [esi+ecx]
    mov byte ptr [edi+ecx], al
    test eax, eax
    je __rt_cstr_copy_ok
    inc ecx
    jmp __rt_cstr_copy_loop
__rt_cstr_copy_last:
    xor eax, eax
    mov byte ptr [edi+ecx], al
    movzx eax, byte ptr [esi+ecx]
    test eax, eax
    je __rt_cstr_copy_ok
__rt_cstr_copy_fail:
    xor eax, eax
    jmp __rt_cstr_copy_done
__rt_cstr_copy_ok:
    mov eax, 1
__rt_cstr_copy_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_knowledge_concat_append:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov esi, dword ptr [ebp+8]
    mov ebx, dword ptr [ebp+12]
    cmp ebx, 6143
    jae __rt_knowledge_concat_append_fail
    mov edi, dword ptr [__prolog_arena]
    add edi, 779776
    add edi, ebx
    xor ecx, ecx
__rt_knowledge_concat_append_loop:
    movzx eax, byte ptr [esi+ecx]
    test eax, eax
    je __rt_knowledge_concat_append_ok
    cmp ebx, 6143
    jae __rt_knowledge_concat_append_fail
    mov byte ptr [edi], al
    inc edi
    inc ebx
    inc ecx
    jmp __rt_knowledge_concat_append_loop
__rt_knowledge_concat_append_ok:
    xor eax, eax
    mov byte ptr [edi], al
    mov eax, ebx
    mov edx, 1
    jmp __rt_knowledge_concat_append_done
__rt_knowledge_concat_append_fail:
    xor eax, eax
    xor edx, edx
__rt_knowledge_concat_append_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_db_lookup_knowledge_string:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [ebp+8]
    mov esi, dword ptr [__prolog_dyn_count]
__rt_db_lookup_knowledge_string_loop:
    test esi, esi
    je __rt_db_lookup_knowledge_string_fail
    dec esi
    mov edi, dword ptr [__prolog_arena]
    add edi, 743424
    mov eax, esi
    shl eax, 4
    add edi, eax
    cmp dword ptr [edi], 0
    je __rt_db_lookup_knowledge_string_loop
    cmp dword ptr [edi+4], 75
    jne __rt_db_lookup_knowledge_string_loop
    cmp dword ptr [edi+8], 2
    jne __rt_db_lookup_knowledge_string_loop
    mov eax, dword ptr [edi+12]
    call __rt_dyn_ptr
    cmp dword ptr [edi], 7
    jne __rt_db_lookup_knowledge_string_loop
    mov eax, dword ptr [edi+12]
    call __rt_dyn_ptr
    cmp dword ptr [edi], 8
    jne __rt_db_lookup_knowledge_string_loop
    mov ecx, dword ptr [edi+8]
    mov edx, dword ptr [edi+12]
    push edx
    mov eax, ecx
    call __rt_dyn_ptr
    cmp dword ptr [edi], 2
    jne __rt_db_lookup_knowledge_string_pop_next
    cmp dword ptr [edi+4], ebx
    jne __rt_db_lookup_knowledge_string_pop_next
    pop eax
    call __rt_dyn_ptr
    cmp dword ptr [edi], 8
    jne __rt_db_lookup_knowledge_string_loop
    mov eax, dword ptr [edi+8]
    call __rt_dyn_ptr
    cmp dword ptr [edi], 4
    jne __rt_db_lookup_knowledge_string_loop
    push dword ptr [edi+4]
    call __rt_atom_ptr
    add esp, 4
    test eax, eax
    je __rt_db_lookup_knowledge_string_loop
    mov edx, 1
    jmp __rt_db_lookup_knowledge_string_done
__rt_db_lookup_knowledge_string_pop_next:
    pop eax
    jmp __rt_db_lookup_knowledge_string_loop
__rt_db_lookup_knowledge_string_fail:
    xor eax, eax
    xor edx, edx
__rt_db_lookup_knowledge_string_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_db_filename_ptr:
    push ebp
    mov ebp, esp
    push ebx
    push edi
    mov ebx, dword ptr [ebp+8]
    mov eax, ebx
    shl eax, 8
    mov ecx, ebx
    shl ecx, 2
    add eax, ecx
    mov edi, dword ptr [__prolog_arena]
    add edi, 770688
    add edi, eax
    mov eax, edi
    pop edi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_db_find_slot:
    push ebp
    mov ebp, esp
    push ebx
    push edi
    mov ebx, dword ptr [ebp+8]
    xor ecx, ecx
__rt_db_find_slot_loop:
    cmp ecx, 32
    jae __rt_db_find_slot_fail
    mov edi, dword ptr [__prolog_arena]
    add edi, 770048
    cmp dword ptr [edi+ecx*4], 0
    je __rt_db_find_slot_next
    mov edi, dword ptr [__prolog_arena]
    add edi, 770176
    cmp dword ptr [edi+ecx*4], ebx
    je __rt_db_find_slot_found
__rt_db_find_slot_next:
    inc ecx
    jmp __rt_db_find_slot_loop
__rt_db_find_slot_found:
    mov eax, ecx
    jmp __rt_db_find_slot_done
__rt_db_find_slot_fail:
    mov eax, 4294967295
__rt_db_find_slot_done:
    pop edi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_db_find_free_slot:
    push ebp
    mov ebp, esp
    push edi
    xor ecx, ecx
__rt_db_find_free_loop:
    cmp ecx, 32
    jae __rt_db_find_free_fail
    mov edi, dword ptr [__prolog_arena]
    add edi, 770048
    cmp dword ptr [edi+ecx*4], 0
    je __rt_db_find_free_found
    inc ecx
    jmp __rt_db_find_free_loop
__rt_db_find_free_found:
    mov eax, ecx
    jmp __rt_db_find_free_done
__rt_db_find_free_fail:
    mov eax, 4294967295
__rt_db_find_free_done:
    pop edi
    mov esp, ebp
    pop ebp
    ret

__rt_db_can_modify_id:
    push ebp
    mov ebp, esp
    push ebx
    push edi
    push dword ptr [ebp+8]
    call __rt_db_find_slot
    add esp, 4
    cmp eax, 4294967295
    je __rt_db_can_modify_no
    mov ebx, eax
    mov edi, dword ptr [__prolog_arena]
    add edi, 770304
    cmp dword ptr [edi+ebx*4], 1
    jne __rt_db_can_modify_no
    mov edi, dword ptr [__prolog_arena]
    add edi, 770432
    cmp dword ptr [edi+ebx*4], 3
    je __rt_db_can_modify_no
    mov eax, 1
    jmp __rt_db_can_modify_done
__rt_db_can_modify_no:
    xor eax, eax
__rt_db_can_modify_done:
    pop edi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_db_mark_modified_id:
    push ebp
    mov ebp, esp
    push ebx
    push edi
    cmp dword ptr [__prolog_db_loading], 0
    jne __rt_db_mark_modified_done
    push dword ptr [ebp+8]
    call __rt_db_find_slot
    add esp, 4
    cmp eax, 4294967295
    je __rt_db_mark_modified_done
    mov ebx, eax
    mov edi, dword ptr [__prolog_arena]
    add edi, 770560
    mov dword ptr [edi+ebx*4], 1
__rt_db_mark_modified_done:
    mov eax, 1
    pop edi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_db_mode_from_term:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __rt_term_atom_id
    add esp, 4
    test edx, edx
    je __rt_db_mode_fail
    cmp eax, 70
    je __rt_db_mode_ro
    cmp eax, 71
    je __rt_db_mode_rw
    jmp __rt_db_mode_fail
__rt_db_mode_ro:
    mov eax, 0
    jmp __rt_db_mode_done
__rt_db_mode_rw:
    mov eax, 1
    jmp __rt_db_mode_done
__rt_db_mode_fail:
    mov eax, 4294967295
__rt_db_mode_done:
    mov esp, ebp
    pop ebp
    ret

__rt_db_kind_from_term:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call __rt_term_atom_id
    add esp, 4
    test edx, edx
    je __rt_db_kind_fail
    cmp eax, 72
    je __rt_db_kind_knowledge
    cmp eax, 73
    je __rt_db_kind_record
    cmp eax, 74
    je __rt_db_kind_system
    jmp __rt_db_kind_fail
__rt_db_kind_knowledge:
    mov eax, 1
    jmp __rt_db_kind_done
__rt_db_kind_record:
    mov eax, 2
    jmp __rt_db_kind_done
__rt_db_kind_system:
    mov eax, 3
    jmp __rt_db_kind_done
__rt_db_kind_fail:
    mov eax, 4294967295
__rt_db_kind_done:
    mov esp, ebp
    pop ebp
    ret

__rt_db_make_temp_path:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    push dword ptr [ebp+8]
    call __rt_db_filename_ptr
    add esp, 4
    mov esi, eax
    mov edi, dword ptr [__prolog_arena]
    add edi, 779008
    xor ebx, ebx
__rt_db_temp_copy:
    cmp ebx, 255
    jae __rt_db_temp_fail
    movzx eax, byte ptr [esi+ebx]
    test eax, eax
    je __rt_db_temp_suffix
    mov byte ptr [edi+ebx], al
    inc ebx
    jmp __rt_db_temp_copy
__rt_db_temp_suffix:
    mov byte ptr [edi+ebx], 46
    inc ebx
    mov byte ptr [edi+ebx], 116
    inc ebx
    mov byte ptr [edi+ebx], 109
    inc ebx
    mov byte ptr [edi+ebx], 112
    inc ebx
    mov byte ptr [edi+ebx], 0
    mov eax, edi
    jmp __rt_db_temp_done
__rt_db_temp_fail:
    xor eax, eax
__rt_db_temp_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_emit_saved_var:
    push ebp
    mov ebp, esp
    push ebx
    push edi
    mov ebx, dword ptr [ebp+8]
    xor ecx, ecx
__rt_emit_saved_var_scan:
    cmp ecx, dword ptr [__prolog_save_var_count]
    jae __rt_emit_saved_var_new
    mov edi, dword ptr [__prolog_arena]
    add edi, 765952
    cmp dword ptr [edi+ecx*4], ebx
    je __rt_emit_saved_var_have
    inc ecx
    jmp __rt_emit_saved_var_scan
__rt_emit_saved_var_new:
    cmp ecx, 256
    jae __rt_emit_saved_var_have
    mov edi, dword ptr [__prolog_arena]
    add edi, 765952
    mov dword ptr [edi+ecx*4], ebx
    inc dword ptr [__prolog_save_var_count]
__rt_emit_saved_var_have:
    push ecx
    push __prolog_fmt_saved_var
    push __prolog_format_buffer
    call wsprintfA
    add esp, 12
    push __prolog_format_buffer
    call __rt_emit_text
    add esp, 4
    mov eax, 1
    pop edi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_emit_source_expr:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov eax, dword ptr [ebp+8]
    call __rt_deref
    mov esi, eax
    call __rt_node_ptr
    cmp dword ptr [edi], 7
    jne __rt_emit_source_expr_generic
    cmp dword ptr [edi+8], 2
    jne __rt_emit_source_expr_generic
    mov edx, dword ptr [edi+4]
    cmp edx, 3
    je __rt_emit_source_expr_op_0
    cmp edx, 4
    je __rt_emit_source_expr_op_1
    cmp edx, 10
    je __rt_emit_source_expr_op_2
    cmp edx, 11
    je __rt_emit_source_expr_op_3
    cmp edx, 12
    je __rt_emit_source_expr_op_4
    cmp edx, 13
    je __rt_emit_source_expr_op_5
    cmp edx, 14
    je __rt_emit_source_expr_op_6
    cmp edx, 15
    je __rt_emit_source_expr_op_7
    cmp edx, 16
    je __rt_emit_source_expr_op_8
    cmp edx, 17
    je __rt_emit_source_expr_op_9
    cmp edx, 18
    je __rt_emit_source_expr_op_10
    cmp edx, 19
    je __rt_emit_source_expr_op_11
    cmp edx, 20
    je __rt_emit_source_expr_op_12
    cmp edx, 21
    je __rt_emit_source_expr_op_13
    cmp edx, 22
    je __rt_emit_source_expr_op_14
    jmp __rt_emit_source_expr_generic
__rt_emit_source_expr_op_0:
    mov ebx, __prolog_text_op_comma
    jmp __rt_emit_source_expr_binary
__rt_emit_source_expr_op_1:
    mov ebx, __prolog_text_op_semi
    jmp __rt_emit_source_expr_binary
__rt_emit_source_expr_op_2:
    mov ebx, __prolog_text_op_eq
    jmp __rt_emit_source_expr_binary
__rt_emit_source_expr_op_3:
    mov ebx, __prolog_text_op_ne
    jmp __rt_emit_source_expr_binary
__rt_emit_source_expr_op_4:
    mov ebx, __prolog_text_op_strict_eq
    jmp __rt_emit_source_expr_binary
__rt_emit_source_expr_op_5:
    mov ebx, __prolog_text_op_is
    jmp __rt_emit_source_expr_binary
__rt_emit_source_expr_op_6:
    mov ebx, __prolog_text_op_lt
    jmp __rt_emit_source_expr_binary
__rt_emit_source_expr_op_7:
    mov ebx, __prolog_text_op_le
    jmp __rt_emit_source_expr_binary
__rt_emit_source_expr_op_8:
    mov ebx, __prolog_text_op_gt
    jmp __rt_emit_source_expr_binary
__rt_emit_source_expr_op_9:
    mov ebx, __prolog_text_op_ge
    jmp __rt_emit_source_expr_binary
__rt_emit_source_expr_op_10:
    mov ebx, __prolog_text_op_plus
    jmp __rt_emit_source_expr_binary
__rt_emit_source_expr_op_11:
    mov ebx, __prolog_text_op_minus
    jmp __rt_emit_source_expr_binary
__rt_emit_source_expr_op_12:
    mov ebx, __prolog_text_op_mul
    jmp __rt_emit_source_expr_binary
__rt_emit_source_expr_op_13:
    mov ebx, __prolog_text_op_div
    jmp __rt_emit_source_expr_binary
__rt_emit_source_expr_op_14:
    mov ebx, __prolog_text_op_mod
    jmp __rt_emit_source_expr_binary
__rt_emit_source_expr_binary:
    push __prolog_text_lparen
    call __rt_emit_text
    add esp, 4
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_emit_source_expr
    add esp, 4
    push ebx
    call __rt_emit_text
    add esp, 4
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_emit_source_expr
    add esp, 4
    push __prolog_text_rparen
    call __rt_emit_text
    add esp, 4
    jmp __rt_emit_source_expr_done
__rt_emit_source_expr_generic:
    push esi
    call __rt_emit_term
    add esp, 4
__rt_emit_source_expr_done:
    mov eax, 1
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_emit_clause_source:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov eax, dword ptr [ebp+8]
    call __rt_deref
    mov esi, eax
    call __rt_node_ptr
    cmp dword ptr [edi], 7
    jne __rt_emit_clause_fact
    cmp dword ptr [edi+4], 75
    jne __rt_emit_clause_check_rule
    cmp dword ptr [edi+8], 2
    je __rt_emit_clause_knowledge
__rt_emit_clause_check_rule:
    cmp dword ptr [edi+4], 5
    jne __rt_emit_clause_fact
    cmp dword ptr [edi+8], 2
    jne __rt_emit_clause_fact
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_emit_term
    add esp, 4
    push __prolog_text_rule_sep
    call __rt_emit_text
    add esp, 4
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_emit_source_expr
    add esp, 4
    jmp __rt_emit_clause_done
__rt_emit_clause_knowledge:
    push __prolog_text_underscore
    call __rt_emit_text
    add esp, 4
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_emit_term
    add esp, 4
    push __prolog_text_knowledge_sep
    call __rt_emit_text
    add esp, 4
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_emit_source_expr
    add esp, 4
    jmp __rt_emit_clause_done
__rt_emit_clause_fact:
    push esi
    call __rt_emit_term
    add esp, 4
__rt_emit_clause_done:
    mov eax, 1
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_db_load_slot:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [ebp+8]
    push ebx
    call __rt_db_filename_ptr
    add esp, 4
    mov esi, eax
    push 0
    push 128
    push 3
    push 0
    push 1
    push -2147483648
    push esi
    call CreateFileA
    cmp eax, -1
    jne __rt_db_load_have_file
    mov edi, dword ptr [__prolog_arena]
    add edi, 770304
    cmp dword ptr [edi+ebx*4], 1
    jne __rt_db_load_fail
    push 0
    push 128
    push 2
    push 0
    push 0
    push 1073741824
    push esi
    call CreateFileA
    cmp eax, -1
    je __rt_db_load_fail
    push eax
    call CloseHandle
    mov eax, 1
    jmp __rt_db_load_done
__rt_db_load_have_file:
    mov dword ptr [__prolog_db_file_handle], eax
    mov edi, dword ptr [__prolog_arena]
    add edi, 1310720
    mov dword ptr [__prolog_db_file_read], 0
    push 0
    push __prolog_db_file_read
    push 1048575
    push edi
    push dword ptr [__prolog_db_file_handle]
    call ReadFile
    test eax, eax
    je __rt_db_load_close_fail
    push dword ptr [__prolog_db_file_handle]
    call CloseHandle
    mov dword ptr [__prolog_db_file_handle], 0
    mov ecx, dword ptr [__prolog_db_file_read]
    cmp ecx, 1048575
    jae __rt_db_load_fail
    mov edi, dword ptr [__prolog_arena]
    add edi, 1310720
    xor eax, eax
    mov byte ptr [edi+ecx], al
    mov dword ptr [__prolog_db_file_pos], 0
    mov dword ptr [__prolog_parser_db_mode], 1
__rt_db_load_clause_loop:
    mov esi, dword ptr [__prolog_arena]
    add esi, 1310720
    mov eax, dword ptr [__prolog_db_file_pos]
    add esi, eax
    mov edi, dword ptr [__prolog_arena]
    add edi, 720896
    xor ecx, ecx
__rt_db_load_window_copy:
    cmp ecx, 4095
    jae __rt_db_load_window_full
    movzx eax, byte ptr [esi+ecx]
    mov byte ptr [edi+ecx], al
    test eax, eax
    je __rt_db_load_window_ready
    inc ecx
    jmp __rt_db_load_window_copy
__rt_db_load_window_full:
    xor eax, eax
    mov byte ptr [edi+ecx], al
__rt_db_load_window_ready:
    mov dword ptr [__prolog_parse_pos], 0
    call __rt_parse_skip_ws
    test eax, eax
    je __rt_db_load_success
    mov eax, dword ptr [__prolog_heap_top]
    mov dword ptr [__prolog_db_heap_mark], eax
    mov dword ptr [__prolog_db_parser_var_count], 0
    mov dword ptr [__prolog_db_parser_name_top], 0
    call __rt_parse_knowledge_assignment
    cmp eax, 4294967295
    jne __rt_db_load_clause_parsed
    call __rt_parse_rule_expr
    cmp eax, 4294967295
    je __rt_db_load_parse_fail
__rt_db_load_clause_parsed:
    mov ebx, eax
    call __rt_parse_skip_ws
    cmp eax, 46
    jne __rt_db_load_parse_fail
    inc dword ptr [__prolog_parse_pos]
    call __rt_parse_skip_ws
    push ebx
    call __rt_assertz
    add esp, 4
    mov edx, eax
    mov eax, dword ptr [__prolog_db_heap_mark]
    mov dword ptr [__prolog_heap_top], eax
    test edx, edx
    je __rt_db_load_fail
    mov eax, dword ptr [__prolog_parse_pos]
    test eax, eax
    je __rt_db_load_fail
    add dword ptr [__prolog_db_file_pos], eax
    jmp __rt_db_load_clause_loop
__rt_db_load_parse_fail:
    mov eax, dword ptr [__prolog_db_heap_mark]
    mov dword ptr [__prolog_heap_top], eax
    jmp __rt_db_load_fail
__rt_db_load_close_fail:
    push dword ptr [__prolog_db_file_handle]
    call CloseHandle
    mov dword ptr [__prolog_db_file_handle], 0
    jmp __rt_db_load_fail
__rt_db_load_success:
    mov dword ptr [__prolog_parser_db_mode], 0
    mov eax, 1
    jmp __rt_db_load_done
__rt_db_load_fail:
    mov dword ptr [__prolog_parser_db_mode], 0
    xor eax, eax
__rt_db_load_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_database_open:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [ebp+12]
    mov esi, dword ptr [ebp+16]
    cmp esi, 3
    jne __rt_database_open_mode_ok
    cmp ebx, 0
    jne __rt_database_open_fail
__rt_database_open_mode_ok:
    push dword ptr [ebp+8]
    call __rt_term_cstr
    add esp, 4
    test edx, edx
    je __rt_database_open_fail
    push eax
    call __rt_db_find_free_slot
    cmp eax, 4294967295
    je __rt_database_open_fail_pop
    mov ecx, eax
    push ecx
    call __rt_db_filename_ptr
    add esp, 4
    mov edi, eax
    pop eax
    push 260
    push edi
    push eax
    call __rt_cstr_copy_limit
    add esp, 12
    test eax, eax
    je __rt_database_open_fail
    mov eax, dword ptr [__prolog_db_next_id]
    test eax, eax
    jne __rt_database_open_id_ok
    mov eax, 1
__rt_database_open_id_ok:
    mov edx, eax
    inc eax
    mov dword ptr [__prolog_db_next_id], eax
    call __rt_db_find_free_slot
    cmp eax, 4294967295
    je __rt_database_open_fail
    mov ecx, eax
    mov edi, dword ptr [__prolog_arena]
    add edi, 770048
    mov dword ptr [edi+ecx*4], 1
    mov edi, dword ptr [__prolog_arena]
    add edi, 770176
    mov dword ptr [edi+ecx*4], edx
    mov edi, dword ptr [__prolog_arena]
    add edi, 770304
    mov dword ptr [edi+ecx*4], ebx
    mov edi, dword ptr [__prolog_arena]
    add edi, 770432
    mov dword ptr [edi+ecx*4], esi
    mov edi, dword ptr [__prolog_arena]
    add edi, 770560
    mov dword ptr [edi+ecx*4], 0
    push edx
    mov eax, dword ptr [__prolog_current_db]
    push eax
    mov dword ptr [__prolog_current_db], edx
    mov dword ptr [__prolog_db_loading], 1
    push ecx
    call __rt_db_load_slot
    add esp, 4
    mov esi, eax
    mov dword ptr [__prolog_db_loading], 0
    pop ecx
    pop edx
    mov dword ptr [__prolog_current_db], ecx
    test esi, esi
    je __rt_database_open_cleanup
    push edx
    call __rt_db_find_slot
    add esp, 4
    cmp eax, 4294967295
    je __rt_database_open_fail
    mov ecx, eax
    mov edi, dword ptr [__prolog_arena]
    add edi, 770560
    mov dword ptr [edi+ecx*4], 0
    mov eax, edx
    jmp __rt_database_open_done
__rt_database_open_cleanup:
    push edx
    call __rt_db_unload_id
    add esp, 4
    xor eax, eax
    jmp __rt_database_open_done
__rt_database_open_fail_pop:
    pop eax
__rt_database_open_fail:
    xor eax, eax
__rt_database_open_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_db_unload_id:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [ebp+8]
    xor esi, esi
__rt_db_unload_clause_loop:
    cmp esi, dword ptr [__prolog_dyn_count]
    jae __rt_db_unload_clause_done
    mov edi, dword ptr [__prolog_arena]
    add edi, 759808
    cmp dword ptr [edi+esi*4], ebx
    jne __rt_db_unload_clause_next
    mov edi, dword ptr [__prolog_arena]
    add edi, 743424
    mov eax, esi
    shl eax, 4
    add edi, eax
    mov dword ptr [edi], 0
__rt_db_unload_clause_next:
    inc esi
    jmp __rt_db_unload_clause_loop
__rt_db_unload_clause_done:
    call __rt_dyn_db_compact
    call __rt_gc_dynamic
    push ebx
    call __rt_db_find_slot
    add esp, 4
    cmp eax, 4294967295
    je __rt_db_unload_after_slot
    mov ecx, eax
    mov edi, dword ptr [__prolog_arena]
    add edi, 770048
    mov dword ptr [edi+ecx*4], 0
    mov edi, dword ptr [__prolog_arena]
    add edi, 770176
    mov dword ptr [edi+ecx*4], 0
    mov edi, dword ptr [__prolog_arena]
    add edi, 770304
    mov dword ptr [edi+ecx*4], 0
    mov edi, dword ptr [__prolog_arena]
    add edi, 770432
    mov dword ptr [edi+ecx*4], 0
    mov edi, dword ptr [__prolog_arena]
    add edi, 770560
    mov dword ptr [edi+ecx*4], 0
__rt_db_unload_after_slot:
    cmp dword ptr [__prolog_current_db], ebx
    jne __rt_db_unload_current_ok
    mov dword ptr [__prolog_current_db], 0
__rt_db_unload_current_ok:
    mov eax, 1
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_database_save_id:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [ebp+8]
    push ebx
    call __rt_db_can_modify_id
    add esp, 4
    test eax, eax
    je __rt_database_save_fail
    push ebx
    call __rt_db_find_slot
    add esp, 4
    cmp eax, 4294967295
    je __rt_database_save_fail
    mov esi, eax
    push esi
    call __rt_db_make_temp_path
    add esp, 4
    test eax, eax
    je __rt_database_save_fail
    mov edi, eax
    push 0
    push 128
    push 2
    push 0
    push 0
    push 1073741824
    push edi
    call CreateFileA
    cmp eax, -1
    je __rt_database_save_fail
    mov dword ptr [__prolog_emit_file_handle], eax
    mov dword ptr [__prolog_emit_to_file], 1
    mov dword ptr [__prolog_emit_file_error], 0
    mov eax, dword ptr [__prolog_heap_top]
    mov dword ptr [__prolog_db_heap_mark], eax
    xor esi, esi
__rt_database_save_loop:
    cmp esi, dword ptr [__prolog_dyn_count]
    jae __rt_database_save_written
    mov edi, dword ptr [__prolog_arena]
    add edi, 743424
    mov eax, esi
    shl eax, 4
    add edi, eax
    cmp dword ptr [edi], 0
    je __rt_database_save_next
    mov edi, dword ptr [__prolog_arena]
    add edi, 759808
    cmp dword ptr [edi+esi*4], ebx
    jne __rt_database_save_next
    mov edi, dword ptr [__prolog_arena]
    add edi, 743424
    mov eax, esi
    shl eax, 4
    add edi, eax
    mov eax, dword ptr [edi+12]
    mov dword ptr [__prolog_dyn_clone_var_count], 0
    push eax
    call __rt_dyn_clone
    add esp, 4
    cmp eax, 4294967295
    je __rt_database_save_io_fail
    mov dword ptr [__prolog_save_var_count], 0
    push eax
    call __rt_emit_clause_source
    add esp, 4
    push __prolog_text_clause_end
    call __rt_emit_text
    add esp, 4
    mov eax, dword ptr [__prolog_db_heap_mark]
    mov dword ptr [__prolog_heap_top], eax
    cmp dword ptr [__prolog_emit_file_error], 0
    jne __rt_database_save_io_fail
__rt_database_save_next:
    inc esi
    jmp __rt_database_save_loop
__rt_database_save_written:
    push dword ptr [__prolog_emit_file_handle]
    call FlushFileBuffers
    test eax, eax
    je __rt_database_save_io_fail
    push dword ptr [__prolog_emit_file_handle]
    call CloseHandle
    mov dword ptr [__prolog_emit_file_handle], 0
    mov dword ptr [__prolog_emit_to_file], 0
    push ebx
    call __rt_db_find_slot
    add esp, 4
    cmp eax, 4294967295
    je __rt_database_save_fail
    mov esi, eax
    push esi
    call __rt_db_filename_ptr
    add esp, 4
    push eax
    push esi
    call __rt_db_make_temp_path
    add esp, 4
    pop edx
    push 9
    push edx
    push eax
    call MoveFileExA
    test eax, eax
    je __rt_database_save_move_fail
    mov edi, dword ptr [__prolog_arena]
    add edi, 770560
    mov dword ptr [edi+esi*4], 0
    mov eax, 1
    jmp __rt_database_save_done
__rt_database_save_io_fail:
    mov eax, dword ptr [__prolog_db_heap_mark]
    mov dword ptr [__prolog_heap_top], eax
    mov dword ptr [__prolog_emit_to_file], 0
    cmp dword ptr [__prolog_emit_file_handle], 0
    je __rt_database_save_delete_temp
    push dword ptr [__prolog_emit_file_handle]
    call CloseHandle
    mov dword ptr [__prolog_emit_file_handle], 0
__rt_database_save_delete_temp:
    push ebx
    call __rt_db_find_slot
    add esp, 4
    cmp eax, 4294967295
    je __rt_database_save_fail
    push eax
    call __rt_db_make_temp_path
    add esp, 4
    test eax, eax
    je __rt_database_save_fail
    push eax
    call DeleteFileA
    jmp __rt_database_save_fail
__rt_database_save_move_fail:
    push esi
    call __rt_db_make_temp_path
    add esp, 4
    push eax
    call DeleteFileA
__rt_database_save_fail:
    xor eax, eax
__rt_database_save_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_database_close_id:
    push ebp
    mov ebp, esp
    push ebx
    push edi
    mov ebx, dword ptr [ebp+8]
    push ebx
    call __rt_db_find_slot
    add esp, 4
    cmp eax, 4294967295
    je __rt_database_close_fail
    mov ecx, eax
    mov edi, dword ptr [__prolog_arena]
    add edi, 770432
    cmp dword ptr [edi+ecx*4], 3
    je __rt_database_close_fail
    push ebx
    call __rt_db_unload_id
    add esp, 4
    mov eax, 1
    jmp __rt_database_close_done
__rt_database_close_fail:
    xor eax, eax
__rt_database_close_done:
    pop edi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_database_save_as:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov ebx, dword ptr [ebp+8]
    push dword ptr [ebp+12]
    call __rt_term_cstr
    add esp, 4
    test edx, edx
    je __rt_database_save_as_fail
    mov esi, eax
    push ebx
    call __rt_db_find_slot
    add esp, 4
    cmp eax, 4294967295
    je __rt_database_save_as_fail
    mov ecx, eax
    push ecx
    call __rt_db_filename_ptr
    add esp, 4
    push 260
    mov edi, dword ptr [__prolog_arena]
    add edi, 779268
    push edi
    push eax
    call __rt_cstr_copy_limit
    add esp, 12
    test eax, eax
    je __rt_database_save_as_fail
    push ebx
    call __rt_db_find_slot
    add esp, 4
    cmp eax, 4294967295
    je __rt_database_save_as_fail
    mov ecx, eax
    push ecx
    call __rt_db_filename_ptr
    add esp, 4
    mov edi, eax
    push 260
    push edi
    push esi
    call __rt_cstr_copy_limit
    add esp, 12
    test eax, eax
    je __rt_database_save_as_restore
    push ebx
    call __rt_database_save_id
    add esp, 4
    test eax, eax
    je __rt_database_save_as_restore
    mov eax, 1
    jmp __rt_database_save_as_done
__rt_database_save_as_restore:
    push ebx
    call __rt_db_find_slot
    add esp, 4
    cmp eax, 4294967295
    je __rt_database_save_as_fail
    push eax
    call __rt_db_filename_ptr
    add esp, 4
    mov edi, eax
    push 260
    push edi
    mov esi, dword ptr [__prolog_arena]
    add esi, 779268
    push esi
    call __rt_cstr_copy_limit
    add esp, 12
__rt_database_save_as_fail:
    xor eax, eax
__rt_database_save_as_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_database_assert_scoped:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    mov ebx, dword ptr [ebp+8]
    mov esi, dword ptr [ebp+12]
    push ebx
    call __rt_db_can_modify_id
    add esp, 4
    test eax, eax
    je __rt_database_assert_scoped_fail
    mov eax, dword ptr [__prolog_current_db]
    push eax
    mov dword ptr [__prolog_current_db], ebx
    cmp dword ptr [ebp+16], 0
    jne __rt_database_assert_scoped_front
    push esi
    call __rt_assertz
    add esp, 4
    jmp __rt_database_assert_scoped_restore
__rt_database_assert_scoped_front:
    push esi
    call __rt_asserta
    add esp, 4
__rt_database_assert_scoped_restore:
    mov edx, eax
    pop eax
    mov dword ptr [__prolog_current_db], eax
    mov eax, edx
    jmp __rt_database_assert_scoped_done
__rt_database_assert_scoped_fail:
    xor eax, eax
__rt_database_assert_scoped_done:
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_database_retract_scoped:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    mov ebx, dword ptr [ebp+8]
    mov esi, dword ptr [ebp+12]
    push ebx
    call __rt_db_can_modify_id
    add esp, 4
    test eax, eax
    je __rt_database_retract_scoped_fail
    mov eax, dword ptr [__prolog_current_db]
    push eax
    mov dword ptr [__prolog_current_db], ebx
    push esi
    call __rt_retract
    add esp, 4
    mov edx, eax
    pop eax
    mov dword ptr [__prolog_current_db], eax
    mov eax, edx
    jmp __rt_database_retract_scoped_done
__rt_database_retract_scoped_fail:
    xor eax, eax
__rt_database_retract_scoped_done:
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_solve_goals:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    cmp dword ptr [__prolog_stop_search], 0
    jne __rt_solve_done
    mov ebx, dword ptr [ebp+8]
    cmp ebx, 4294967295
    jne __rt_solve_have_goal
    call __rt_emit_solution
    jmp __rt_solve_done
__rt_solve_have_goal:
    mov eax, ebx
    call __rt_node_ptr
    mov eax, dword ptr [edi+4]
    mov dword ptr [__prolog_current_cut_barrier], eax
    mov esi, dword ptr [edi+8]
    mov ebx, dword ptr [edi+12]
    mov eax, esi
    call __rt_deref
    mov esi, eax
    call __rt_node_ptr
    mov ecx, dword ptr [edi]
    cmp ecx, 2
    je __rt_solve_atom_goal
    cmp ecx, 7
    jne __rt_solve_done
    mov edx, dword ptr [edi+4]
    mov ecx, dword ptr [edi+8]
    jmp __rt_solve_dispatch
__rt_solve_atom_goal:
    mov edx, dword ptr [edi+4]
    xor ecx, ecx
__rt_solve_dispatch:
    cmp edx, 6
    jne __rt_builtin_next_0
    cmp ecx, 0
    je __rt_bi_true
__rt_builtin_next_0:
    cmp edx, 8
    jne __rt_builtin_next_1
    cmp ecx, 0
    je __rt_bi_fail
__rt_builtin_next_1:
    cmp edx, 9
    jne __rt_builtin_next_2
    cmp ecx, 0
    je __rt_bi_cut
__rt_builtin_next_2:
    cmp edx, 26
    jne __rt_builtin_next_3
    cmp ecx, 0
    je __rt_bi_nl
__rt_builtin_next_3:
    cmp edx, 38
    jne __rt_builtin_next_4
    cmp ecx, 0
    je __rt_bi_repl
__rt_builtin_next_4:
    cmp edx, 39
    jne __rt_builtin_next_5
    cmp ecx, 0
    je __rt_bi_halt
__rt_builtin_next_5:
    cmp edx, 40
    jne __rt_builtin_next_6
    cmp ecx, 0
    je __rt_bi_halt
__rt_builtin_next_6:
    cmp edx, 41
    jne __rt_builtin_next_7
    cmp ecx, 0
    je __rt_bi_gc
__rt_builtin_next_7:
    cmp edx, 42
    jne __rt_builtin_next_8
    cmp ecx, 0
    je __rt_bi_gc
__rt_builtin_next_8:
    cmp edx, 43
    jne __rt_builtin_next_9
    cmp ecx, 1
    je __rt_bi_verbose
__rt_builtin_next_9:
    cmp edx, 44
    jne __rt_builtin_next_10
    cmp ecx, 2
    je __rt_bi_set_stream
__rt_builtin_next_10:
    cmp edx, 45
    jne __rt_builtin_next_11
    cmp ecx, 1
    je __rt_bi_set_console_codepage
__rt_builtin_next_11:
    cmp edx, 23
    jne __rt_builtin_next_12
    cmp ecx, 1
    je __rt_bi_write
__rt_builtin_next_12:
    cmp edx, 24
    jne __rt_builtin_next_13
    cmp ecx, 1
    je __rt_bi_writeln
__rt_builtin_next_13:
    cmp edx, 25
    jne __rt_builtin_next_14
    cmp ecx, 1
    je __rt_bi_d64_eval
__rt_builtin_next_14:
    cmp edx, 27
    jne __rt_builtin_next_15
    cmp ecx, 1
    je __rt_bi_var
__rt_builtin_next_15:
    cmp edx, 28
    jne __rt_builtin_next_16
    cmp ecx, 1
    je __rt_bi_nonvar
__rt_builtin_next_16:
    cmp edx, 29
    jne __rt_builtin_next_17
    cmp ecx, 1
    je __rt_bi_atom
__rt_builtin_next_17:
    cmp edx, 30
    jne __rt_builtin_next_18
    cmp ecx, 1
    je __rt_bi_integer
__rt_builtin_next_18:
    cmp edx, 31
    jne __rt_builtin_next_19
    cmp ecx, 1
    je __rt_bi_float
__rt_builtin_next_19:
    cmp edx, 32
    jne __rt_builtin_next_20
    cmp ecx, 1
    je __rt_bi_number
__rt_builtin_next_20:
    cmp edx, 33
    jne __rt_builtin_next_21
    cmp ecx, 1
    je __rt_bi_string
__rt_builtin_next_21:
    cmp edx, 254
    jne __rt_builtin_next_22
    cmp ecx, 1
    je __rt_bi_random1
__rt_builtin_next_22:
    cmp edx, 254
    jne __rt_builtin_next_23
    cmp ecx, 2
    je __rt_bi_random2
__rt_builtin_next_23:
    cmp edx, 289
    jne __rt_builtin_next_24
    cmp ecx, 3
    je __rt_bi_random_between
__rt_builtin_next_24:
    cmp edx, 34
    jne __rt_builtin_next_25
    cmp ecx, 1
    je __rt_bi_assertz
__rt_builtin_next_25:
    cmp edx, 35
    jne __rt_builtin_next_26
    cmp ecx, 1
    je __rt_bi_asserta
__rt_builtin_next_26:
    cmp edx, 36
    jne __rt_builtin_next_27
    cmp ecx, 1
    je __rt_bi_assertz
__rt_builtin_next_27:
    cmp edx, 37
    jne __rt_builtin_next_28
    cmp ecx, 1
    je __rt_bi_retract
__rt_builtin_next_28:
    cmp edx, 58
    jne __rt_builtin_next_29
    cmp ecx, 2
    je __rt_bi_database_open2
__rt_builtin_next_29:
    cmp edx, 58
    jne __rt_builtin_next_30
    cmp ecx, 3
    je __rt_bi_database_open3
__rt_builtin_next_30:
    cmp edx, 58
    jne __rt_builtin_next_31
    cmp ecx, 4
    je __rt_bi_database_open4
__rt_builtin_next_31:
    cmp edx, 59
    jne __rt_builtin_next_32
    cmp ecx, 1
    je __rt_bi_database_close
__rt_builtin_next_32:
    cmp edx, 60
    jne __rt_builtin_next_33
    cmp ecx, 1
    je __rt_bi_database_save
__rt_builtin_next_33:
    cmp edx, 61
    jne __rt_builtin_next_34
    cmp ecx, 2
    je __rt_bi_database_save_as
__rt_builtin_next_34:
    cmp edx, 62
    jne __rt_builtin_next_35
    cmp ecx, 1
    je __rt_bi_database_select
__rt_builtin_next_35:
    cmp edx, 63
    jne __rt_builtin_next_36
    cmp ecx, 1
    je __rt_bi_current_database
__rt_builtin_next_36:
    cmp edx, 68
    jne __rt_builtin_next_37
    cmp ecx, 1
    je __rt_bi_database_modified
__rt_builtin_next_37:
    cmp edx, 64
    jne __rt_builtin_next_38
    cmp ecx, 2
    je __rt_bi_database_assertz
__rt_builtin_next_38:
    cmp edx, 65
    jne __rt_builtin_next_39
    cmp ecx, 2
    je __rt_bi_database_asserta
__rt_builtin_next_39:
    cmp edx, 66
    jne __rt_builtin_next_40
    cmp ecx, 2
    je __rt_bi_database_assertz
__rt_builtin_next_40:
    cmp edx, 67
    jne __rt_builtin_next_41
    cmp ecx, 2
    je __rt_bi_database_retract
__rt_builtin_next_41:
    cmp edx, 69
    jne __rt_builtin_next_42
    cmp ecx, 2
    je __rt_bi_with_database
__rt_builtin_next_42:
    cmp edx, 3
    jne __rt_builtin_next_43
    cmp ecx, 2
    je __rt_bi_conjunction
__rt_builtin_next_43:
    cmp edx, 4
    jne __rt_builtin_next_44
    cmp ecx, 2
    je __rt_bi_disjunction
__rt_builtin_next_44:
    cmp edx, 10
    jne __rt_builtin_next_45
    cmp ecx, 2
    je __rt_bi_unify
__rt_builtin_next_45:
    cmp edx, 11
    jne __rt_builtin_next_46
    cmp ecx, 2
    je __rt_bi_notunify
__rt_builtin_next_46:
    cmp edx, 12
    jne __rt_builtin_next_47
    cmp ecx, 2
    je __rt_bi_equal
__rt_builtin_next_47:
    cmp edx, 13
    jne __rt_builtin_next_48
    cmp ecx, 2
    je __rt_bi_is
__rt_builtin_next_48:
    cmp edx, 14
    jne __rt_builtin_next_49
    cmp ecx, 2
    je __rt_bi_lt
__rt_builtin_next_49:
    cmp edx, 15
    jne __rt_builtin_next_50
    cmp ecx, 2
    je __rt_bi_le
__rt_builtin_next_50:
    cmp edx, 16
    jne __rt_builtin_next_51
    cmp ecx, 2
    je __rt_bi_gt
__rt_builtin_next_51:
    cmp edx, 17
    jne __rt_builtin_next_52
    cmp ecx, 2
    je __rt_bi_ge
__rt_builtin_next_52:
    jmp __rt_builtin_fallthrough
__rt_bi_true:
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_fail:
    jmp __rt_solve_done
__rt_bi_cut:
    mov eax, dword ptr [__prolog_current_cut_barrier]
    cmp eax, 4294967295
    je __rt_bi_cut_cont
    mov dword ptr [__prolog_choice_top], eax
    mov dword ptr [__prolog_cut_active_barrier], eax
__rt_bi_cut_cont:
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_nl:
    push __prolog_text_newline
    call __rt_emit_text
    add esp, 4
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_gc:
    call __rt_gc_dynamic
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_verbose:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    call __rt_deref
    call __rt_node_ptr
    cmp dword ptr [edi], 2
    jne __rt_solve_done
    cmp dword ptr [edi+4], 6
    jne __rt_bi_verbose_false_test
    mov dword ptr [__prolog_verbose], 1
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_verbose_false_test:
    cmp dword ptr [edi+4], 7
    jne __rt_solve_done
    mov dword ptr [__prolog_verbose], 0
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_set_stream:
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_set_stream_encoding
    add esp, 8
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_set_console_codepage:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_term_int
    add esp, 4
    test edx, edx
    je __rt_solve_done
    test eax, eax
    jle __rt_solve_done
    push eax
    call __rt_set_console_codepage
    add esp, 4
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_halt:
    push 0
    call ExitProcess
    jmp __rt_solve_done
__rt_bi_repl:
    call __rt_repl
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_write:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_emit_term
    add esp, 4
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_writeln:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_emit_term
    add esp, 4
    push __prolog_text_newline
    call __rt_emit_text
    add esp, 4
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_d64_eval:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_solve_done
    push eax
    call __rt_emit_term
    add esp, 4
    push __prolog_text_newline
    call __rt_emit_text
    add esp, 4
    mov dword ptr [__prolog_direct_eval], 1
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_var:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    call __rt_deref
    call __rt_node_ptr
    cmp dword ptr [edi], 1
    jne __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_nonvar:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    call __rt_deref
    call __rt_node_ptr
    cmp dword ptr [edi], 1
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_atom:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    call __rt_deref
    call __rt_node_ptr
    cmp dword ptr [edi], 2
    jne __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_integer:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    call __rt_deref
    call __rt_node_ptr
    cmp dword ptr [edi], 3
    jne __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_float:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    call __rt_deref
    call __rt_node_ptr
    cmp dword ptr [edi], 9
    jne __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_string:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    call __rt_deref
    call __rt_node_ptr
    cmp dword ptr [edi], 4
    jne __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_number:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    call __rt_deref
    call __rt_node_ptr
    cmp dword ptr [edi], 3
    je __rt_bi_number_ok
    cmp dword ptr [edi], 9
    jne __rt_solve_done
__rt_bi_number_ok:
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_assertz:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_assertz
    add esp, 4
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_asserta:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_asserta
    add esp, 4
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_retract:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_retract
    add esp, 4
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_database_open2:
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push 2
    push 1
    push eax
    call __rt_database_open
    add esp, 12
    test eax, eax
    je __rt_bi_database_open2_fail
    push eax
    call __rt_make_int
    add esp, 4
    pop edx
    push eax
    push edx
    call __rt_unify
    add esp, 8
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_database_open2_fail:
    pop edx
    jmp __rt_solve_done
__rt_bi_database_open3:
    push 2
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_db_mode_from_term
    add esp, 4
    cmp eax, 4294967295
    je __rt_bi_database_open3_fail
    push eax
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    pop ecx
    push 2
    push ecx
    push eax
    call __rt_database_open
    add esp, 12
    test eax, eax
    je __rt_bi_database_open3_fail
    push eax
    call __rt_make_int
    add esp, 4
    pop edx
    push eax
    push edx
    call __rt_unify
    add esp, 8
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_database_open3_fail:
    pop edx
    jmp __rt_solve_done
__rt_bi_database_open4:
    push 3
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_db_mode_from_term
    add esp, 4
    cmp eax, 4294967295
    je __rt_bi_database_open4_fail
    push eax
    push 2
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_db_kind_from_term
    add esp, 4
    cmp eax, 4294967295
    je __rt_bi_database_open4_fail_mode
    push eax
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    pop edx
    pop ecx
    push edx
    push ecx
    push eax
    call __rt_database_open
    add esp, 12
    test eax, eax
    je __rt_bi_database_open4_fail
    push eax
    call __rt_make_int
    add esp, 4
    pop edx
    push eax
    push edx
    call __rt_unify
    add esp, 8
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_database_open4_fail:
    pop edx
    jmp __rt_solve_done
__rt_bi_database_open4_fail_mode:
    pop ecx
    jmp __rt_bi_database_open4_fail
__rt_bi_database_close:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_term_int
    add esp, 4
    test edx, edx
    je __rt_solve_done
    push eax
    call __rt_database_close_id
    add esp, 4
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_database_save:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_term_int
    add esp, 4
    test edx, edx
    je __rt_solve_done
    push eax
    call __rt_database_save_id
    add esp, 4
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_database_save_as:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_term_int
    add esp, 4
    test edx, edx
    je __rt_solve_done
    push eax
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    mov edx, eax
    pop eax
    push edx
    push eax
    call __rt_database_save_as
    add esp, 8
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_database_select:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_term_int
    add esp, 4
    test edx, edx
    je __rt_solve_done
    test eax, eax
    je __rt_bi_database_select_set
    push eax
    call __rt_db_find_slot
    add esp, 4
    cmp eax, 4294967295
    je __rt_solve_done
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_term_int
    add esp, 4
__rt_bi_database_select_set:
    mov dword ptr [__prolog_current_db], eax
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_current_database:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    push dword ptr [__prolog_current_db]
    call __rt_make_int
    add esp, 4
    pop edx
    push eax
    push edx
    call __rt_unify
    add esp, 8
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_database_modified:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_term_int
    add esp, 4
    test edx, edx
    je __rt_solve_done
    push eax
    call __rt_db_find_slot
    add esp, 4
    cmp eax, 4294967295
    je __rt_solve_done
    mov edi, dword ptr [__prolog_arena]
    add edi, 770560
    cmp dword ptr [edi+eax*4], 0
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_database_assertz:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_term_int
    add esp, 4
    test edx, edx
    je __rt_solve_done
    push eax
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    mov edx, eax
    pop eax
    push 0
    push edx
    push eax
    call __rt_database_assert_scoped
    add esp, 12
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_database_asserta:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_term_int
    add esp, 4
    test edx, edx
    je __rt_solve_done
    push eax
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    mov edx, eax
    pop eax
    push 1
    push edx
    push eax
    call __rt_database_assert_scoped
    add esp, 12
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_database_retract:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_term_int
    add esp, 4
    test edx, edx
    je __rt_solve_done
    push eax
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    mov edx, eax
    pop eax
    push edx
    push eax
    call __rt_database_retract_scoped
    add esp, 8
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_with_database:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_term_int
    add esp, 4
    test edx, edx
    je __rt_solve_done
    push eax
    test eax, eax
    je __rt_bi_with_database_have_db
    push eax
    call __rt_db_find_slot
    add esp, 4
    cmp eax, 4294967295
    je __rt_bi_with_database_fail_pop
__rt_bi_with_database_have_db:
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    mov edx, dword ptr [__prolog_current_cut_barrier]
    push edx
    push ebx
    push eax
    call __rt_goal_expr_to_chain
    add esp, 12
    mov edx, eax
    pop ecx
    mov eax, dword ptr [__prolog_current_db]
    push eax
    mov dword ptr [__prolog_current_db], ecx
    push edx
    call __rt_solve_goals
    add esp, 4
    pop eax
    mov dword ptr [__prolog_current_db], eax
    jmp __rt_solve_done
__rt_bi_with_database_fail_pop:
    pop ecx
    jmp __rt_solve_done
__rt_bi_random1:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_random_u32
    and eax, 2147483647
    push eax
    call __rt_make_int
    add esp, 4
    mov ecx, eax
    pop eax
    push ecx
    push eax
    call __rt_unify
    add esp, 8
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_random2:
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_bi_random2_fail_pop
    push eax
    call __rt_term_int
    add esp, 4
    test edx, edx
    je __rt_bi_random2_fail_pop
    test eax, eax
    jle __rt_bi_random2_fail_pop
    mov ecx, eax
    call __rt_random_bounded
    push eax
    call __rt_make_int
    add esp, 4
    mov ecx, eax
    pop eax
    push ecx
    push eax
    call __rt_unify
    add esp, 8
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_random2_fail_pop:
    pop eax
    jmp __rt_solve_done
__rt_bi_random_between:
    push 2
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_bi_random_between_fail_output
    push eax
    call __rt_term_int
    add esp, 4
    test edx, edx
    je __rt_bi_random_between_fail_output
    push eax
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_bi_random_between_fail_min_output
    push eax
    call __rt_term_int
    add esp, 4
    test edx, edx
    je __rt_bi_random_between_fail_min_output
    mov ecx, eax
    pop eax
    cmp ecx, eax
    jl __rt_bi_random_between_fail_output
    sub ecx, eax
    inc ecx
    push eax
    call __rt_random_bounded
    pop ecx
    add eax, ecx
    push eax
    call __rt_make_int
    add esp, 4
    mov ecx, eax
    pop eax
    push ecx
    push eax
    call __rt_unify
    add esp, 8
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_random_between_fail_min_output:
    pop eax
__rt_bi_random_between_fail_output:
    pop eax
    jmp __rt_solve_done
__rt_bi_conjunction:
    mov edx, dword ptr [__prolog_current_cut_barrier]
    push edx
    push ebx
    push esi
    call __rt_goal_expr_to_chain
    add esp, 12
    push eax
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_disjunction:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    mov ecx, eax
    pop eax
    push ecx
    mov edx, dword ptr [__prolog_choice_top]
    push edx
    call __rt_choice_push
    mov edx, dword ptr [__prolog_current_cut_barrier]
    push edx
    push ebx
    push eax
    call __rt_goal_expr_to_chain
    add esp, 12
    push eax
    call __rt_solve_goals
    add esp, 4
    mov edx, dword ptr [esp]
    push edx
    call __rt_choice_restore_slot
    add esp, 4
    pop edx
    pop ecx
    cmp dword ptr [__prolog_stop_search], 0
    jne __rt_solve_done
    mov eax, dword ptr [__prolog_current_cut_barrier]
    cmp dword ptr [__prolog_cut_active_barrier], eax
    je __rt_solve_done
    mov edx, dword ptr [__prolog_choice_top]
    push edx
    call __rt_choice_push
    mov edx, dword ptr [__prolog_current_cut_barrier]
    push edx
    push ebx
    push ecx
    call __rt_goal_expr_to_chain
    add esp, 12
    push eax
    call __rt_solve_goals
    add esp, 4
    mov edx, dword ptr [esp]
    push edx
    call __rt_choice_restore_slot
    add esp, 4
    pop edx
    jmp __rt_solve_done
__rt_bi_is:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    mov ecx, eax
    pop eax
    push eax
    push ecx
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_bi_is_fail_pop
    mov ecx, eax
    pop eax
    push ecx
    push eax
    call __rt_unify
    add esp, 8
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_is_fail_pop:
    pop eax
    jmp __rt_solve_done
__rt_bi_unify:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    mov ecx, eax
    pop eax
    push ecx
    push eax
    call __rt_unify
    add esp, 8
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_notunify:
    call __rt_choice_push
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    mov ecx, eax
    pop eax
    push ecx
    push eax
    call __rt_unify
    add esp, 8
    mov ecx, eax
    call __rt_choice_restore_pop
    test ecx, ecx
    jne __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_equal:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    mov ecx, eax
    pop eax
    push ecx
    push eax
    call __rt_equal_terms
    add esp, 8
    test eax, eax
    je __rt_solve_done
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_lt:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    mov ecx, eax
    pop eax
    push ecx
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_cmp_fail_pop
    mov esi, eax
    pop eax
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_solve_done
    mov ecx, eax
    push ecx
    push esi
    call __rt_numeric_compare
    add esp, 8
    test edx, edx
    je __rt_solve_done
    cmp eax, 0
    jl __rt_bi_lt_ok
    jmp __rt_solve_done
__rt_bi_lt_ok:
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_le:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    mov ecx, eax
    pop eax
    push ecx
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_cmp_fail_pop
    mov esi, eax
    pop eax
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_solve_done
    mov ecx, eax
    push ecx
    push esi
    call __rt_numeric_compare
    add esp, 8
    test edx, edx
    je __rt_solve_done
    cmp eax, 0
    jle __rt_bi_le_ok
    jmp __rt_solve_done
__rt_bi_le_ok:
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_gt:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    mov ecx, eax
    pop eax
    push ecx
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_cmp_fail_pop
    mov esi, eax
    pop eax
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_solve_done
    mov ecx, eax
    push ecx
    push esi
    call __rt_numeric_compare
    add esp, 8
    test edx, edx
    je __rt_solve_done
    cmp eax, 0
    jg __rt_bi_gt_ok
    jmp __rt_solve_done
__rt_bi_gt_ok:
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_bi_ge:
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    push 1
    push esi
    call __rt_struct_arg
    add esp, 8
    mov ecx, eax
    pop eax
    push ecx
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_cmp_fail_pop
    mov esi, eax
    pop eax
    push eax
    call __rt_eval_arith
    add esp, 4
    test edx, edx
    je __rt_solve_done
    mov ecx, eax
    push ecx
    push esi
    call __rt_numeric_compare
    add esp, 8
    test edx, edx
    je __rt_solve_done
    cmp eax, 0
    jge __rt_bi_ge_ok
    jmp __rt_solve_done
__rt_bi_ge_ok:
    push ebx
    call __rt_solve_goals
    add esp, 4
    jmp __rt_solve_done
__rt_cmp_fail_pop:
    pop eax
    jmp __rt_solve_done
__rt_builtin_fallthrough:
    push ebx
    push esi
    call __rt_try_user
    add esp, 8
__rt_solve_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_try_static_clause:
    push ebp
    mov ebp, esp
    push edx
    push edi
    mov eax, dword ptr [__prolog_choice_top]
    mov dword ptr [__prolog_build_barrier], eax
    push eax
    call __rt_choice_push
    mov edx, ebx
    mov eax, dword ptr [ebp+8]
    call __prolog_clause_descriptor_build
    push ecx
    push eax
    push esi
    call __rt_unify
    add esp, 8
    pop ecx
    test eax, eax
    je __rt_try_static_clause_after
    push ecx
    call __rt_solve_goals
    add esp, 4
__rt_try_static_clause_after:
    mov ecx, dword ptr [esp]
    push ecx
    call __rt_choice_restore_slot
    add esp, 4
    pop ecx
    cmp dword ptr [__prolog_cut_active_barrier], ecx
    jne __rt_try_static_clause_no_cut
    mov dword ptr [__prolog_cut_active_barrier], 4294967295
    mov eax, 1
    jmp __rt_try_static_clause_return
__rt_try_static_clause_no_cut:
    cmp dword ptr [__prolog_stop_search], 0
    jne __rt_try_static_clause_stop
    xor eax, eax
    jmp __rt_try_static_clause_return
__rt_try_static_clause_stop:
    mov eax, 1
__rt_try_static_clause_return:
    pop edi
    pop edx
    mov esp, ebp
    pop ebp
    ret

__rt_try_static_group:
    push ebp
    mov ebp, esp
    push edx
    push edi
    mov edi, dword ptr [ebp+8]
    mov edx, dword ptr [ebp+12]
__rt_try_static_group_loop:
    test edx, edx
    je __rt_try_static_group_exhausted
    mov eax, dword ptr [edi]
    add edi, 4
    push eax
    call __rt_try_static_clause
    add esp, 4
    test eax, eax
    jne __rt_try_static_group_stop
    dec edx
    jmp __rt_try_static_group_loop
__rt_try_static_group_exhausted:
    xor eax, eax
    jmp __rt_try_static_group_return
__rt_try_static_group_stop:
    mov eax, 1
__rt_try_static_group_return:
    pop edi
    pop edx
    mov esp, ebp
    pop ebp
    ret

__rt_try_user:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov esi, dword ptr [ebp+8]
    mov ebx, dword ptr [ebp+12]
    mov eax, esi
    call __rt_deref
    mov esi, eax
    call __rt_node_ptr
    cmp dword ptr [edi], 2
    je __rt_try_user_atom
    cmp dword ptr [edi], 7
    jne __rt_try_user_dynamic
    mov edx, dword ptr [edi+4]
    mov ecx, dword ptr [edi+8]
    jmp __rt_try_user_dispatch
__rt_try_user_atom:
    mov edx, dword ptr [edi+4]
    xor ecx, ecx
__rt_try_user_dispatch:
    cmp edx, 279
    jne __rt_try_pred_next_0
    cmp ecx, 2
    jne __rt_try_pred_next_0
    push 1
    push __prolog_pred_group_0_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_0:
    cmp edx, 280
    jne __rt_try_pred_next_1
    cmp ecx, 2
    jne __rt_try_pred_next_1
    push 6
    push __prolog_pred_group_1_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_1:
    cmp edx, 76
    jne __rt_try_pred_next_2
    cmp ecx, 1
    jne __rt_try_pred_next_2
    push 9
    push __prolog_pred_group_2_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_2:
    cmp edx, 86
    jne __rt_try_pred_next_3
    cmp ecx, 2
    jne __rt_try_pred_next_3
    push 8
    push __prolog_pred_group_3_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_3:
    cmp edx, 287
    jne __rt_try_pred_next_4
    cmp ecx, 2
    jne __rt_try_pred_next_4
    push 2
    push __prolog_pred_group_4_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_4:
    cmp edx, 288
    jne __rt_try_pred_next_5
    cmp ecx, 2
    jne __rt_try_pred_next_5
    push 2
    push __prolog_pred_group_5_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_5:
    cmp edx, 98
    jne __rt_try_pred_next_6
    cmp ecx, 1
    jne __rt_try_pred_next_6
    push 1
    push __prolog_pred_group_6_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_6:
    cmp edx, 251
    jne __rt_try_pred_next_7
    cmp ecx, 2
    jne __rt_try_pred_next_7
    push 2
    push __prolog_pred_group_7_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_7:
    cmp edx, 253
    jne __rt_try_pred_next_8
    cmp ecx, 2
    jne __rt_try_pred_next_8
    push 1
    push __prolog_pred_group_8_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_8:
    cmp edx, 252
    jne __rt_try_pred_next_9
    cmp ecx, 3
    jne __rt_try_pred_next_9
    push 2
    push __prolog_pred_group_9_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_9:
    cmp edx, 260
    jne __rt_try_pred_next_10
    cmp ecx, 2
    jne __rt_try_pred_next_10
    push 5
    push __prolog_pred_group_10_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_10:
    cmp edx, 278
    jne __rt_try_pred_next_11
    cmp ecx, 2
    jne __rt_try_pred_next_11
    push 1
    push __prolog_pred_group_11_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_11:
    cmp edx, 255
    jne __rt_try_pred_next_12
    cmp ecx, 2
    jne __rt_try_pred_next_12
    push 4
    push __prolog_pred_group_12_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_12:
    cmp edx, 215
    jne __rt_try_pred_next_13
    cmp ecx, 2
    jne __rt_try_pred_next_13
    push 10
    push __prolog_pred_group_13_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_13:
    cmp edx, 219
    jne __rt_try_pred_next_14
    cmp ecx, 2
    jne __rt_try_pred_next_14
    push 2
    push __prolog_pred_group_14_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_14:
    cmp edx, 95
    jne __rt_try_pred_next_15
    cmp ecx, 1
    jne __rt_try_pred_next_15
    push 1
    push __prolog_pred_group_15_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_15:
    cmp edx, 220
    jne __rt_try_pred_next_16
    cmp ecx, 2
    jne __rt_try_pred_next_16
    push 33
    push __prolog_pred_group_16_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_16:
    cmp edx, 108
    jne __rt_try_pred_next_17
    cmp ecx, 2
    jne __rt_try_pred_next_17
    push 31
    push __prolog_pred_group_17_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_17:
    cmp edx, 108
    jne __rt_try_pred_next_18
    cmp ecx, 3
    jne __rt_try_pred_next_18
    push 71
    push __prolog_pred_group_18_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_18:
    cmp edx, 101
    jne __rt_try_pred_next_19
    cmp ecx, 2
    jne __rt_try_pred_next_19
    push 4
    push __prolog_pred_group_19_descriptors
    call __rt_try_static_group
    add esp, 8
    test eax, eax
    jne __rt_try_user_return
    jmp __rt_try_user_dynamic
__rt_try_pred_next_19:
__rt_try_user_dynamic:
    push ebx
    push esi
    call __rt_try_dynamic
    add esp, 8
__rt_try_user_return:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_try_dynamic:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    mov esi, dword ptr [ebp+8]
    mov ebx, dword ptr [ebp+12]
    mov eax, esi
    call __rt_deref
    mov esi, eax
    call __rt_node_ptr
    cmp dword ptr [edi], 2
    je __rt_try_dynamic_atom
    cmp dword ptr [edi], 7
    jne __rt_try_dynamic_return
    mov edx, dword ptr [edi+4]
    mov ecx, dword ptr [edi+8]
    jmp __rt_try_dynamic_scan
__rt_try_dynamic_atom:
    mov edx, dword ptr [edi+4]
    xor ecx, ecx
__rt_try_dynamic_scan:
    push ecx
    push edx
    xor ecx, ecx
__rt_try_dynamic_loop:
    cmp dword ptr [__prolog_stop_search], 0
    jne __rt_try_dynamic_done_pop
    cmp ecx, dword ptr [__prolog_dyn_count]
    jae __rt_try_dynamic_done_pop
    mov edi, dword ptr [__prolog_arena]
    add edi, 743424
    mov eax, ecx
    shl eax, 4
    add edi, eax
    cmp dword ptr [edi], 0
    je __rt_try_dynamic_next
    mov eax, dword ptr [esp]
    cmp dword ptr [edi+4], eax
    jne __rt_try_dynamic_next
    mov eax, dword ptr [esp+4]
    cmp dword ptr [edi+8], eax
    jne __rt_try_dynamic_next
    mov eax, dword ptr [edi+12]
    mov edi, eax
    push ecx
    mov edx, dword ptr [__prolog_choice_top]
    mov dword ptr [__prolog_build_barrier], edx
    push edx
    call __rt_choice_push
    mov dword ptr [__prolog_dyn_clone_var_count], 0
    push edi
    call __rt_dyn_clone
    add esp, 4
    cmp eax, 4294967295
    je __rt_try_dynamic_after_solve
    mov edx, eax
    call __rt_node_ptr
    cmp dword ptr [edi], 7
    jne __rt_try_dynamic_fact
    cmp dword ptr [edi+4], 5
    jne __rt_try_dynamic_fact
    cmp dword ptr [edi+8], 2
    jne __rt_try_dynamic_fact
    push 1
    push edx
    call __rt_struct_arg
    add esp, 8
    mov ecx, eax
    push ecx
    push 0
    push edx
    call __rt_struct_arg
    add esp, 8
    mov edx, eax
    pop ecx
    jmp __rt_try_dynamic_unify
__rt_try_dynamic_fact:
    mov ecx, 4294967295
__rt_try_dynamic_unify:
    push ecx
    push edx
    push esi
    call __rt_unify
    add esp, 8
    pop ecx
    test eax, eax
    je __rt_try_dynamic_after_solve
    cmp ecx, 4294967295
    je __rt_try_dynamic_solve_rest
    mov edx, dword ptr [esp]
    push edx
    push ebx
    push ecx
    call __rt_goal_expr_to_chain
    add esp, 12
    push eax
    call __rt_solve_goals
    add esp, 4
    jmp __rt_try_dynamic_after_solve
__rt_try_dynamic_solve_rest:
    push ebx
    call __rt_solve_goals
    add esp, 4
__rt_try_dynamic_after_solve:
    mov edx, dword ptr [esp]
    push edx
    call __rt_choice_restore_slot
    add esp, 4
    pop edx
    pop ecx
    cmp dword ptr [__prolog_cut_active_barrier], edx
    jne __rt_try_dynamic_next
    mov dword ptr [__prolog_cut_active_barrier], 4294967295
    jmp __rt_try_dynamic_done_pop
__rt_try_dynamic_next:
    inc ecx
    jmp __rt_try_dynamic_loop
__rt_try_dynamic_done_pop:
    pop edx
    pop ecx
__rt_try_dynamic_return:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_run_query:
    push ebp
    mov ebp, esp
    mov dword ptr [__prolog_solution_count], 0
    mov dword ptr [__prolog_stop_search], 0
    mov dword ptr [__prolog_requested_more], 0
    mov dword ptr [__prolog_direct_eval], 0
    push dword ptr [ebp+8]
    call __rt_solve_goals
    add esp, 4
    cmp dword ptr [__prolog_interactive_mode], 0
    je __rt_run_query_noninteractive
    cmp dword ptr [__prolog_stop_search], 0
    jne __rt_run_query_done
    push __prolog_text_false_line
    call __rt_emit_text
    add esp, 4
    jmp __rt_run_query_done
__rt_run_query_noninteractive:
    cmp dword ptr [__prolog_solution_count], 0
    jne __rt_run_query_done
    push __prolog_text_false_line
    call __rt_emit_text
    add esp, 4
__rt_run_query_done:
    mov esp, ebp
    pop ebp
    ret

__rt_set_console_codepage:
    push ebp
    mov ebp, esp
    push dword ptr [ebp+8]
    call SetConsoleCP
    push dword ptr [ebp+8]
    call SetConsoleOutputCP
    mov eax, 1
__rt_set_console_codepage_done:
    mov esp, ebp
    pop ebp
    ret

__rt_set_stream_encoding:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    push dword ptr [ebp+8]
    call __rt_term_atom_id
    add esp, 4
    test edx, edx
    je __rt_set_stream_encoding_fail
    mov ebx, eax
    mov esi, dword ptr [ebp+12]
    mov eax, esi
    call __rt_deref
    call __rt_node_ptr
    cmp dword ptr [edi], 7
    jne __rt_set_stream_encoding_fail
    cmp dword ptr [edi+4], 46
    jne __rt_set_stream_encoding_fail
    cmp dword ptr [edi+8], 1
    jne __rt_set_stream_encoding_fail
    push 0
    push esi
    call __rt_struct_arg
    add esp, 8
    push eax
    call __rt_term_atom_id
    add esp, 4
    test edx, edx
    je __rt_set_stream_encoding_fail
    cmp eax, 52
    je __rt_set_stream_cp_utf8
    cmp eax, 55
    je __rt_set_stream_cp_utf8
    cmp eax, 53
    je __rt_set_stream_cp_ascii
    cmp eax, 54
    je __rt_set_stream_cp_latin1
    cmp eax, 56
    je __rt_set_stream_cp_1252
    cmp eax, 57
    je __rt_set_stream_cp_1252
    jmp __rt_set_stream_encoding_fail
__rt_set_stream_cp_utf8:
    mov esi, 65001
    jmp __rt_set_stream_cp_ready
__rt_set_stream_cp_ascii:
    mov esi, 20127
    jmp __rt_set_stream_cp_ready
__rt_set_stream_cp_latin1:
    mov esi, 28591
    jmp __rt_set_stream_cp_ready
__rt_set_stream_cp_1252:
    mov esi, 1252
__rt_set_stream_cp_ready:
    cmp ebx, 47
    je __rt_set_stream_input
    cmp ebx, 50
    je __rt_set_stream_input
    cmp ebx, 48
    je __rt_set_stream_output
    cmp ebx, 51
    je __rt_set_stream_output
    cmp ebx, 49
    je __rt_set_stream_output
    jmp __rt_set_stream_encoding_fail
__rt_set_stream_input:
    push esi
    call SetConsoleCP
    mov eax, 1
    jmp __rt_set_stream_encoding_done
__rt_set_stream_output:
    push esi
    call SetConsoleOutputCP
    mov eax, 1
    jmp __rt_set_stream_encoding_done
__rt_set_stream_encoding_fail:
    xor eax, eax
__rt_set_stream_encoding_done:
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_read_line:
    push ebp
    mov ebp, esp
    push esi
    push edi
    mov esi, dword ptr [__prolog_arena]
    add esi, 720896
    cmp dword ptr [__prolog_start_mode], 1
    jne __rt_read_line_console
    push 4095
    push esi
    mov eax, dword ptr [__prolog_qt_read_fn]
    call eax
    add esp, 8
    test eax, eax
    js __rt_read_line_gui_closed
    mov edx, eax
    jmp __rt_read_terminate
__rt_read_line_gui_closed:
    call __rt_gui_shutdown
    push 0
    call ExitProcess
__rt_read_line_console:
    mov dword ptr [__prolog_read_count], 0
    push 0
    push __prolog_read_count
    push 4095
    push esi
    push dword ptr [__prolog_stdin]
    call ReadFile
    mov edx, dword ptr [__prolog_read_count]
__rt_read_trim:
    test edx, edx
    je __rt_read_terminate
    movzx eax, byte ptr [esi+edx-1]
    cmp eax, 10
    je __rt_read_trim_one
    cmp eax, 13
    jne __rt_read_terminate
__rt_read_trim_one:
    dec edx
    jmp __rt_read_trim
__rt_read_terminate:
    xor eax, eax
    mov byte ptr [esi+edx], al
    mov eax, esi
    pop edi
    pop esi
    mov esp, ebp
    pop ebp
    ret

__rt_repl:
    push ebp
    mov ebp, esp
__rt_repl_loop:
    push __prolog_text_prompt
    call __rt_emit_text
    add esp, 4
    call __rt_read_line
    movzx ecx, byte ptr [eax]
    test ecx, ecx
    je __rt_repl_loop
    mov dword ptr [__prolog_heap_top], 0
    mov dword ptr [__prolog_trail_top], 0
    mov dword ptr [__prolog_choice_top], 0
    mov dword ptr [__prolog_query_var_count], 0
    mov dword ptr [__prolog_qname_top], 0
    mov dword ptr [__prolog_parse_pos], 0
    call __rt_parse_query
    cmp eax, 4294967295
    jne __rt_repl_run
    push __prolog_text_parse_error
    call __rt_emit_text
    add esp, 4
    jmp __rt_repl_loop
__rt_repl_run:
    mov dword ptr [__prolog_interactive_mode], 1
    push eax
    call __rt_run_query
    add esp, 4
    mov dword ptr [__prolog_interactive_mode], 0
    mov dword ptr [__prolog_stop_search], 0
    jmp __rt_repl_loop
    mov esp, ebp
    pop ebp
    ret

; Stage 288: one generic structural descriptor interpreter
__rt_build_descriptor_term:
    push ebp
    mov ebp, esp
    sub esp, 12
    push ebx
    movzx ebx, word ptr [esi]
    add esi, 2
    cmp ebx, 1
    je __rt_desc_term_var
    cmp ebx, 2
    je __rt_desc_term_int
    cmp ebx, 3
    je __rt_desc_term_float
    cmp ebx, 4
    je __rt_desc_term_string
    cmp ebx, 5
    je __rt_desc_term_atom
    cmp ebx, 6
    je __rt_desc_term_nil
    cmp ebx, 7
    je __rt_desc_term_list
    cmp ebx, 8
    je __rt_desc_term_compound
    call __rt_fatal
__rt_desc_term_var:
    movzx eax, word ptr [esi]
    add esi, 2
    push edi
    push eax
    call __rt_make_var
    add esp, 4
    pop edi
    jmp __rt_desc_term_done
__rt_desc_term_int:
    movzx ecx, word ptr [esi]
    add esi, 2
    mov eax, dword ptr [edi+ecx*4]
    push edi
    push eax
    call __rt_make_int
    add esp, 4
    pop edi
    jmp __rt_desc_term_done
__rt_desc_term_float:
    movzx ecx, word ptr [esi]
    add esi, 2
    mov eax, dword ptr [edi+ecx*4]
    mov edx, dword ptr [edi+ecx*4+4]
    push edi
    push edx
    push eax
    call __rt_make_float_bits
    add esp, 8
    pop edi
    jmp __rt_desc_term_done
__rt_desc_term_string:
    movzx ecx, word ptr [esi]
    add esi, 2
    mov eax, dword ptr [edi+ecx*4]
    push edi
    push eax
    call __rt_make_string
    add esp, 4
    pop edi
    jmp __rt_desc_term_done
__rt_desc_term_atom:
    movzx ecx, word ptr [esi]
    add esi, 2
    mov eax, dword ptr [edi+ecx*4]
    push edi
    push eax
    call __rt_make_atom
    add esp, 4
    pop edi
    jmp __rt_desc_term_done
__rt_desc_term_nil:
    push edi
    call __rt_make_nil
    pop edi
    jmp __rt_desc_term_done
__rt_desc_term_list:
    push edi
    call __rt_build_descriptor_term
    pop edi
    push eax
    push edi
    call __rt_build_descriptor_term
    pop edi
    pop ecx
    push edi
    push ecx
    push eax
    call __rt_make_list
    add esp, 8
    pop edi
    jmp __rt_desc_term_done
__rt_desc_term_compound:
    movzx eax, word ptr [esi]
    add esi, 2
    mov dword ptr [ebp-4], eax
    movzx eax, word ptr [esi]
    add esi, 2
    mov dword ptr [ebp-8], eax
    mov dword ptr [ebp-12], eax
    push 4294967295
__rt_desc_term_compound_loop:
    cmp dword ptr [ebp-12], 0
    je __rt_desc_term_compound_ready
    push edi
    call __rt_build_descriptor_term
    pop edi
    pop ecx
    push edi
    push ecx
    push eax
    call __rt_make_link
    add esp, 8
    pop edi
    push eax
    dec dword ptr [ebp-12]
    jmp __rt_desc_term_compound_loop
__rt_desc_term_compound_ready:
    pop edx
    mov ecx, dword ptr [ebp-4]
    mov eax, dword ptr [edi+ecx*4]
    mov ecx, dword ptr [ebp-8]
    push edi
    push edx
    push ecx
    push eax
    call __rt_make_struct
    add esp, 12
    pop edi
__rt_desc_term_done:
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__prolog_clause_descriptor_build:
    push ebp
    mov ebp, esp
    sub esp, 4
    push ebx
    push esi
    push edi
    mov ebx, edx
    mov edi, eax
    mov ecx, dword ptr [edi]
    add edi, 4
    mov esi, __prolog_clause_template_table
    mov esi, dword ptr [esi+ecx*4]
    movzx eax, word ptr [esi]
    add esi, 2
    push eax
    call __rt_build_vars_reset
    add esp, 4
    movzx eax, word ptr [esi]
    add esi, 2
    mov dword ptr [ebp-4], eax
    call __rt_build_descriptor_term
    push eax
__prolog_clause_descriptor_body_loop:
    cmp dword ptr [ebp-4], 0
    je __prolog_clause_descriptor_done
    call __rt_build_descriptor_term
    mov ecx, dword ptr [__prolog_build_barrier]
    push edi
    push ecx
    push ebx
    push eax
    call __rt_make_goal_link
    add esp, 12
    pop edi
    mov ebx, eax
    dec dword ptr [ebp-4]
    jmp __prolog_clause_descriptor_body_loop
__prolog_clause_descriptor_done:
    pop eax
    mov ecx, ebx
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_detect_start_mode:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push edi
    xor ebx, ebx
    call GetCommandLineA
    test eax, eax
    je __rt_detect_start_mode_done
    mov esi, eax
    mov edi, 32
__rt_detect_start_mode_scan:
    movzx eax, byte ptr [esi]
    test eax, eax
    je __rt_detect_start_mode_done
    cmp eax, 45
    jne __rt_detect_start_mode_advance
    cmp edi, 32
    je __rt_detect_start_mode_maybe_gui
    cmp edi, 9
    je __rt_detect_start_mode_maybe_gui
    cmp edi, 34
    jne __rt_detect_start_mode_advance
__rt_detect_start_mode_maybe_gui:
    movzx ecx, byte ptr [esi+0]
    cmp ecx, 45
    jne __rt_detect_start_mode_maybe_pipe
    movzx ecx, byte ptr [esi+1]
    cmp ecx, 45
    jne __rt_detect_start_mode_maybe_pipe
    movzx ecx, byte ptr [esi+2]
    cmp ecx, 103
    jne __rt_detect_start_mode_maybe_pipe
    movzx ecx, byte ptr [esi+3]
    cmp ecx, 117
    jne __rt_detect_start_mode_maybe_pipe
    movzx ecx, byte ptr [esi+4]
    cmp ecx, 105
    jne __rt_detect_start_mode_maybe_pipe
    movzx ecx, byte ptr [esi+5]
    test ecx, ecx
    je __rt_detect_start_mode_found_gui
    cmp ecx, 32
    je __rt_detect_start_mode_found_gui
    cmp ecx, 9
    je __rt_detect_start_mode_found_gui
    cmp ecx, 34
    jne __rt_detect_start_mode_maybe_pipe
__rt_detect_start_mode_found_gui:
    mov ebx, 1
    jmp __rt_detect_start_mode_done
__rt_detect_start_mode_maybe_pipe:
    movzx ecx, byte ptr [esi+0]
    cmp ecx, 45
    jne __rt_detect_start_mode_advance
    movzx ecx, byte ptr [esi+1]
    cmp ecx, 45
    jne __rt_detect_start_mode_advance
    movzx ecx, byte ptr [esi+2]
    cmp ecx, 105
    jne __rt_detect_start_mode_advance
    movzx ecx, byte ptr [esi+3]
    cmp ecx, 100
    jne __rt_detect_start_mode_advance
    movzx ecx, byte ptr [esi+4]
    cmp ecx, 101
    jne __rt_detect_start_mode_advance
    movzx ecx, byte ptr [esi+5]
    cmp ecx, 45
    jne __rt_detect_start_mode_advance
    movzx ecx, byte ptr [esi+6]
    cmp ecx, 112
    jne __rt_detect_start_mode_advance
    movzx ecx, byte ptr [esi+7]
    cmp ecx, 105
    jne __rt_detect_start_mode_advance
    movzx ecx, byte ptr [esi+8]
    cmp ecx, 112
    jne __rt_detect_start_mode_advance
    movzx ecx, byte ptr [esi+9]
    cmp ecx, 101
    jne __rt_detect_start_mode_advance
    movzx ecx, byte ptr [esi+10]
    test ecx, ecx
    je __rt_detect_start_mode_found_pipe
    cmp ecx, 32
    je __rt_detect_start_mode_found_pipe
    cmp ecx, 9
    je __rt_detect_start_mode_found_pipe
    cmp ecx, 34
    jne __rt_detect_start_mode_advance
__rt_detect_start_mode_found_pipe:
    mov ebx, 2
    jmp __rt_detect_start_mode_done
__rt_detect_start_mode_advance:
    mov edi, eax
    inc esi
    jmp __rt_detect_start_mode_scan
__rt_detect_start_mode_done:
    mov eax, ebx
    pop edi
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_load_gui_bridge:
    push ebp
    mov ebp, esp
    push ebx
    push esi
    push __prolog_qt_dll_name
    call LoadLibraryA
    test eax, eax
    je __rt_load_gui_bridge_fail
    mov dword ptr [__prolog_qt_module], eax
    push __prolog_qt_name_init
    push dword ptr [__prolog_qt_module]
    call GetProcAddress
    test eax, eax
    je __rt_load_gui_bridge_fail
    mov dword ptr [__prolog_qt_init_fn], eax
    push __prolog_qt_name_write
    push dword ptr [__prolog_qt_module]
    call GetProcAddress
    test eax, eax
    je __rt_load_gui_bridge_fail
    mov dword ptr [__prolog_qt_write_fn], eax
    push __prolog_qt_name_read
    push dword ptr [__prolog_qt_module]
    call GetProcAddress
    test eax, eax
    je __rt_load_gui_bridge_fail
    mov dword ptr [__prolog_qt_read_fn], eax
    push __prolog_qt_name_shutdown
    push dword ptr [__prolog_qt_module]
    call GetProcAddress
    test eax, eax
    je __rt_load_gui_bridge_fail
    mov dword ptr [__prolog_qt_shutdown_fn], eax
    mov eax, 1
    jmp __rt_load_gui_bridge_done
__rt_load_gui_bridge_fail:
    xor eax, eax
__rt_load_gui_bridge_done:
    pop esi
    pop ebx
    mov esp, ebp
    pop ebp
    ret

__rt_gui_initialize:
    push ebp
    mov ebp, esp
    call __rt_load_gui_bridge
    test eax, eax
    je __rt_gui_initialize_fail
    push -1
    push __prolog_caption
    mov eax, dword ptr [__prolog_qt_init_fn]
    call eax
    add esp, 8
    test eax, eax
    je __rt_gui_initialize_fail
    mov eax, 1
    jmp __rt_gui_initialize_done
__rt_gui_initialize_fail:
    push 16
    push __prolog_caption
    push __prolog_gui_launch_error
    push 0
    call MessageBoxA
    xor eax, eax
__rt_gui_initialize_done:
    mov esp, ebp
    pop ebp
    ret

__rt_gui_shutdown:
    push ebp
    mov ebp, esp
    mov eax, dword ptr [__prolog_qt_shutdown_fn]
    test eax, eax
    je __rt_gui_shutdown_done
    call eax
__rt_gui_shutdown_done:
    mov esp, ebp
    pop ebp
    ret

__prolog_startup_0_build:
    push ebp
    mov ebp, esp
    push ebx
    push 0
    call __rt_build_vars_reset
    add esp, 4
    mov ebx, 4294967295
    push 4294967295
    push 4294967295
    push 56
    call __rt_make_atom
    add esp, 4
    pop ecx
    push ecx
    push eax
    call __rt_make_link
    add esp, 8
    push eax
    pop ecx
    push ecx
    push 1
    push 46
    call __rt_make_struct
    add esp, 12
    pop ecx
    push ecx
    push eax
    call __rt_make_link
    add esp, 8
    push eax
    push 48
    call __rt_make_atom
    add esp, 4
    pop ecx
    push ecx
    push eax
    call __rt_make_link
    add esp, 8
    push eax
    pop ecx
    push ecx
    push 2
    push 44
    call __rt_make_struct
    add esp, 12
    push ebx
    push eax
    call __rt_make_link
    add esp, 8
    mov ebx, eax
    mov dword ptr [__prolog_query_var_count], 0
    mov eax, ebx
    pop ebx
    mov esp, ebp
    pop ebp
    ret

_start:
    call __rt_detect_start_mode
    mov dword ptr [__prolog_start_mode], eax
    cmp eax, 1
    jne __prolog_start_not_gui
    call __rt_gui_initialize
    test eax, eax
    je __prolog_gui_start_failed
    call FreeConsole
    jmp __prolog_start_runtime
__prolog_gui_start_failed:
    push 2
    call ExitProcess
__prolog_start_not_gui:
    cmp dword ptr [__prolog_start_mode], 2
    je __prolog_console_handles
    call GetConsoleWindow
    test eax, eax
    jne __prolog_console_handles
    call AllocConsole
__prolog_console_handles:
    push -11
    call GetStdHandle
    mov dword ptr [__prolog_stdout], eax
    push -10
    call GetStdHandle
    mov dword ptr [__prolog_stdin], eax
__prolog_start_runtime:
    push 4
    push 12288
    push 2359296
    push 0
    call VirtualAlloc
    mov dword ptr [__prolog_arena], eax
    test eax, eax
    jne __prolog_init_ok
    call __rt_fatal
__prolog_init_ok:
    mov edi, eax
    add edi, 262144
    mov dword ptr [__prolog_dyn_base], edi
    mov edi, eax
    add edi, 1048576
    mov dword ptr [__prolog_dyn_alt_base], edi
    call GetTickCount
    xor eax, dword ptr [__prolog_arena]
    test eax, eax
    jne __prolog_random_seed_ok
    mov eax, 2463534242
__prolog_random_seed_ok:
    mov dword ptr [__prolog_random_state], eax
    mov dword ptr [__prolog_heap_top], 0
    mov dword ptr [__prolog_dyn_heap_top], 0
    mov dword ptr [__prolog_trail_top], 0
    mov dword ptr [__prolog_choice_top], 0
    mov dword ptr [__prolog_dyn_count], 0
    mov dword ptr [__prolog_dyn_atom_count], 0
    mov dword ptr [__prolog_atom_pool_top], 0
    mov dword ptr [__prolog_output_top], 0
    mov dword ptr [__prolog_current_cut_barrier], 4294967295
    mov dword ptr [__prolog_cut_active_barrier], 4294967295
    mov dword ptr [__prolog_build_barrier], 0
    mov dword ptr [__prolog_interactive_mode], 0
    mov dword ptr [__prolog_stop_search], 0
    mov dword ptr [__prolog_requested_more], 0
    mov dword ptr [__prolog_direct_eval], 0
    mov dword ptr [__prolog_verbose], 0
    mov dword ptr [__prolog_db_next_id], 1
    mov dword ptr [__prolog_current_db], 0
    mov dword ptr [__prolog_db_loading], 0
    mov dword ptr [__prolog_parser_db_mode], 0
    mov dword ptr [__prolog_emit_to_file], 0
    mov dword ptr [__prolog_emit_file_error], 0
    mov dword ptr [__prolog_verbose], 1
    mov dword ptr [__prolog_heap_top], 0
    mov dword ptr [__prolog_trail_top], 0
    mov dword ptr [__prolog_choice_top], 0
    call __prolog_startup_0_build
    push eax
    call __rt_run_query
    add esp, 4
    mov dword ptr [__prolog_verbose], 0
    call __rt_repl
    cmp dword ptr [__prolog_start_mode], 1
    jne __prolog_exit_process
    call __rt_gui_shutdown
__prolog_exit_process:
    push 0
    call ExitProcess

section .data

__prolog_static_atom_offsets:
    dw 0, 3, 5, 7, 9, 12, 17, 23, 28, 30, 32, 35, 38, 41, 43, 46
    dw 48, 51, 53, 55, 57, 59, 63, 69, 77, 86, 89, 93, 100, 105, 113, 119
    dw 126, 133, 140, 148, 156, 164, 169, 174, 179, 182, 198, 206, 217, 238, 247, 258
    dw 270, 281, 295, 310, 315, 321, 333, 338, 345, 358, 372, 387, 401, 418, 434, 451
    dw 467, 484, 501, 518, 536, 550, 560, 571, 581, 588, 595, 615, 622, 640, 656, 673
    dw 682, 690, 701, 714, 721, 737, 756, 801, 844, 891, 924, 957, 995, 1044, 1071, 1080
    dw 1088, 1096, 1103, 1112, 1121, 1138, 1145, 1186, 1238, 1247, 1299, 1352, 1357, 1362, 1366, 1375
    dw 1379, 1388, 1399, 1403, 1410, 1419, 1424, 1429, 1435, 1440, 1449, 1454, 1460, 1469, 1476, 1483
    dw 1488, 1493, 1505, 1515, 1523, 1530, 1537, 1545, 1553, 1562, 1567, 1578, 1586, 1595, 1600, 1608
    dw 1614, 1626, 1639, 1646, 1653, 1658, 1665, 1673, 1678, 1684, 1688, 1694, 1699, 1703, 1712, 1722
    dw 1729, 1737, 1742, 1748, 1754, 1760, 1766, 1772, 1779, 1787, 1793, 1801, 1806, 1812, 1817, 1826
    dw 1832, 1837, 1841, 1847, 1860, 1864, 1873, 1877, 1881, 1884, 1889, 1895, 1902, 1910, 1918, 1922
    dw 1930, 1933, 1936, 1940, 1944, 1948, 1953, 1964, 1970, 1975, 1981, 1986, 1993, 1998, 2006, 2010
    dw 2015, 2020, 2025, 2030, 2036, 2043, 2051, 2060, 2065, 2074, 2081, 2095, 2105, 2110, 2114, 2121
    dw 2125, 2129, 2136, 2142, 2148, 2151, 2155, 2161, 2168, 2172, 2178, 2185, 2193, 2197, 2209, 2213
    dw 2220, 2225, 2229, 2232, 2236, 2242, 2248, 2252, 2259, 2264, 2269, 2288, 2300, 2314, 2321, 2330
    dw 2347, 2386, 2402, 2417, 2433, 2450, 2467, 2484, 2501, 2522, 2543, 2564, 2585, 2602, 2623, 2630
    dw 2641, 2662, 2690, 2707, 2717, 2728, 2736, 2750, 2764, 2777, 2795, 2810, 2827, 2843, 2853, 2865
    dw 2872
__prolog_static_atom_blob:
    db 91, 93, 0, 46, 0, 44, 0, 59, 0, 58, 45, 0, 116, 114, 117, 101, 0, 102, 97, 108, 115, 101, 0, 102
    db 97, 105, 108, 0, 33, 0, 61, 0, 92, 61, 0, 61, 61, 0, 105, 115, 0, 60, 0, 61, 60, 0, 62, 0
    db 62, 61, 0, 43, 0, 45, 0, 42, 0, 47, 0, 109, 111, 100, 0, 119, 114, 105, 116, 101, 0, 119, 114, 105
    db 116, 101, 108, 110, 0, 100, 54, 52, 95, 101, 118, 97, 108, 0, 110, 108, 0, 118, 97, 114, 0, 110, 111, 110
    db 118, 97, 114, 0, 97, 116, 111, 109, 0, 105, 110, 116, 101, 103, 101, 114, 0, 102, 108, 111, 97, 116, 0, 110
    db 117, 109, 98, 101, 114, 0, 115, 116, 114, 105, 110, 103, 0, 97, 115, 115, 101, 114, 116, 0, 97, 115, 115, 101
    db 114, 116, 97, 0, 97, 115, 115, 101, 114, 116, 122, 0, 114, 101, 116, 114, 97, 99, 116, 0, 114, 101, 112, 108
    db 0, 104, 97, 108, 116, 0, 113, 117, 105, 116, 0, 103, 99, 0, 103, 97, 114, 98, 97, 103, 101, 95, 99, 111
    db 108, 108, 101, 99, 116, 0, 118, 101, 114, 98, 111, 115, 101, 0, 115, 101, 116, 95, 115, 116, 114, 101, 97, 109
    db 0, 115, 101, 116, 95, 99, 111, 110, 115, 111, 108, 101, 95, 99, 111, 100, 101, 112, 97, 103, 101, 0, 101, 110
    db 99, 111, 100, 105, 110, 103, 0, 117, 115, 101, 114, 95, 105, 110, 112, 117, 116, 0, 117, 115, 101, 114, 95, 111
    db 117, 116, 112, 117, 116, 0, 117, 115, 101, 114, 95, 101, 114, 114, 111, 114, 0, 99, 117, 114, 114, 101, 110, 116
    db 95, 105, 110, 112, 117, 116, 0, 99, 117, 114, 114, 101, 110, 116, 95, 111, 117, 116, 112, 117, 116, 0, 117, 116
    db 102, 56, 0, 97, 115, 99, 105, 105, 0, 105, 115, 111, 95, 108, 97, 116, 105, 110, 95, 49, 0, 116, 101, 120
    db 116, 0, 99, 112, 49, 50, 53, 50, 0, 119, 105, 110, 100, 111, 119, 115, 95, 49, 50, 53, 50, 0, 100, 97
    db 116, 97, 98, 97, 115, 101, 95, 111, 112, 101, 110, 0, 100, 97, 116, 97, 98, 97, 115, 101, 95, 99, 108, 111
    db 115, 101, 0, 100, 97, 116, 97, 98, 97, 115, 101, 95, 115, 97, 118, 101, 0, 100, 97, 116, 97, 98, 97, 115
    db 101, 95, 115, 97, 118, 101, 95, 97, 115, 0, 100, 97, 116, 97, 98, 97, 115, 101, 95, 115, 101, 108, 101, 99
    db 116, 0, 99, 117, 114, 114, 101, 110, 116, 95, 100, 97, 116, 97, 98, 97, 115, 101, 0, 100, 97, 116, 97, 98
    db 97, 115, 101, 95, 97, 115, 115, 101, 114, 116, 0, 100, 97, 116, 97, 98, 97, 115, 101, 95, 97, 115, 115, 101
    db 114, 116, 97, 0, 100, 97, 116, 97, 98, 97, 115, 101, 95, 97, 115, 115, 101, 114, 116, 122, 0, 100, 97, 116
    db 97, 98, 97, 115, 101, 95, 114, 101, 116, 114, 97, 99, 116, 0, 100, 97, 116, 97, 98, 97, 115, 101, 95, 109
    db 111, 100, 105, 102, 105, 101, 100, 0, 119, 105, 116, 104, 95, 100, 97, 116, 97, 98, 97, 115, 101, 0, 114, 101
    db 97, 100, 95, 111, 110, 108, 121, 0, 114, 101, 97, 100, 95, 119, 114, 105, 116, 101, 0, 107, 110, 111, 119, 108
    db 101, 100, 103, 101, 0, 114, 101, 99, 111, 114, 100, 0, 115, 121, 115, 116, 101, 109, 0, 100, 54, 52, 95, 107
    db 110, 111, 119, 108, 101, 100, 103, 101, 95, 118, 97, 108, 117, 101, 0, 105, 110, 116, 101, 110, 116, 0, 97, 115
    db 107, 95, 110, 97, 109, 101, 95, 105, 110, 102, 111, 114, 109, 97, 108, 0, 97, 115, 107, 95, 110, 97, 109, 101
    db 95, 102, 111, 114, 109, 97, 108, 0, 97, 115, 107, 95, 110, 97, 109, 101, 95, 103, 101, 110, 101, 114, 97, 108
    db 0, 103, 114, 101, 101, 116, 105, 110, 103, 0, 103, 111, 111, 100, 98, 121, 101, 0, 97, 115, 107, 95, 115, 116
    db 97, 116, 117, 115, 0, 97, 115, 107, 95, 105, 100, 101, 110, 116, 105, 116, 121, 0, 116, 104, 97, 110, 107, 115
    db 0, 100, 111, 99, 116, 111, 114, 95, 99, 97, 110, 95, 104, 101, 108, 112, 0, 105, 110, 116, 101, 110, 116, 95
    db 100, 101, 115, 99, 114, 105, 112, 116, 105, 111, 110, 0, 68, 101, 114, 32, 66, 101, 110, 117, 116, 122, 101, 114
    db 32, 102, 114, 97, 103, 116, 32, 105, 110, 102, 111, 114, 109, 101, 108, 108, 32, 110, 97, 99, 104, 32, 100, 101
    db 109, 32, 78, 97, 109, 101, 110, 46, 0, 68, 101, 114, 32, 66, 101, 110, 117, 116, 122, 101, 114, 32, 102, 114
    db 97, 103, 116, 32, 104, 246, 102, 108, 105, 99, 104, 32, 110, 97, 99, 104, 32, 100, 101, 109, 32, 78, 97, 109
    db 101, 110, 46, 0, 68, 101, 114, 32, 66, 101, 110, 117, 116, 122, 101, 114, 32, 102, 114, 97, 103, 116, 32, 97
    db 108, 108, 103, 101, 109, 101, 105, 110, 32, 110, 97, 99, 104, 32, 101, 105, 110, 101, 109, 32, 78, 97, 109, 101
    db 110, 46, 0, 68, 101, 114, 32, 66, 101, 110, 117, 116, 122, 101, 114, 32, 98, 101, 103, 114, 252, 223, 116, 32
    db 100, 97, 115, 32, 83, 121, 115, 116, 101, 109, 46, 0, 68, 101, 114, 32, 66, 101, 110, 117, 116, 122, 101, 114
    db 32, 118, 101, 114, 97, 98, 115, 99, 104, 105, 101, 100, 101, 116, 32, 115, 105, 99, 104, 46, 0, 68, 101, 114
    db 32, 66, 101, 110, 117, 116, 122, 101, 114, 32, 102, 114, 97, 103, 116, 32, 110, 97, 99, 104, 32, 100, 101, 109
    db 32, 66, 101, 102, 105, 110, 100, 101, 110, 46, 0, 68, 101, 114, 32, 66, 101, 110, 117, 116, 122, 101, 114, 32
    db 102, 114, 97, 103, 116, 44, 32, 119, 101, 114, 32, 111, 100, 101, 114, 32, 119, 97, 115, 32, 100, 97, 115, 32
    db 83, 121, 115, 116, 101, 109, 32, 105, 115, 116, 46, 0, 68, 101, 114, 32, 66, 101, 110, 117, 116, 122, 101, 114
    db 32, 98, 101, 100, 97, 110, 107, 116, 32, 115, 105, 99, 104, 46, 0, 115, 105, 109, 103, 117, 108, 97, 114, 0
    db 101, 105, 110, 122, 101, 108, 110, 0, 101, 105, 110, 122, 97, 104, 108, 0, 112, 108, 117, 114, 97, 108, 0, 109
    db 101, 104, 114, 109, 97, 108, 115, 0, 109, 101, 104, 114, 122, 97, 104, 108, 0, 119, 111, 114, 100, 95, 100, 101
    db 115, 99, 114, 105, 112, 116, 105, 111, 110, 0, 97, 114, 98, 101, 105, 116, 0, 102, 252, 114, 32, 100, 97, 115
    db 32, 252, 98, 101, 114, 108, 101, 98, 101, 110, 32, 97, 110, 32, 100, 101, 114, 32, 65, 101, 98, 101, 105, 116
    db 32, 97, 114, 98, 101, 105, 116, 101, 110, 0, 106, 101, 109, 97, 110, 100, 101, 110, 32, 97, 117, 115, 98, 105
    db 108, 100, 101, 110, 44, 32, 117, 109, 32, 100, 105, 101, 32, 65, 114, 98, 101, 105, 116, 32, 109, 97, 99, 104
    db 101, 110, 32, 122, 117, 32, 107, 246, 110, 110, 101, 110, 46, 0, 97, 114, 98, 101, 105, 116, 101, 114, 0, 102
    db 252, 114, 32, 65, 114, 98, 101, 105, 116, 101, 110, 32, 110, 111, 116, 119, 101, 110, 100, 105, 103, 101, 44, 32
    db 102, 228, 104, 105, 103, 101, 110, 32, 77, 101, 110, 115, 99, 104, 32, 101, 105, 110, 115, 116, 101, 108, 108, 101
    db 110, 46, 0, 102, 252, 114, 32, 65, 114, 98, 101, 105, 116, 101, 110, 32, 110, 111, 116, 119, 101, 110, 100, 105
    db 103, 101, 44, 32, 102, 228, 104, 105, 103, 101, 32, 77, 101, 110, 115, 99, 104, 101, 110, 32, 101, 105, 110, 115
    db 116, 101, 108, 108, 101, 110, 46, 0, 119, 111, 114, 100, 0, 110, 111, 117, 110, 0, 100, 101, 114, 0, 115, 105
    db 110, 103, 117, 108, 97, 114, 0, 100, 105, 101, 0, 97, 114, 98, 101, 105, 116, 101, 110, 0, 97, 114, 98, 101
    db 105, 116, 115, 97, 109, 116, 0, 100, 97, 115, 0, 97, 114, 122, 110, 101, 105, 0, 97, 114, 122, 110, 101, 105
    db 101, 110, 0, 97, 114, 122, 116, 0, 98, 97, 110, 100, 0, 98, 97, 110, 100, 101, 0, 98, 97, 110, 107, 0
    db 98, 97, 110, 107, 110, 111, 116, 101, 0, 98, 97, 117, 109, 0, 98, 114, 97, 110, 100, 0, 98, 114, 97, 117
    db 101, 114, 101, 105, 0, 98, 114, 97, 117, 115, 101, 0, 98, 114, 117, 100, 101, 114, 0, 99, 104, 101, 102, 0
    db 100, 97, 99, 104, 0, 100, 97, 99, 104, 102, 101, 110, 115, 116, 101, 114, 0, 100, 97, 99, 104, 114, 105, 110
    db 110, 101, 0, 102, 101, 110, 115, 116, 101, 114, 0, 102, 114, 101, 117, 110, 100, 0, 103, 101, 114, 117, 99, 104
    db 0, 103, 101, 114, 252, 99, 104, 101, 0, 103, 101, 116, 114, 228, 110, 107, 0, 103, 101, 116, 114, 228, 110, 107
    db 101, 0, 104, 97, 117, 115, 0, 104, 97, 117, 115, 110, 117, 109, 109, 101, 114, 0, 104, 97, 117, 115, 116, 252
    db 114, 0, 104, 97, 117, 115, 119, 97, 110, 100, 0, 104, 117, 110, 100, 0, 107, 111, 108, 108, 101, 103, 101, 0
    db 107, 114, 105, 109, 105, 0, 107, 114, 105, 109, 105, 110, 97, 108, 97, 109, 116, 0, 107, 114, 105, 109, 105, 110
    db 97, 108, 105, 116, 228, 116, 0, 107, 117, 99, 104, 101, 110, 0, 108, 101, 104, 114, 101, 114, 0, 109, 97, 110
    db 110, 0, 109, 101, 110, 115, 99, 104, 0, 110, 97, 99, 104, 98, 97, 114, 0, 110, 111, 116, 101, 0, 110, 111
    db 116, 101, 110, 0, 111, 109, 97, 0, 111, 110, 107, 101, 108, 0, 111, 98, 101, 114, 0, 111, 112, 97, 0, 112
    db 114, 111, 103, 114, 97, 109, 109, 0, 112, 114, 111, 103, 114, 97, 109, 109, 101, 0, 113, 117, 101, 108, 108, 101
    db 0, 113, 117, 101, 108, 108, 101, 110, 0, 114, 97, 117, 109, 0, 114, 228, 117, 109, 101, 0, 114, 105, 110, 110
    db 101, 0, 115, 111, 104, 108, 101, 0, 115, 111, 110, 100, 101, 0, 115, 111, 110, 110, 101, 0, 115, 111, 110, 110
    db 101, 110, 0, 115, 111, 110, 110, 116, 97, 103, 0, 115, 116, 101, 114, 110, 0, 115, 116, 117, 100, 101, 110, 116
    db 0, 117, 102, 101, 114, 0, 118, 97, 116, 101, 114, 0, 122, 97, 104, 110, 0, 122, 97, 104, 110, 97, 114, 122
    db 116, 0, 122, 97, 110, 103, 101, 0, 122, 97, 117, 110, 0, 122, 117, 103, 0, 122, 117, 110, 103, 101, 0, 122
    db 119, 105, 115, 99, 104, 101, 110, 114, 97, 117, 109, 0, 119, 105, 101, 0, 113, 117, 101, 115, 116, 105, 111, 110
    db 0, 119, 97, 115, 0, 119, 101, 114, 0, 119, 111, 0, 119, 97, 110, 110, 0, 119, 97, 114, 117, 109, 0, 119
    db 101, 108, 99, 104, 101, 0, 119, 101, 108, 99, 104, 101, 114, 0, 119, 101, 108, 99, 104, 101, 115, 0, 105, 99
    db 104, 0, 112, 114, 111, 110, 111, 117, 110, 0, 100, 117, 0, 101, 114, 0, 115, 105, 101, 0, 119, 105, 114, 0
    db 105, 104, 114, 0, 109, 101, 105, 110, 0, 112, 111, 115, 115, 101, 115, 115, 105, 118, 101, 0, 109, 101, 105, 110
    db 101, 0, 100, 101, 105, 110, 0, 100, 101, 105, 110, 101, 0, 105, 104, 114, 101, 0, 104, 101, 105, 115, 115, 116
    db 0, 118, 101, 114, 98, 0, 104, 101, 105, 115, 115, 101, 110, 0, 105, 115, 116, 0, 115, 105, 110, 100, 0, 103
    db 101, 104, 116, 0, 98, 105, 115, 116, 0, 104, 97, 115, 116, 0, 104, 97, 98, 101, 110, 0, 107, 97, 110, 110
    db 115, 116, 0, 107, 111, 101, 110, 110, 101, 110, 0, 115, 101, 109, 97, 110, 116, 105, 99, 0, 110, 97, 109, 101
    db 0, 105, 110, 102, 111, 114, 109, 97, 108, 0, 102, 111, 114, 109, 97, 108, 0, 115, 101, 109, 97, 110, 116, 105
    db 99, 95, 108, 105, 115, 116, 0, 117, 116, 116, 101, 114, 97, 110, 99, 101, 0, 107, 97, 110, 110, 0, 117, 110
    db 115, 0, 104, 101, 108, 102, 101, 110, 0, 115, 97, 103, 0, 109, 105, 114, 0, 100, 101, 105, 110, 101, 110, 0
    db 110, 97, 109, 101, 110, 0, 104, 97, 108, 108, 111, 0, 104, 105, 0, 104, 101, 121, 0, 103, 117, 116, 101, 110
    db 0, 109, 111, 114, 103, 101, 110, 0, 116, 97, 103, 0, 97, 98, 101, 110, 100, 0, 115, 101, 114, 118, 117, 115
    db 0, 116, 115, 99, 104, 252, 115, 115, 0, 97, 117, 102, 0, 119, 105, 101, 100, 101, 114, 115, 101, 104, 101, 110
    db 0, 98, 105, 115, 0, 115, 112, 228, 116, 101, 114, 0, 98, 97, 108, 100, 0, 98, 121, 101, 0, 101, 115, 0
    db 100, 105, 114, 0, 103, 101, 104, 116, 115, 0, 97, 108, 108, 101, 115, 0, 103, 117, 116, 0, 102, 252, 104, 108
    db 115, 116, 0, 100, 105, 99, 104, 0, 115, 101, 105, 100, 0, 114, 97, 110, 100, 111, 109, 95, 108, 105, 115, 116
    db 95, 108, 101, 110, 103, 116, 104, 0, 114, 97, 110, 100, 111, 109, 95, 110, 116, 104, 48, 0, 114, 97, 110, 100
    db 111, 109, 95, 109, 101, 109, 98, 101, 114, 0, 114, 97, 110, 100, 111, 109, 0, 114, 101, 115, 112, 111, 110, 115
    db 101, 0, 68, 97, 115, 32, 105, 115, 116, 32, 114, 105, 99, 104, 116, 105, 103, 46, 0, 73, 99, 104, 32, 98
    db 105, 110, 32, 101, 105, 110, 32, 100, 105, 97, 108, 111, 103, 111, 114, 105, 101, 110, 116, 105, 101, 114, 116, 101
    db 115, 32, 83, 121, 115, 116, 101, 109, 46, 0, 71, 101, 114, 110, 32, 103, 101, 115, 99, 104, 101, 104, 101, 110
    db 46, 0, 75, 101, 105, 110, 101, 32, 85, 114, 115, 97, 99, 104, 101, 46, 0, 114, 97, 110, 100, 111, 109, 95
    db 114, 101, 115, 112, 111, 110, 115, 101, 0, 73, 99, 104, 32, 104, 101, 105, 223, 101, 32, 67, 111, 110, 110, 121
    db 46, 0, 73, 99, 104, 32, 104, 101, 105, 223, 101, 32, 70, 114, 97, 110, 107, 46, 0, 73, 99, 104, 32, 104
    db 101, 105, 223, 101, 32, 83, 111, 110, 110, 121, 46, 0, 73, 99, 104, 32, 104, 101, 105, 223, 101, 32, 80, 101
    db 116, 101, 114, 46, 0, 77, 101, 105, 110, 32, 78, 97, 109, 101, 32, 105, 115, 116, 32, 67, 111, 110, 110, 121
    db 46, 0, 77, 101, 105, 110, 32, 78, 97, 109, 101, 32, 105, 115, 116, 32, 70, 114, 97, 110, 107, 46, 0, 77
    db 101, 105, 110, 32, 78, 97, 109, 101, 32, 105, 115, 116, 32, 83, 111, 110, 110, 121, 46, 0, 77, 101, 105, 110
    db 32, 78, 97, 109, 101, 32, 105, 115, 116, 32, 80, 101, 116, 101, 114, 46, 0, 77, 105, 114, 32, 103, 101, 104
    db 116, 32, 101, 115, 32, 103, 117, 116, 46, 0, 68, 97, 110, 107, 101, 32, 100, 101, 114, 32, 78, 97, 99, 104
    db 102, 114, 97, 103, 101, 46, 0, 72, 97, 108, 108, 111, 33, 0, 71, 117, 116, 101, 110, 32, 84, 97, 103, 33
    db 0, 83, 99, 104, 246, 110, 32, 100, 105, 99, 104, 32, 122, 117, 32, 115, 101, 104, 101, 110, 46, 0, 72, 97
    db 108, 108, 111, 44, 32, 119, 105, 101, 32, 107, 97, 110, 110, 32, 105, 99, 104, 32, 104, 101, 108, 102, 101, 110
    db 63, 0, 65, 117, 102, 32, 87, 105, 101, 100, 101, 114, 115, 101, 104, 101, 110, 33, 0, 66, 105, 115, 32, 98
    db 97, 108, 100, 33, 0, 77, 97, 99, 104, 115, 32, 103, 117, 116, 33, 0, 114, 101, 115, 112, 111, 110, 100, 0
    db 100, 101, 116, 101, 99, 116, 95, 105, 110, 116, 101, 110, 116, 0, 100, 111, 116, 95, 117, 116, 116, 101, 114, 97
    db 110, 99, 101, 0, 119, 105, 101, 46, 104, 101, 105, 223, 116, 46, 100, 117, 0, 119, 105, 101, 46, 105, 115, 116
    db 46, 100, 101, 105, 110, 46, 110, 97, 109, 101, 0, 119, 105, 101, 46, 104, 101, 105, 223, 101, 110, 46, 115, 105
    db 101, 0, 119, 105, 101, 46, 105, 115, 116, 46, 105, 104, 114, 46, 110, 97, 109, 101, 0, 119, 105, 101, 46, 103
    db 101, 104, 116, 46, 101, 115, 46, 100, 105, 114, 0, 103, 117, 116, 101, 110, 46, 116, 97, 103, 0, 105, 110, 116
    db 101, 110, 116, 95, 114, 117, 108, 101, 0, 109, 101, 109, 98, 101, 114, 0, 114, 97, 110, 100, 111, 109, 95, 98
    db 101, 116, 119, 101, 101, 110, 0

__prolog_pred_group_0_descriptors:
    dd __prolog_clause_193_desc
__prolog_pred_group_1_descriptors:
    dd __prolog_clause_185_desc, __prolog_clause_186_desc, __prolog_clause_187_desc, __prolog_clause_188_desc, __prolog_clause_189_desc, __prolog_clause_190_desc
__prolog_pred_group_2_descriptors:
    dd __prolog_clause_0_desc, __prolog_clause_1_desc, __prolog_clause_2_desc, __prolog_clause_3_desc, __prolog_clause_4_desc, __prolog_clause_5_desc, __prolog_clause_6_desc, __prolog_clause_7_desc
    dd __prolog_clause_8_desc
__prolog_pred_group_3_descriptors:
    dd __prolog_clause_9_desc, __prolog_clause_10_desc, __prolog_clause_11_desc, __prolog_clause_12_desc, __prolog_clause_13_desc, __prolog_clause_14_desc, __prolog_clause_15_desc, __prolog_clause_16_desc
__prolog_pred_group_4_descriptors:
    dd __prolog_clause_191_desc, __prolog_clause_192_desc
__prolog_pred_group_5_descriptors:
    dd __prolog_clause_194_desc, __prolog_clause_195_desc
__prolog_pred_group_6_descriptors:
    dd __prolog_clause_18_desc
__prolog_pred_group_7_descriptors:
    dd __prolog_clause_170_desc, __prolog_clause_171_desc
__prolog_pred_group_8_descriptors:
    dd __prolog_clause_174_desc
__prolog_pred_group_9_descriptors:
    dd __prolog_clause_172_desc, __prolog_clause_173_desc
__prolog_pred_group_10_descriptors:
    dd __prolog_clause_179_desc, __prolog_clause_180_desc, __prolog_clause_181_desc, __prolog_clause_182_desc, __prolog_clause_183_desc
__prolog_pred_group_11_descriptors:
    dd __prolog_clause_184_desc
__prolog_pred_group_12_descriptors:
    dd __prolog_clause_175_desc, __prolog_clause_176_desc, __prolog_clause_177_desc, __prolog_clause_178_desc
__prolog_pred_group_13_descriptors:
    dd __prolog_clause_125_desc, __prolog_clause_126_desc, __prolog_clause_127_desc, __prolog_clause_128_desc, __prolog_clause_129_desc, __prolog_clause_130_desc, __prolog_clause_131_desc, __prolog_clause_132_desc
    dd __prolog_clause_133_desc, __prolog_clause_134_desc
__prolog_pred_group_14_descriptors:
    dd __prolog_clause_135_desc, __prolog_clause_136_desc
__prolog_pred_group_15_descriptors:
    dd __prolog_clause_17_desc
__prolog_pred_group_16_descriptors:
    dd __prolog_clause_137_desc, __prolog_clause_138_desc, __prolog_clause_139_desc, __prolog_clause_140_desc, __prolog_clause_141_desc, __prolog_clause_142_desc, __prolog_clause_143_desc, __prolog_clause_144_desc
    dd __prolog_clause_145_desc, __prolog_clause_146_desc, __prolog_clause_147_desc, __prolog_clause_148_desc, __prolog_clause_149_desc, __prolog_clause_150_desc, __prolog_clause_151_desc, __prolog_clause_152_desc
    dd __prolog_clause_153_desc, __prolog_clause_154_desc, __prolog_clause_155_desc, __prolog_clause_156_desc, __prolog_clause_157_desc, __prolog_clause_158_desc, __prolog_clause_159_desc, __prolog_clause_160_desc
    dd __prolog_clause_161_desc, __prolog_clause_162_desc, __prolog_clause_163_desc, __prolog_clause_164_desc, __prolog_clause_165_desc, __prolog_clause_166_desc, __prolog_clause_167_desc, __prolog_clause_168_desc
    dd __prolog_clause_169_desc
__prolog_pred_group_17_descriptors:
    dd __prolog_clause_94_desc, __prolog_clause_95_desc, __prolog_clause_96_desc, __prolog_clause_97_desc, __prolog_clause_98_desc, __prolog_clause_99_desc, __prolog_clause_100_desc, __prolog_clause_101_desc
    dd __prolog_clause_102_desc, __prolog_clause_103_desc, __prolog_clause_104_desc, __prolog_clause_105_desc, __prolog_clause_106_desc, __prolog_clause_107_desc, __prolog_clause_108_desc, __prolog_clause_109_desc
    dd __prolog_clause_110_desc, __prolog_clause_111_desc, __prolog_clause_112_desc, __prolog_clause_113_desc, __prolog_clause_114_desc, __prolog_clause_115_desc, __prolog_clause_116_desc, __prolog_clause_117_desc
    dd __prolog_clause_118_desc, __prolog_clause_119_desc, __prolog_clause_120_desc, __prolog_clause_121_desc, __prolog_clause_122_desc, __prolog_clause_123_desc, __prolog_clause_124_desc
__prolog_pred_group_18_descriptors:
    dd __prolog_clause_23_desc, __prolog_clause_24_desc, __prolog_clause_25_desc, __prolog_clause_26_desc, __prolog_clause_27_desc, __prolog_clause_28_desc, __prolog_clause_29_desc, __prolog_clause_30_desc
    dd __prolog_clause_31_desc, __prolog_clause_32_desc, __prolog_clause_33_desc, __prolog_clause_34_desc, __prolog_clause_35_desc, __prolog_clause_36_desc, __prolog_clause_37_desc, __prolog_clause_38_desc
    dd __prolog_clause_39_desc, __prolog_clause_40_desc, __prolog_clause_41_desc, __prolog_clause_42_desc, __prolog_clause_43_desc, __prolog_clause_44_desc, __prolog_clause_45_desc, __prolog_clause_46_desc
    dd __prolog_clause_47_desc, __prolog_clause_48_desc, __prolog_clause_49_desc, __prolog_clause_50_desc, __prolog_clause_51_desc, __prolog_clause_52_desc, __prolog_clause_53_desc, __prolog_clause_54_desc
    dd __prolog_clause_55_desc, __prolog_clause_56_desc, __prolog_clause_57_desc, __prolog_clause_58_desc, __prolog_clause_59_desc, __prolog_clause_60_desc, __prolog_clause_61_desc, __prolog_clause_62_desc
    dd __prolog_clause_63_desc, __prolog_clause_64_desc, __prolog_clause_65_desc, __prolog_clause_66_desc, __prolog_clause_67_desc, __prolog_clause_68_desc, __prolog_clause_69_desc, __prolog_clause_70_desc
    dd __prolog_clause_71_desc, __prolog_clause_72_desc, __prolog_clause_73_desc, __prolog_clause_74_desc, __prolog_clause_75_desc, __prolog_clause_76_desc, __prolog_clause_77_desc, __prolog_clause_78_desc
    dd __prolog_clause_79_desc, __prolog_clause_80_desc, __prolog_clause_81_desc, __prolog_clause_82_desc, __prolog_clause_83_desc, __prolog_clause_84_desc, __prolog_clause_85_desc, __prolog_clause_86_desc
    dd __prolog_clause_87_desc, __prolog_clause_88_desc, __prolog_clause_89_desc, __prolog_clause_90_desc, __prolog_clause_91_desc, __prolog_clause_92_desc, __prolog_clause_93_desc
__prolog_pred_group_19_descriptors:
    dd __prolog_clause_19_desc, __prolog_clause_20_desc, __prolog_clause_21_desc, __prolog_clause_22_desc

; Stage 288: generic descriptor structural programs
__prolog_clause_template_table:
    dd __prolog_clause_template_0_desc, __prolog_clause_template_1_desc, __prolog_clause_template_2_desc, __prolog_clause_template_3_desc, __prolog_clause_template_4_desc, __prolog_clause_template_5_desc, __prolog_clause_template_6_desc, __prolog_clause_template_7_desc
    dd __prolog_clause_template_8_desc, __prolog_clause_template_9_desc, __prolog_clause_template_10_desc, __prolog_clause_template_11_desc, __prolog_clause_template_12_desc, __prolog_clause_template_13_desc, __prolog_clause_template_14_desc, __prolog_clause_template_15_desc
    dd __prolog_clause_template_16_desc, __prolog_clause_template_17_desc, __prolog_clause_template_18_desc, __prolog_clause_template_19_desc, __prolog_clause_template_20_desc, __prolog_clause_template_21_desc, __prolog_clause_template_22_desc, __prolog_clause_template_23_desc
    dd __prolog_clause_template_24_desc
__prolog_clause_template_0_desc:
    dw 0, 0, 8, 0, 1, 5, 1
__prolog_clause_template_1_desc:
    dw 0, 0, 8, 0, 2, 5, 2, 5, 1
__prolog_clause_template_2_desc:
    dw 0, 0, 8, 0, 1, 7, 7, 6, 5, 2, 5, 1
__prolog_clause_template_3_desc:
    dw 0, 0, 8, 0, 2, 4, 2, 5, 1
__prolog_clause_template_4_desc:
    dw 0, 0, 8, 0, 3, 7, 7, 6, 5, 4, 5, 3, 5, 2, 5, 1
__prolog_clause_template_5_desc:
    dw 0, 0, 8, 0, 2, 6, 6
__prolog_clause_template_6_desc:
    dw 4, 2, 8, 0, 2, 7, 1, 3, 1, 2, 7, 1, 1, 1, 0, 8
    dw 2, 2, 1, 3, 1, 1, 8, 1, 2, 1, 2, 1, 0
__prolog_clause_template_7_desc:
    dw 0, 0, 8, 0, 2, 7, 7, 7, 7, 7, 6, 5, 6, 5, 5, 5
    dw 4, 5, 3, 5, 2, 5, 1
__prolog_clause_template_8_desc:
    dw 0, 0, 8, 0, 2, 7, 7, 7, 6, 5, 4, 5, 3, 5, 2, 5
    dw 1
__prolog_clause_template_9_desc:
    dw 0, 0, 8, 0, 2, 7, 7, 7, 7, 6, 5, 5, 5, 4, 5, 3
    dw 5, 2, 5, 1
__prolog_clause_template_10_desc:
    dw 0, 0, 8, 0, 2, 7, 7, 6, 5, 3, 5, 2, 5, 1
__prolog_clause_template_11_desc:
    dw 0, 0, 8, 0, 2, 7, 6, 5, 2, 5, 1
__prolog_clause_template_12_desc:
    dw 0, 0, 8, 0, 2, 2, 1, 6
__prolog_clause_template_13_desc:
    dw 4, 2, 8, 0, 2, 1, 2, 7, 1, 1, 1, 0, 8, 2, 2, 8
    dw 3, 2, 2, 4, 1, 3, 1, 2, 8, 1, 2, 1, 3, 1, 1
__prolog_clause_template_14_desc:
    dw 2, 0, 8, 0, 3, 1, 0, 7, 1, 1, 1, 0, 2, 1
__prolog_clause_template_15_desc:
    dw 5, 3, 8, 0, 3, 1, 3, 7, 1, 2, 1, 1, 1, 0, 8, 6
    dw 3, 1, 3, 1, 2, 1, 4, 8, 3, 2, 8, 4, 2, 2, 5, 1
    dw 0, 1, 4, 8, 1, 2, 2, 2, 1, 0
__prolog_clause_template_16_desc:
    dw 4, 3, 8, 0, 2, 1, 1, 1, 0, 8, 3, 3, 1, 1, 1, 0
    dw 1, 3, 8, 2, 2, 1, 3, 1, 2, 8, 1, 2, 1, 2, 1, 0
__prolog_clause_template_17_desc:
    dw 1, 1, 8, 0, 2, 1, 0, 5, 1, 8, 2, 2, 1, 0, 7, 7
    dw 7, 7, 6, 5, 6, 5, 5, 5, 4, 5, 3
__prolog_clause_template_18_desc:
    dw 1, 1, 8, 0, 2, 1, 0, 5, 1, 8, 2, 2, 1, 0, 7, 7
    dw 6, 5, 4, 5, 3
__prolog_clause_template_19_desc:
    dw 1, 1, 8, 0, 2, 1, 0, 5, 1, 8, 2, 2, 1, 0, 7, 7
    dw 7, 6, 5, 5, 5, 4, 5, 3
__prolog_clause_template_20_desc:
    dw 3, 2, 8, 0, 2, 1, 1, 1, 0, 8, 2, 2, 1, 1, 1, 2
    dw 8, 1, 2, 1, 2, 1, 0
__prolog_clause_template_21_desc:
    dw 0, 0, 8, 0, 2, 5, 4, 7, 7, 7, 6, 5, 3, 5, 2, 5
    dw 1
__prolog_clause_template_22_desc:
    dw 2, 0, 8, 0, 2, 7, 1, 1, 1, 0, 1, 0
__prolog_clause_template_23_desc:
    dw 3, 1, 8, 0, 2, 7, 1, 2, 1, 1, 1, 0, 8, 1, 2, 1
    dw 2, 1, 0
__prolog_clause_template_24_desc:
    dw 2, 1, 8, 0, 2, 1, 1, 1, 0, 8, 1, 2, 1, 1, 1, 0

; Stage 288: per-clause descriptor payloads
__prolog_clause_0_desc:
    dd 0, 76, 77
__prolog_clause_1_desc:
    dd 0, 76, 78
__prolog_clause_2_desc:
    dd 0, 76, 79
__prolog_clause_3_desc:
    dd 0, 76, 80
__prolog_clause_4_desc:
    dd 0, 76, 81
__prolog_clause_5_desc:
    dd 0, 76, 82
__prolog_clause_6_desc:
    dd 0, 76, 83
__prolog_clause_7_desc:
    dd 0, 76, 84
__prolog_clause_8_desc:
    dd 0, 76, 85
__prolog_clause_9_desc:
    dd 1, 86, 77, 87
__prolog_clause_10_desc:
    dd 1, 86, 78, 88
__prolog_clause_11_desc:
    dd 1, 86, 79, 89
__prolog_clause_12_desc:
    dd 1, 86, 80, 90
__prolog_clause_13_desc:
    dd 1, 86, 81, 91
__prolog_clause_14_desc:
    dd 1, 86, 82, 92
__prolog_clause_15_desc:
    dd 1, 86, 83, 93
__prolog_clause_16_desc:
    dd 1, 86, 84, 94
__prolog_clause_17_desc:
    dd 2, 95, 96, 97
__prolog_clause_18_desc:
    dd 2, 98, 99, 100
__prolog_clause_19_desc:
    dd 3, 101, 102, 103
__prolog_clause_20_desc:
    dd 3, 101, 102, 104
__prolog_clause_21_desc:
    dd 3, 101, 105, 106
__prolog_clause_22_desc:
    dd 3, 101, 105, 107
__prolog_clause_23_desc:
    dd 4, 108, 102, 109, 110, 111
__prolog_clause_24_desc:
    dd 4, 108, 102, 109, 112, 111
__prolog_clause_25_desc:
    dd 4, 108, 105, 109, 110, 111
__prolog_clause_26_desc:
    dd 4, 108, 105, 109, 112, 98
__prolog_clause_27_desc:
    dd 4, 108, 113, 109, 112, 98
__prolog_clause_28_desc:
    dd 4, 108, 114, 109, 115, 111
__prolog_clause_29_desc:
    dd 4, 108, 116, 109, 112, 111
__prolog_clause_30_desc:
    dd 4, 108, 117, 109, 112, 98
__prolog_clause_31_desc:
    dd 4, 108, 118, 109, 110, 111
__prolog_clause_32_desc:
    dd 4, 108, 119, 109, 115, 111
__prolog_clause_33_desc:
    dd 4, 108, 120, 109, 112, 111
__prolog_clause_34_desc:
    dd 4, 108, 121, 109, 112, 111
__prolog_clause_35_desc:
    dd 4, 108, 122, 109, 112, 111
__prolog_clause_36_desc:
    dd 4, 108, 123, 109, 110, 111
__prolog_clause_37_desc:
    dd 4, 108, 124, 109, 110, 111
__prolog_clause_38_desc:
    dd 4, 108, 125, 109, 112, 111
__prolog_clause_39_desc:
    dd 4, 108, 126, 109, 112, 111
__prolog_clause_40_desc:
    dd 4, 108, 127, 109, 110, 111
__prolog_clause_41_desc:
    dd 4, 108, 128, 109, 110, 111
__prolog_clause_42_desc:
    dd 4, 108, 129, 109, 115, 111
__prolog_clause_43_desc:
    dd 4, 108, 130, 109, 115, 111
__prolog_clause_44_desc:
    dd 4, 108, 131, 109, 112, 111
__prolog_clause_45_desc:
    dd 4, 108, 132, 109, 115, 111
__prolog_clause_46_desc:
    dd 4, 108, 133, 109, 110, 111
__prolog_clause_47_desc:
    dd 4, 108, 134, 109, 110, 111
__prolog_clause_48_desc:
    dd 4, 108, 135, 109, 112, 111
__prolog_clause_49_desc:
    dd 4, 108, 136, 109, 115, 111
__prolog_clause_50_desc:
    dd 4, 108, 137, 109, 112, 98
__prolog_clause_51_desc:
    dd 4, 108, 138, 109, 115, 111
__prolog_clause_52_desc:
    dd 4, 108, 139, 109, 112, 111
__prolog_clause_53_desc:
    dd 4, 108, 140, 109, 112, 111
__prolog_clause_54_desc:
    dd 4, 108, 141, 109, 112, 111
__prolog_clause_55_desc:
    dd 4, 108, 142, 109, 110, 111
__prolog_clause_56_desc:
    dd 4, 108, 143, 109, 110, 111
__prolog_clause_57_desc:
    dd 4, 108, 144, 109, 110, 111
__prolog_clause_58_desc:
    dd 4, 108, 145, 109, 115, 111
__prolog_clause_59_desc:
    dd 4, 108, 146, 109, 112, 111
__prolog_clause_60_desc:
    dd 4, 108, 147, 109, 110, 111
__prolog_clause_61_desc:
    dd 4, 108, 148, 109, 110, 111
__prolog_clause_62_desc:
    dd 4, 108, 149, 109, 110, 111
__prolog_clause_63_desc:
    dd 4, 108, 150, 109, 110, 111
__prolog_clause_64_desc:
    dd 4, 108, 151, 109, 110, 111
__prolog_clause_65_desc:
    dd 4, 108, 152, 109, 112, 111
__prolog_clause_66_desc:
    dd 4, 108, 153, 109, 112, 98
__prolog_clause_67_desc:
    dd 4, 108, 154, 109, 112, 111
__prolog_clause_68_desc:
    dd 4, 108, 155, 109, 110, 111
__prolog_clause_69_desc:
    dd 4, 108, 156, 109, 110, 111
__prolog_clause_70_desc:
    dd 4, 108, 157, 109, 110, 111
__prolog_clause_71_desc:
    dd 4, 108, 158, 109, 115, 111
__prolog_clause_72_desc:
    dd 4, 108, 159, 109, 112, 98
__prolog_clause_73_desc:
    dd 4, 108, 160, 109, 112, 111
__prolog_clause_74_desc:
    dd 4, 108, 161, 109, 112, 98
__prolog_clause_75_desc:
    dd 4, 108, 162, 109, 110, 111
__prolog_clause_76_desc:
    dd 4, 108, 163, 109, 112, 98
__prolog_clause_77_desc:
    dd 4, 108, 164, 109, 112, 111
__prolog_clause_78_desc:
    dd 4, 108, 165, 109, 112, 111
__prolog_clause_79_desc:
    dd 4, 108, 166, 109, 112, 111
__prolog_clause_80_desc:
    dd 4, 108, 167, 109, 112, 111
__prolog_clause_81_desc:
    dd 4, 108, 168, 109, 112, 98
__prolog_clause_82_desc:
    dd 4, 108, 169, 109, 110, 111
__prolog_clause_83_desc:
    dd 4, 108, 170, 109, 110, 111
__prolog_clause_84_desc:
    dd 4, 108, 171, 109, 110, 111
__prolog_clause_85_desc:
    dd 4, 108, 172, 109, 115, 111
__prolog_clause_86_desc:
    dd 4, 108, 173, 109, 110, 111
__prolog_clause_87_desc:
    dd 4, 108, 174, 109, 110, 111
__prolog_clause_88_desc:
    dd 4, 108, 175, 109, 110, 111
__prolog_clause_89_desc:
    dd 4, 108, 176, 109, 112, 111
__prolog_clause_90_desc:
    dd 4, 108, 177, 109, 110, 111
__prolog_clause_91_desc:
    dd 4, 108, 178, 109, 110, 111
__prolog_clause_92_desc:
    dd 4, 108, 179, 109, 112, 111
__prolog_clause_93_desc:
    dd 4, 108, 180, 109, 110, 111
__prolog_clause_94_desc:
    dd 1, 108, 181, 182
__prolog_clause_95_desc:
    dd 1, 108, 183, 182
__prolog_clause_96_desc:
    dd 1, 108, 184, 182
__prolog_clause_97_desc:
    dd 1, 108, 185, 182
__prolog_clause_98_desc:
    dd 1, 108, 186, 182
__prolog_clause_99_desc:
    dd 1, 108, 187, 182
__prolog_clause_100_desc:
    dd 1, 108, 188, 182
__prolog_clause_101_desc:
    dd 1, 108, 189, 182
__prolog_clause_102_desc:
    dd 1, 108, 190, 182
__prolog_clause_103_desc:
    dd 1, 108, 191, 192
__prolog_clause_104_desc:
    dd 1, 108, 193, 192
__prolog_clause_105_desc:
    dd 1, 108, 194, 192
__prolog_clause_106_desc:
    dd 1, 108, 195, 192
__prolog_clause_107_desc:
    dd 1, 108, 196, 192
__prolog_clause_108_desc:
    dd 1, 108, 197, 192
__prolog_clause_109_desc:
    dd 1, 108, 198, 199
__prolog_clause_110_desc:
    dd 1, 108, 200, 199
__prolog_clause_111_desc:
    dd 1, 108, 201, 199
__prolog_clause_112_desc:
    dd 1, 108, 202, 199
__prolog_clause_113_desc:
    dd 1, 108, 197, 199
__prolog_clause_114_desc:
    dd 1, 108, 203, 199
__prolog_clause_115_desc:
    dd 1, 108, 204, 205
__prolog_clause_116_desc:
    dd 1, 108, 206, 205
__prolog_clause_117_desc:
    dd 1, 108, 207, 205
__prolog_clause_118_desc:
    dd 1, 108, 208, 205
__prolog_clause_119_desc:
    dd 1, 108, 209, 205
__prolog_clause_120_desc:
    dd 1, 108, 210, 205
__prolog_clause_121_desc:
    dd 1, 108, 211, 205
__prolog_clause_122_desc:
    dd 1, 108, 212, 205
__prolog_clause_123_desc:
    dd 1, 108, 213, 205
__prolog_clause_124_desc:
    dd 1, 108, 214, 205
__prolog_clause_125_desc:
    dd 1, 215, 204, 216
__prolog_clause_126_desc:
    dd 1, 215, 206, 216
__prolog_clause_127_desc:
    dd 1, 215, 216, 216
__prolog_clause_128_desc:
    dd 1, 215, 193, 217
__prolog_clause_129_desc:
    dd 1, 215, 201, 217
__prolog_clause_130_desc:
    dd 1, 215, 195, 218
__prolog_clause_131_desc:
    dd 1, 215, 197, 218
__prolog_clause_132_desc:
    dd 1, 215, 181, 182
__prolog_clause_133_desc:
    dd 1, 215, 184, 182
__prolog_clause_134_desc:
    dd 1, 215, 183, 182
__prolog_clause_135_desc:
    dd 5, 219
__prolog_clause_136_desc:
    dd 6, 219, 215, 219
__prolog_clause_137_desc:
    dd 7, 220, 85, 110, 118, 221, 222, 223
__prolog_clause_138_desc:
    dd 8, 220, 77, 181, 204, 193
__prolog_clause_139_desc:
    dd 9, 220, 77, 181, 207, 201, 216
__prolog_clause_140_desc:
    dd 9, 220, 77, 183, 207, 201, 216
__prolog_clause_141_desc:
    dd 8, 220, 77, 184, 210, 193
__prolog_clause_142_desc:
    dd 9, 220, 77, 224, 225, 226, 227
__prolog_clause_143_desc:
    dd 8, 220, 78, 181, 206, 195
__prolog_clause_144_desc:
    dd 9, 220, 78, 181, 207, 197, 216
__prolog_clause_145_desc:
    dd 9, 220, 78, 183, 207, 197, 216
__prolog_clause_146_desc:
    dd 8, 220, 78, 184, 208, 195
__prolog_clause_147_desc:
    dd 10, 220, 79, 181, 204
__prolog_clause_148_desc:
    dd 10, 220, 79, 181, 206
__prolog_clause_149_desc:
    dd 11, 220, 80, 228
__prolog_clause_150_desc:
    dd 11, 220, 80, 229
__prolog_clause_151_desc:
    dd 11, 220, 80, 230
__prolog_clause_152_desc:
    dd 10, 220, 80, 231, 232
__prolog_clause_153_desc:
    dd 10, 220, 80, 231, 233
__prolog_clause_154_desc:
    dd 10, 220, 80, 231, 234
__prolog_clause_155_desc:
    dd 11, 220, 80, 235
__prolog_clause_156_desc:
    dd 11, 220, 81, 236
__prolog_clause_157_desc:
    dd 10, 220, 81, 237, 238
__prolog_clause_158_desc:
    dd 10, 220, 81, 239, 240
__prolog_clause_159_desc:
    dd 10, 220, 81, 239, 241
__prolog_clause_160_desc:
    dd 11, 220, 81, 242
__prolog_clause_161_desc:
    dd 9, 220, 82, 181, 209, 243, 244
__prolog_clause_162_desc:
    dd 10, 220, 82, 181, 245
__prolog_clause_163_desc:
    dd 8, 220, 82, 181, 209, 243
__prolog_clause_164_desc:
    dd 10, 220, 82, 246, 247
__prolog_clause_165_desc:
    dd 9, 220, 82, 181, 248, 193, 249
__prolog_clause_166_desc:
    dd 8, 220, 83, 184, 210, 193
__prolog_clause_167_desc:
    dd 8, 220, 83, 183, 210, 193
__prolog_clause_168_desc:
    dd 8, 220, 83, 183, 213, 193
__prolog_clause_169_desc:
    dd 8, 220, 83, 184, 250, 197
__prolog_clause_170_desc:
    dd 12, 251, 0
__prolog_clause_171_desc:
    dd 13, 251, 251, 13, 18, 1
__prolog_clause_172_desc:
    dd 14, 252, 0
__prolog_clause_173_desc:
    dd 15, 252, 16, 0, 13, 19, 1, 252
__prolog_clause_174_desc:
    dd 16, 253, 251, 254, 252
__prolog_clause_175_desc:
    dd 1, 255, 85, 256
__prolog_clause_176_desc:
    dd 1, 255, 83, 257
__prolog_clause_177_desc:
    dd 1, 255, 84, 258
__prolog_clause_178_desc:
    dd 1, 255, 84, 259
__prolog_clause_179_desc:
    dd 17, 260, 77, 253, 261, 262, 263, 264
__prolog_clause_180_desc:
    dd 17, 260, 78, 253, 265, 266, 267, 268
__prolog_clause_181_desc:
    dd 18, 260, 82, 253, 269, 270
__prolog_clause_182_desc:
    dd 17, 260, 80, 253, 271, 272, 273, 274
__prolog_clause_183_desc:
    dd 19, 260, 81, 253, 275, 276, 277
__prolog_clause_184_desc:
    dd 20, 278, 279, 260
__prolog_clause_185_desc:
    dd 1, 280, 77, 281
__prolog_clause_186_desc:
    dd 1, 280, 77, 282
__prolog_clause_187_desc:
    dd 1, 280, 78, 283
__prolog_clause_188_desc:
    dd 1, 280, 78, 284
__prolog_clause_189_desc:
    dd 1, 280, 82, 285
__prolog_clause_190_desc:
    dd 1, 280, 80, 286
__prolog_clause_191_desc:
    dd 21, 287, 182, 216, 217, 77
__prolog_clause_192_desc:
    dd 21, 287, 182, 216, 218, 78
__prolog_clause_193_desc:
    dd 20, 279, 219, 287
__prolog_clause_194_desc:
    dd 22, 288
__prolog_clause_195_desc:
    dd 23, 288, 288
__prolog_clause_196_desc:
    dd 24, 72, 75

__prolog_caption:
    db 80, 114, 111, 108, 111, 103, 32, 45, 32, 40, 99, 41, 32, 50, 48, 50, 54, 32, 98, 121, 32, 74, 101, 110
    db 115, 32, 75, 97, 108, 108, 117, 112, 0
__prolog_fmt_int:
    db 37, 100, 0
__prolog_text_underscore:
    db 95, 0
__prolog_text_nil:
    db 91, 93, 0
__prolog_text_lbrack:
    db 91, 0
__prolog_text_rbrack:
    db 93, 0
__prolog_text_bar:
    db 32, 124, 32, 0
__prolog_text_lparen:
    db 40, 0
__prolog_text_rparen:
    db 41, 0
__prolog_text_comma_space:
    db 44, 32, 0
__prolog_text_equals:
    db 32, 61, 32, 0
__prolog_text_quote:
    db 34, 0
__prolog_text_dot_nl:
    db 46, 13, 10, 0
__prolog_text_newline:
    db 13, 10, 0
__prolog_text_true_line:
    db 116, 114, 117, 101, 46, 13, 10, 0
__prolog_text_false_line:
    db 107, 101, 105, 110, 101, 32, 119, 101, 105, 116, 101, 114, 101, 110, 32, 65, 110, 116, 119, 111, 114, 116, 101, 110
    db 46, 13, 10, 0
__prolog_text_prompt:
    db 63, 45, 32, 0
__prolog_text_more_prompt:
    db 69, 78, 84, 69, 82, 32, 61, 32, 119, 101, 105, 116, 101, 114, 101, 32, 76, 246, 115, 117, 110, 103, 44, 32
    db 113, 32, 61, 32, 122, 117, 114, 252, 99, 107, 32, 122, 117, 109, 32, 80, 114, 111, 109, 112, 116, 32, 40, 59
    db 32, 61, 32, 83, 87, 73, 45, 114, 101, 100, 111, 41, 58, 32, 0
__prolog_text_parse_error:
    db 115, 121, 110, 116, 97, 120, 95, 101, 114, 114, 111, 114, 46, 13, 10, 0
__prolog_text_repl_gui:
    db 114, 101, 112, 108, 47, 48, 32, 105, 115, 116, 32, 110, 117, 114, 32, 105, 109, 32, 67, 111, 110, 115, 111, 108
    db 101, 45, 77, 111, 100, 117, 115, 32, 118, 101, 114, 102, 252, 103, 98, 97, 114, 46, 13, 10, 0
__prolog_qt_dll_name:
    db 108, 105, 98, 100, 54, 52, 95, 113, 116, 53, 46, 100, 108, 108, 0
__prolog_qt_name_init:
    db 68, 66, 97, 115, 101, 81, 116, 80, 114, 111, 108, 111, 103, 73, 110, 105, 116, 105, 97, 108, 105, 122, 101, 0
__prolog_qt_name_write:
    db 68, 66, 97, 115, 101, 81, 116, 80, 114, 111, 108, 111, 103, 87, 114, 105, 116, 101, 0
__prolog_qt_name_read:
    db 68, 66, 97, 115, 101, 81, 116, 80, 114, 111, 108, 111, 103, 82, 101, 97, 100, 76, 105, 110, 101, 0
__prolog_qt_name_shutdown:
    db 68, 66, 97, 115, 101, 81, 116, 80, 114, 111, 108, 111, 103, 83, 104, 117, 116, 100, 111, 119, 110, 0
__prolog_gui_launch_error:
    db 80, 82, 79, 76, 79, 71, 32, 45, 45, 103, 117, 105, 58, 32, 110, 97, 116, 105, 118, 101, 32, 81, 116, 53
    db 45, 82, 117, 110, 116, 105, 109, 101, 32, 108, 105, 98, 100, 54, 52, 95, 113, 116, 53, 46, 100, 108, 108, 32
    db 102, 101, 104, 108, 116, 32, 111, 100, 101, 114, 32, 98, 101, 115, 105, 116, 122, 116, 32, 110, 105, 99, 104, 116
    db 32, 100, 105, 101, 32, 83, 116, 97, 103, 101, 45, 50, 57, 53, 45, 80, 82, 79, 76, 79, 71, 45, 83, 99
    db 104, 110, 105, 116, 116, 115, 116, 101, 108, 108, 101, 46, 0
__prolog_fmt_saved_var:
    db 95, 86, 37, 100, 0
__prolog_text_rule_sep:
    db 32, 58, 45, 32, 0
__prolog_text_knowledge_sep:
    db 32, 61, 32, 0
__prolog_text_clause_end:
    db 46, 13, 10, 0
__prolog_text_op_comma:
    db 32, 44, 32, 0
__prolog_text_op_semi:
    db 32, 59, 32, 0
__prolog_text_op_eq:
    db 32, 61, 32, 0
__prolog_text_op_ne:
    db 32, 92, 61, 32, 0
__prolog_text_op_strict_eq:
    db 32, 61, 61, 32, 0
__prolog_text_op_is:
    db 32, 105, 115, 32, 0
__prolog_text_op_lt:
    db 32, 60, 32, 0
__prolog_text_op_le:
    db 32, 61, 60, 32, 0
__prolog_text_op_gt:
    db 32, 62, 32, 0
__prolog_text_op_ge:
    db 32, 62, 61, 32, 0
__prolog_text_op_plus:
    db 32, 43, 32, 0
__prolog_text_op_minus:
    db 32, 45, 32, 0
__prolog_text_op_mul:
    db 32, 42, 32, 0
__prolog_text_op_div:
    db 32, 47, 32, 0
__prolog_text_op_mod:
    db 32, 109, 111, 100, 32, 0

section .bss
__prolog_arena:
    resd 1
__prolog_stdout:
    resd 1
__prolog_stdin:
    resd 1
__prolog_dyn_base:
    resd 1
__prolog_dyn_alt_base:
    resd 1
__prolog_db_file_handle:
    resd 1
__prolog_emit_file_handle:
    resd 1
__prolog_qt_module:
    resd 1
__prolog_qt_init_fn:
    resd 1
__prolog_qt_write_fn:
    resd 1
__prolog_qt_read_fn:
    resd 1
__prolog_qt_shutdown_fn:
    resd 1
__prolog_heap_top:
    resd 1
__prolog_dyn_heap_top:
    resd 1
__prolog_trail_top:
    resd 1
__prolog_choice_top:
    resd 1
__prolog_dyn_count:
    resd 1
__prolog_dyn_atom_count:
    resd 1
__prolog_atom_pool_top:
    resd 1
__prolog_output_top:
    resd 1
__prolog_query_var_count:
    resd 1
__prolog_solution_count:
    resd 1
__prolog_read_count:
    resd 1
__prolog_parse_pos:
    resd 1
__prolog_qname_top:
    resd 1
__prolog_written:
    resd 1
__prolog_dyn_copy_var_count:
    resd 1
__prolog_dyn_clone_var_count:
    resd 1
__prolog_current_cut_barrier:
    resd 1
__prolog_cut_active_barrier:
    resd 1
__prolog_build_barrier:
    resd 1
__prolog_interactive_mode:
    resd 1
__prolog_stop_search:
    resd 1
__prolog_requested_more:
    resd 1
__prolog_direct_eval:
    resd 1
__prolog_verbose:
    resd 1
__prolog_gc_heap_mark:
    resd 1
__prolog_db_next_id:
    resd 1
__prolog_current_db:
    resd 1
__prolog_db_loading:
    resd 1
__prolog_db_file_read:
    resd 1
__prolog_db_file_pos:
    resd 1
__prolog_db_heap_mark:
    resd 1
__prolog_parser_db_mode:
    resd 1
__prolog_db_parser_var_count:
    resd 1
__prolog_db_parser_name_top:
    resd 1
__prolog_save_var_count:
    resd 1
__prolog_emit_to_file:
    resd 1
__prolog_emit_file_error:
    resd 1
__prolog_random_state:
    resd 1
__prolog_start_mode:
    resd 1
__prolog_argc:
    resd 1
__prolog_format_buffer:
    resb 64
