# -*- coding: utf-8 -*-
"""Stage 448: shared DLL character-case predicates for CP1252 and UTF-8.

ABI: (const char *ptr, unsigned byte_length) -> EAX=0/1.
PE32 uses caller-cleaned cdecl; PE32+ follows Windows x64 (RCX, EDX).
Only the original stage-326 one- or two-byte Unicode subset is accepted.
"""
from .char_case import _ranges, _contiguous_ranges, _cp1252_is_case

CASE_EXPORTS = (
    'DBaseCharIsLowerCP1252', 'DBaseCharIsUpperCP1252',
    'DBaseCharIsLowerUtf8', 'DBaseCharIsUpperUtf8',
)


def export_name(*, upper: bool, encoding: str) -> str:
    if encoding not in ('cp1252', 'utf8'):
        raise ValueError(encoding)
    return 'DBaseCharIs' + ('Upper' if upper else 'Lower') + ('Utf8' if encoding == 'utf8' else 'CP1252')


def emit_predicate(name: str, *, upper: bool, encoding: str, is64: bool) -> list[str]:
    """Generate a leaf DLL function; no global scratch variables or x87 use."""
    if encoding not in ('cp1252', 'utf8'):
        raise ValueError(encoding)
    ptr = 'rcx' if is64 else 'edx'
    length = 'edx' if is64 else 'dword ptr [esp+8]'
    code = [f'{name}:']
    if not is64:
        code += ['    mov edx, dword ptr [esp+4]']
    code += [f'    test {ptr}, {ptr}', f'    je {name}_false']
    if encoding == 'cp1252':
        code += [f'    cmp {length}, 1', f'    jne {name}_false',
                 f'    movzx eax, byte ptr [{ptr}]']
        ranges = _ranges(upper)
    else:
        one = f'{name}_one'
        ready = f'{name}_ready'
        second_register = 'edx' if is64 else 'ecx'
        code += [
            f'    cmp {length}, 1', f'    je {one}',
            f'    cmp {length}, 2', f'    jne {name}_false',
            f'    movzx eax, byte ptr [{ptr}]',
            '    cmp eax, 194', f'    jb {name}_false',
            '    cmp eax, 223', f'    ja {name}_false',
            '    and eax, 31', '    shl eax, 6',
            f'    movzx {second_register}, byte ptr [{ptr}+1]',
            f'    cmp {second_register}, 128', f'    jb {name}_false',
            f'    cmp {second_register}, 191', f'    ja {name}_false',
            f'    and {second_register}, 63',
            f'    or eax, {second_register}', f'    jmp {ready}',
            f'{one}:', f'    movzx eax, byte ptr [{ptr}]',
            '    cmp eax, 127', f'    ja {name}_false',
            f'{ready}:',
        ]
        case_values = sorted({ord(bytes((b,)).decode('cp1252'))
                              for b in range(256) if _cp1252_is_case(b, upper)})
        ranges = _contiguous_ranges(case_values)
    for i, (lo, hi) in enumerate(ranges):
        if lo == hi:
            code += [f'    cmp eax, {lo}', f'    je {name}_true']
        else:
            next_label = f'{name}_next_{i}'
            code += [f'    cmp eax, {lo}', f'    jb {next_label}',
                     f'    cmp eax, {hi}', f'    jbe {name}_true', f'{next_label}:']
    code += [f'{name}_false:', '    xor eax, eax', '    ret',
             f'{name}_true:', '    mov eax, 1', '    ret']
    return code
