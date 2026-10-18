"""Stage 441: native dBASE LEN/LTRIM/RTRIM/TRIM builtins.

A value slot has a byte pointer and a byte length (the dBASE output
codepage is CP1252).  The generated PE32/PE32+ code works with that length,
never scans beyond it, and never modifies the input string in place.
"""
from __future__ import annotations

from decimal import Decimal

TRIM_NAMES = frozenset({'ltrim', 'rtrim', 'trim'})
# LTRIM historically strips plain spaces; RTRIM and TRIM additionally strip
# the explicit control/blank characters requested by the dBASE dialect.
_LEFT_SPACE = ' '
_ALL_SPACE = ' \t\n\b\r'


def string_length(value: str) -> Decimal:
    """Length measured in characters of the CP1252-backed dBASE string."""
    return Decimal(len(str(value).encode('cp1252', errors='replace')))


def trim_string(name: str, value: str) -> str:
    """Pure preview/folding implementation, in lockstep with native code."""
    name = name.casefold()
    text = str(value)
    if name == 'ltrim':
        return text.lstrip(_LEFT_SPACE)
    if name == 'rtrim':
        return text.rstrip(_ALL_SPACE)
    if name == 'trim':
        return text.strip(_ALL_SPACE)
    raise ValueError('unknown string trim operation: ' + name)


def emit_trim_operation(source: str, destination: str, *, kind: str,
                        is64: bool, prefix: str, string_type: int,
                        shadow_space_reserved: bool = False) -> list[str]:
    kind = kind.casefold()
    if kind not in TRIM_NAMES:
        raise ValueError(kind)
    L = lambda part: f'{prefix}_{part}'
    ptr = 'qword' if is64 else 'dword'
    acc = 'rax' if is64 else 'eax'
    si = 'rsi' if is64 else 'esi'
    di = 'rdi' if is64 else 'edi'

    lines = [f'    mov eax, dword ptr [{source}_len]', '    inc eax']
    if is64:
        lines += ['    mov ecx, eax']
        if not shadow_space_reserved:
            lines.append('    sub rsp, 40')
        lines.append('    call __dbase_malloc')
        if not shadow_space_reserved:
            lines.append('    add rsp, 40')
    else:
        lines += ['    push eax', '    call __dbase_malloc', '    add esp, 4']
    lines += [f'    test {acc}, {acc}', f'    jne {L("allocated")}']
    if is64:
        lines += ['    mov ecx, 8', '    sub rsp, 40', '    call ExitProcess']
    else:
        lines += ['    push 8', '    call ExitProcess']
    lines += [L('allocated') + ':', f'    mov {ptr} ptr [{destination}_ptr], {acc}',
              f'    push {si}', f'    push {di}',
              f'    mov {si}, {ptr} ptr [{source}_ptr]',
              f'    mov {di}, {si}', f'    mov eax, dword ptr [{source}_len]',
              f'    add {di}, {acc}']

    def whitespace_jump(loop_label: str, stop_label: str, *, extended: bool) -> list[str]:
        """AL holds character, decide whether to continue trimming."""
        result = ['    cmp al, 32', f'    je {loop_label}']
        if extended:
            for byte in (9, 10, 8, 13):
                result += [f'    cmp al, {byte}', f'    je {loop_label}']
        result += [f'    jmp {stop_label}']
        return result

    if kind in ('ltrim', 'trim'):
        lines += [L('left_loop') + ':', f'    cmp {si}, {di}',
                  f'    jae {L("left_done")}',
                  f'    mov al, byte ptr [{si}]']
        lines += whitespace_jump(L('left_advance'), L('left_done'),
                                 extended=(kind == 'trim'))
        lines += [L('left_advance') + ':', f'    inc {si}',
                  f'    jmp {L("left_loop")}', L('left_done') + ':']

    if kind in ('rtrim', 'trim'):
        lines += [L('right_loop') + ':', f'    cmp {di}, {si}',
                  f'    jbe {L("right_done")}',
                  f'    mov al, byte ptr [{di}-1]']
        lines += whitespace_jump(L('right_retreat'), L('right_done'), extended=True)
        lines += [L('right_retreat') + ':', f'    dec {di}',
                  f'    jmp {L("right_loop")}', L('right_done') + ':']

    lines += [f'    sub {di}, {si}',  # RDI/EDI now length
              f'    mov dword ptr [{destination}_len], edi',
              f'    mov dword ptr [{destination}_type], {int(string_type)}',
              '    mov ecx, edi',
              f'    mov {di}, {ptr} ptr [{destination}_ptr]',
              L('copy_loop') + ':',
              '    test ecx, ecx',
              f'    je {L("copy_done")}',
              f'    movzx eax, byte ptr [{si}]',
              f'    mov byte ptr [{di}], al',
              f'    inc {si}',
              f'    inc {di}',
              '    dec ecx',
              f'    jmp {L("copy_loop")}',
              L('copy_done') + ':',
              f'    mov byte ptr [{di}], 0',
              f'    pop {di}', f'    pop {si}']
    return lines
