"""Stage 595: copy C ANSI string results into length-based dBASE value slots.

The original C pointer stays DLL-owned.  A PVOID return remains a raw native
address; only LPSTR/LPCSTR (and compatible char-pointer aliases) opt in.

PRG slots contain CP1252 bytes; WFM/Qt slots contain UTF-8.  The latter are
converted via the Windows code-page APIs, not mislabeled ANSI as UTF-8.
"""
from __future__ import annotations

MAX_C_STRING_BYTES = 16 * 1024 * 1024


def returns_ansi_string(type_name: str) -> bool:
    from .ffi_types import ffi_type_info
    info = ffi_type_info(type_name)
    return info.category == 'ansi_string' or info.name in {'LPSTR', 'PSTR', 'PCHAR'}


def prg_ansi_result(slot: str, *, is64: bool, prefix: str) -> list[str]:
    """EAX/RAX -> independent, zero-terminated CP1252 allocation in slot.

    This code uses lstrlenA (stdcall Win32), malloc/memcpy (cdecl).  NULL maps
    to empty text.  A huge/invalid length or allocation failure exits with 13;
    there is deliberately no attempt to free the DLL-owned C pointer.
    """
    ptr = 'qword' if is64 else 'dword'
    reg = 'rax' if is64 else 'eax'
    empty, done, failure = (f'{prefix}_{name}' for name in ('empty', 'done', 'failure'))
    out = [
        f'    mov {ptr} ptr [__dbase_ffi_return], {reg}',
        f'    test {reg}, {reg}',
        f'    jz {empty}',
    ]
    if is64:
        out += [
            '    mov rcx, rax',
            '    sub rsp, 40',
            '    call __dbase_ffi_lstrlenA',
            '    add rsp, 40',
        ]
    else:
        out += ['    push eax', '    call __dbase_ffi_lstrlenA']
    out += [
        '    test eax, eax', f'    js {failure}',
        f'    cmp eax, {MAX_C_STRING_BYTES}', f'    ja {failure}',
        f'    mov dword ptr [{slot}_len], eax',
        '    inc eax',
    ]
    if is64:
        out += [
            '    mov ecx, eax', '    sub rsp, 40',
            '    call __dbase_malloc', '    add rsp, 40',
            '    test rax, rax', f'    jz {failure}',
            f'    mov qword ptr [{slot}_ptr], rax',
            '    mov rcx, rax',
            '    mov rdx, qword ptr [__dbase_ffi_return]',
            f'    mov r8d, dword ptr [{slot}_len]',
            '    inc r8d',
            '    sub rsp, 40', '    call __dbase_memcpy', '    add rsp, 40',
        ]
    else:
        out += [
            '    push eax', '    call __dbase_malloc', '    add esp, 4',
            '    test eax, eax', f'    jz {failure}',
            f'    mov dword ptr [{slot}_ptr], eax',
            f'    mov edx, dword ptr [{slot}_len]',
            '    inc edx', '    push edx',
            '    push dword ptr [__dbase_ffi_return]',
            '    push eax', '    call __dbase_memcpy', '    add esp, 12',
        ]
    out += [
        f'    mov dword ptr [{slot}_type], 2',
        f'    jmp {done}',
        f'{empty}:',
        f'    mov {ptr} ptr [{slot}_ptr], 0',
        f'    mov dword ptr [{slot}_len], 0',
        f'    mov dword ptr [{slot}_type], 2',
        f'    jmp {done}',
        f'{failure}:',
    ]
    if is64:
        out += ['    mov ecx, 13', '    sub rsp, 40', '    call ExitProcess']
    else:
        out += ['    push 13', '    call ExitProcess']
    out.append(f'{done}:')
    return out


def wfm_utf8_result(slot: str, *, is64: bool, prefix: str) -> list[str]:
    """EAX/RAX -> independent UTF-8 string in WFM slot (type=3).

    Relies on the WFM callback already having 32 bytes of x64 shadow space;
    x64 calls with 6/8 parameters temporarily reserve 48/64 bytes, aligned
    to 16 bytes.  The intermediate wide buffer is freed; UTF-8 data stays
    allocated, since the WFM slot owns the copy.
    """
    ptr = 'qword' if is64 else 'dword'
    reg = 'rax' if is64 else 'eax'
    src = '__dbase_ffi_ansi_src'
    wide = '__dbase_ffi_ansi_wide'
    wcount = '__dbase_ffi_ansi_wcount'
    ucount = '__dbase_ffi_utf8_count'
    empty, done, free_wide, free_both, error = (f'{prefix}_{name}' for name in
                                                   ('empty', 'done', 'free_wide', 'free_both', 'error'))
    out = [
        f'    mov {ptr} ptr [{src}], {reg}',
        f'    test {reg}, {reg}', f'    jz {empty}',
    ]
    # Probe ANSI (CP1252) input length in UTF-16 code units, including NUL.
    if is64:
        out += [
            '    mov ecx, 1252', '    xor edx, edx',
            f'    mov r8, qword ptr [{src}]', '    mov r9d, -1',
            '    sub rsp, 48', '    mov qword ptr [rsp+32], 0',
            '    mov qword ptr [rsp+40], 0',
            '    call MultiByteToWideChar', '    add rsp, 48',
        ]
    else:
        out += [
            '    push 0', '    push 0', '    push -1', f'    push dword ptr [{src}]',
            '    push 0', '    push 1252', '    call MultiByteToWideChar',
        ]
    out += ['    test eax, eax', f'    jz {empty}',
            f'    cmp eax, {MAX_C_STRING_BYTES + 1}', f'    ja {error}',
            f'    mov dword ptr [{wcount}], eax',
            '    shl eax, 1']
    if is64:
        out += ['    mov ecx, eax', '    call __dbase_ffi_malloc',
                '    test rax, rax', f'    jz {error}', f'    mov qword ptr [{wide}], rax',
                '    mov ecx, 1252', '    xor edx, edx',
                f'    mov r8, qword ptr [{src}]', '    mov r9d, -1',
                '    sub rsp, 48', f'    mov rax, qword ptr [{wide}]',
                '    mov qword ptr [rsp+32], rax', f'    mov eax, dword ptr [{wcount}]',
                '    mov qword ptr [rsp+40], rax',
                '    call MultiByteToWideChar', '    add rsp, 48']
    else:
        out += ['    push eax', '    call __dbase_ffi_malloc', '    add esp, 4',
                '    test eax, eax', f'    jz {error}', f'    mov dword ptr [{wide}], eax',
                f'    push dword ptr [{wcount}]', f'    push dword ptr [{wide}]',
                '    push -1', f'    push dword ptr [{src}]',
                '    push 0', '    push 1252', '    call MultiByteToWideChar']
    out += ['    test eax, eax', f'    jz {free_wide}']
    # Probe UTF-8 byte count including NUL.
    if is64:
        out += ['    mov ecx, 65001', '    xor edx, edx',
                f'    mov r8, qword ptr [{wide}]', '    mov r9d, -1',
                '    sub rsp, 64',
                '    mov qword ptr [rsp+32], 0', '    mov qword ptr [rsp+40], 0',
                '    mov qword ptr [rsp+48], 0', '    mov qword ptr [rsp+56], 0',
                '    call WideCharToMultiByte', '    add rsp, 64']
    else:
        out += ['    push 0', '    push 0', '    push 0', '    push 0',
                '    push -1', f'    push dword ptr [{wide}]',
                '    push 0', '    push 65001', '    call WideCharToMultiByte']
    out += ['    test eax, eax', f'    jz {free_wide}',
            f'    cmp eax, {3 * MAX_C_STRING_BYTES + 1}', f'    ja {free_wide}',
            f'    mov dword ptr [{ucount}], eax']
    if is64:
        out += ['    mov ecx, eax', '    call __dbase_ffi_malloc',
                '    test rax, rax', f'    jz {free_wide}',
                f'    mov qword ptr [{slot}_ptr], rax',
                '    mov ecx, 65001', '    xor edx, edx',
                f'    mov r8, qword ptr [{wide}]', '    mov r9d, -1',
                '    sub rsp, 64',
                f'    mov rax, qword ptr [{slot}_ptr]', '    mov qword ptr [rsp+32], rax',
                f'    mov eax, dword ptr [{ucount}]', '    mov qword ptr [rsp+40], rax',
                '    mov qword ptr [rsp+48], 0', '    mov qword ptr [rsp+56], 0',
                '    call WideCharToMultiByte', '    add rsp, 64']
    else:
        out += ['    push eax', '    call __dbase_ffi_malloc', '    add esp, 4',
                '    test eax, eax', f'    jz {free_wide}',
                f'    mov dword ptr [{slot}_ptr], eax',
                '    push 0', '    push 0',
                f'    push dword ptr [{ucount}]', f'    push dword ptr [{slot}_ptr]',
                '    push -1', f'    push dword ptr [{wide}]',
                '    push 0', '    push 65001', '    call WideCharToMultiByte']
    out += ['    test eax, eax', f'    jz {free_both}',
            '    dec eax', f'    mov dword ptr [{slot}_len], eax',
            '    mov dword ptr [' + slot + '_type], 3']
    if is64:
        out += [f'    mov rcx, qword ptr [{wide}]', '    call __dbase_ffi_free']
    else:
        out += [f'    push dword ptr [{wide}]', '    call __dbase_ffi_free', '    add esp, 4']
    out += [f'    jmp {done}', f'{free_both}:']
    if is64:
        out += [f'    mov rcx, qword ptr [{slot}_ptr]', '    call __dbase_ffi_free']
    else:
        out += [f'    push dword ptr [{slot}_ptr]', '    call __dbase_ffi_free', '    add esp, 4']
    out += [f'{free_wide}:']
    if is64:
        out += [f'    mov rcx, qword ptr [{wide}]', '    call __dbase_ffi_free']
    else:
        out += [f'    push dword ptr [{wide}]', '    call __dbase_ffi_free', '    add esp, 4']
    out += [f'{error}:', f'{empty}:',
            f'    mov {ptr} ptr [{slot}_ptr], 0',
            f'    mov dword ptr [{slot}_len], 0',
            f'    mov dword ptr [{slot}_type], 3',
            f'{done}:']
    return out
