"""Stage 205: one-based substring, with UTF-8 character boundaries at runtime."""


def substring(value, start, count=None):
    start = max(1, int(start)) - 1
    if start >= len(value):
        return ''
    return value[start:] if count is None else value[start:start + max(0, int(count))]


def emit_substring_copy(source, start, count, destination, is64, prefix, string_type):
    """Copy a bounded UTF-8 substring to a new string; arguments are value slots.

    Numeric arguments truncate toward zero. Nonpositive starts mean position 1;
    nonpositive counts mean empty. Huge positive values saturate before conversion.
    No calls occur while nonvolatile registers or temporary stack space are saved.
    """
    ptr, acc, inp, out, sp = ('qword', 'rax', 'rsi', 'rdi', 'rsp') if is64 else ('dword', 'eax', 'esi', 'edi', 'esp')
    regs = ('rbx', 'rsi', 'rdi', 'rbp') if is64 else ('ebx', 'esi', 'edi', 'ebp')
    L = lambda name: prefix + '_' + name
    lines = [f'    mov eax, dword ptr [{source}_len]', '    add eax, 1']
    if is64:
        lines += ['    mov ecx, eax', '    sub rsp, 40', '    call __dbase_malloc', '    add rsp, 40']
    else:
        lines += ['    push eax', '    call __dbase_malloc', '    add esp, 4']
    lines += [f'    test {acc}, {acc}', f'    jne {L("allocated")}']
    if is64:
        lines += ['    mov ecx, 8', '    sub rsp, 40', '    call ExitProcess']
    else:
        lines += ['    push 8', '    call ExitProcess']
    lines += [L('allocated') + ':', f'    mov {ptr} ptr [{destination}_ptr], {acc}']
    lines += [f'    push {r}' for r in regs]
    lines += [f'    sub {sp}, 16']

    def integer(slot, register, name):
        # IEEE-754 doubles: inspect sign/exponent before x87 integer conversion.
        # This avoids overflow/indefinite integer results on very large inputs.
        return [f'    xor {register}, {register}',
            f'    mov eax, dword ptr [{slot}_num+4]', '    test eax, eax',
            f'    js {L(name+"_done")}', '    cmp eax, 0x41E00000',
            f'    jb {L(name+"_convert")}', f'    mov {register}, 2147483647',
            f'    jmp {L(name+"_done")}', L(name+'_convert') + ':',
            f'    fnstcw word ptr [{sp}]', f'    movzx eax, word ptr [{sp}]',
            '    or eax, 0x0C00', f'    mov dword ptr [{sp}+4], eax',
            f'    fldcw word ptr [{sp}+4]', f'    fld qword ptr [{slot}_num]',
            f'    fistp dword ptr [{sp}+8]', f'    fldcw word ptr [{sp}]',
            f'    mov {register}, dword ptr [{sp}+8]', L(name+'_done') + ':']

    lines += integer(start, 'ebx', 'start')
    lines += ['    test ebx, ebx', f'    je {L("start_ready")}', '    dec ebx', L('start_ready')+':']
    lines += integer(count, 'ecx', 'count') if count else [f'    mov ecx, dword ptr [{source}_len]']
    lines += [f'    add {sp}, 16', f'    mov {inp}, {ptr} ptr [{source}_ptr]',
        f'    mov {out}, {ptr} ptr [{destination}_ptr]',
        f'    mov edx, dword ptr [{source}_len]', L('loop')+':',
        '    test edx, edx', f'    je {L("done")}',
        '    test ecx, ecx', f'    je {L("done")}',
        f'    movzx eax, byte ptr [{inp}]', '    mov ebp, 1',
        '    cmp eax, 194', f'    jb {L("width")}',
        '    cmp eax, 245', f'    jae {L("width")}',
        '    mov ebp, 2', '    cmp eax, 224', f'    jb {L("width")}',
        '    mov ebp, 3', '    cmp eax, 240', f'    jb {L("width")}',
        '    mov ebp, 4', L('width')+':', '    cmp ebp, edx',
        f'    jbe {L("bounded")}', '    mov ebp, 1', L('bounded')+':',
        '    sub edx, ebp', '    test ebx, ebx', f'    je {L("copy")}',
        f'    add {inp}, ' + ('rbp' if is64 else 'ebp'), '    dec ebx',
        f'    jmp {L("loop")}', L('copy')+':',
        f'    movzx eax, byte ptr [{inp}]', f'    mov byte ptr [{out}], al',
        f'    inc {inp}', f'    inc {out}', '    dec ebp', f'    jne {L("copy")}',
        '    dec ecx', f'    jmp {L("loop")}', L('done')+':',
        f'    mov byte ptr [{out}], 0', f'    sub {out}, {ptr} ptr [{destination}_ptr]',
        f'    mov dword ptr [{destination}_len], edi',
        f'    mov dword ptr [{destination}_type], {string_type}']
    lines += [f'    pop {r}' for r in reversed(regs)]
    return lines
