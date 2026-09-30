"""Stage 208/209: DLL-backed Unicode case conversion with sharp-s exception.

Generated programs no longer embed the Unicode lookup table. The immutable
packed tables live in libd64_qt5.dll; !() calls DBaseUpperBuffer.
"""
from functools import lru_cache


def upper_string(value: str) -> str:
    return ''.join(c if c == 'ß' else c.upper() for c in value)


def lower_string(value: str) -> str:
    return value.lower()


@lru_cache(maxsize=1)
def _mapping_rows():
    rows = []
    for cp in range(128, 0x110000):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        c = chr(cp)
        upper = upper_string(c)
        if upper != c:
            source, result = c.encode('utf-8'), upper.encode('utf-8')
            assert len(result) <= 12
            rows.append((int.from_bytes(source, 'little'), result))
    return tuple(rows)


@lru_cache(maxsize=1)
def _lower_mapping_rows():
    rows = []
    for cp in range(128, 0x110000):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        c = chr(cp)
        lower = lower_string(c)
        if lower != c:
            source, result = c.encode('utf-8'), lower.encode('utf-8')
            rows.append((int.from_bytes(source, 'little'), result))
    return tuple(rows)


def emit_upper_copy(source, destination, is64, prefix, string_type, *,
                    table_label=None, include_table=False,
                    shadow_space_reserved=False):
    """Allocate an independent result string and uppercase it in the DLL."""
    ptr, acc = ('qword', 'rax') if is64 else ('dword', 'eax')
    L = lambda name: prefix + '_' + name
    lines = [
        f'    mov eax, dword ptr [{source}_len]',
        '    mov ecx, eax',
        '    add eax, ecx',
        '    add eax, ecx',
        '    add eax, 1',
    ]
    if is64:
        lines += ['    mov ecx, eax']
        if shadow_space_reserved:
            lines += ['    call __dbase_malloc']
        else:
            lines += [
                '    sub rsp, 40',
                '    call __dbase_malloc',
                '    add rsp, 40',
            ]
    else:
        lines += ['    push eax', '    call __dbase_malloc', '    add esp, 4']
    lines += [
        f'    test {acc}, {acc}',
        f'    jne {L("allocated")}',
    ]
    if is64:
        lines += ['    mov ecx, 8']
        if shadow_space_reserved:
            lines += ['    call ExitProcess']
        else:
            lines += ['    sub rsp, 40', '    call ExitProcess']
    else:
        lines += ['    push 8', '    call ExitProcess']
    lines += [
        L('allocated') + ':',
        f'    mov {ptr} ptr [{destination}_ptr], {acc}',
    ]
    if is64:
        lines += [
            f'    mov rcx, qword ptr [{destination}_ptr]',
            f'    mov edx, dword ptr [{source}_len]',
            '    mov eax, edx',
            '    add edx, eax',
            '    add edx, eax',
            '    add edx, 1',
            f'    mov r8, qword ptr [{source}_ptr]',
            f'    mov r9d, dword ptr [{source}_len]',
        ]
        if shadow_space_reserved:
            lines += ['    call __dbase_upper_buffer']
        else:
            lines += [
                '    sub rsp, 40',
                '    call __dbase_upper_buffer',
                '    add rsp, 40',
            ]
    else:
        lines += [
            f'    mov ecx, dword ptr [{source}_len]',
            '    mov edx, ecx',
            '    add edx, ecx',
            '    add edx, ecx',
            '    add edx, 1',
            '    push ecx',
            f'    push dword ptr [{source}_ptr]',
            '    push edx',
            f'    push dword ptr [{destination}_ptr]',
            '    call __dbase_upper_buffer',
            '    add esp, 16',
        ]
    lines += ['    cmp eax, -1', f'    jne {L("converted")}']
    if is64:
        lines += ['    mov ecx, 13']
        if shadow_space_reserved:
            lines += ['    call ExitProcess']
        else:
            lines += ['    sub rsp, 40', '    call ExitProcess']
    else:
        lines += ['    push 13', '    call ExitProcess']
    lines += [
        L('converted') + ':',
        f'    mov dword ptr [{destination}_len], eax',
        f'    mov dword ptr [{destination}_type], {string_type}',
    ]
    return lines


def emit_upper_table(label="__dbase_upper_table"):
    """Packed rows: UTF-8 key (DWORD), output length (BYTE), exact output bytes.

    No padding; a zero DWORD terminates the table. The compiler emits this only
    once per assembly unit and only if a runtime uppercase operation needs it.
    """
    lines = ['.section .data', label + ':']
    for key, value in _mapping_rows():
        lines += [f'    dd {key}',
                  '    db ' + ', '.join(map(str, bytes([len(value)]) + value))]
    return lines + ['    dd 0', '.section .text']
