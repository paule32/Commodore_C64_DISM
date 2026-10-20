"""Stage 458: small WFM call sites for DLL-backed UTF-8 string operations.

The Qt5 bridge owns the existing Unicode case tables. All string APIs return
an output byte count or UINT32_MAX on failure and never allocate memory.
The WFM caller owns the allocated result and retains its typed value slot ABI.
"""


def emit_runtime_string_copy(source, destination, is64, prefix, string_type,
                             *, operation, start=None, count=None,
                             shadow_space_reserved=False):
    """Emit a bounded runtime call: substring, upper, lower or fused form."""
    symbols = {
        'substring': 'DBaseUtf8Substring',
        'upper': 'DBaseUtf8Upper',
        'lower': 'DBaseUtf8Lower',
        'substring_upper': 'DBaseUtf8SubstringUpper',
        'substring_lower': 'DBaseUtf8SubstringLower',
    }
    if operation not in symbols:
        raise ValueError('Unknown string operation: ' + str(operation))
    has_span = operation in {'substring', 'substring_upper', 'substring_lower'}
    if has_span and start is None:
        raise ValueError('Substring requires numeric start argument')
    # Upper and lower can expand individual UTF-8 codepoints. This bound is
    # also used by the existing Stage-208 Unicode upper/lower runtime.
    expands = operation != 'substring'
    cap_label = prefix + '_capacity'
    ok_label = prefix + '_allocated'
    converted_label = prefix + '_converted'
    lines = [f'    mov eax, dword ptr [{source}_len]']
    if expands:
        lines.extend(['    mov ecx, eax', '    add eax, ecx', '    add eax, ecx'])
    lines.append('    add eax, 1')
    if is64:
        lines.append('    mov ecx, eax')
        if not shadow_space_reserved:
            lines.append('    sub rsp, 40')
        lines.append('    call __dbase_malloc')
        if not shadow_space_reserved:
            lines.append('    add rsp, 40')
    else:
        lines.extend(['    push eax', '    call __dbase_malloc', '    add esp, 4'])
    lines += [f'    test {"rax" if is64 else "eax"}, {"rax" if is64 else "eax"}',
              f'    jne {ok_label}']
    lines += (['    mov ecx, 8', '    call ExitProcess'] if is64
              else ['    push 8', '    call ExitProcess'])
    lines.extend([ok_label + ':',
                  f'    mov {"qword" if is64 else "dword"} ptr [{destination}_ptr], '
                  + ('rax' if is64 else 'eax'),
                  f'    mov eax, dword ptr [{source}_len]'])
    if expands:
        lines.extend(['    mov ecx, eax', '    add eax, ecx', '    add eax, ecx'])
    lines += ['    add eax, 1']
    if is64:
        lines.extend([
            f'    mov rcx, qword ptr [{destination}_ptr]',
            '    mov edx, eax',
            f'    mov r8, qword ptr [{source}_ptr]',
            f'    mov r9d, dword ptr [{source}_len]',
        ])
        if has_span:
            # Caller already has a 40-byte callback frame with aligned RSP;
            # keep stack alignment and provide a new 32-byte shadow area.
            lines += ['    sub rsp, 64',
                      f'    mov rax, {start}_num',
                      '    mov qword ptr [rsp+32], rax']
            if count is None:
                lines.append('    mov qword ptr [rsp+40], 0')
            else:
                lines += [f'    mov rax, {count}_num',
                          '    mov qword ptr [rsp+40], rax']
            lines += [f'    call {symbols[operation]}', '    add rsp, 64']
        elif shadow_space_reserved:
            lines.append(f'    call {symbols[operation]}')
        else:
            lines += ['    sub rsp, 40', f'    call {symbols[operation]}', '    add rsp, 40']
    else:
        if has_span:
            lines += [f'    push {count}_num' if count else '    push 0',
                      f'    push {start}_num']
        lines += [f'    push dword ptr [{source}_len]',
                  f'    push dword ptr [{source}_ptr]',
                  '    push eax',
                  f'    push dword ptr [{destination}_ptr]',
                  f'    call {symbols[operation]}',
                  f'    add esp, {24 if has_span else 16}']
    lines += ['    cmp eax, -1', f'    jne {converted_label}']
    lines += (['    mov ecx, 13', '    call ExitProcess'] if is64
              else ['    push 13', '    call ExitProcess'])
    lines += [converted_label + ':',
              f'    mov dword ptr [{destination}_len], eax',
              f'    mov dword ptr [{destination}_type], {int(string_type)}']
    return lines
