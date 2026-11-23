# -*- coding: utf-8 -*-
"""Stage 674 O2: static-string descriptors and one-argument Qt5 output calls.

The Stage-673 O1 pattern is recognized exactly, including its platform-specific
calling convention. We preserve original literal labels (other features can
still use them as raw strings) and append separate, naturally aligned metadata
records. Original O1 call lines are replaced in place, not deleted.

Output state belongs to the EXE: once after successful Qt initialization the
DLL is bound to the three *existing* state variables. Those variable values
can change at any time (SET FORMAT / SET DEBUG); no shadow copy is made.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

@dataclass(frozen=True)
class O2StaticResult:
    assembly: str
    instructions_saved: int = 0
    calls: int = 0


def _clean(s: str) -> str:
    return s.strip().casefold()


def compact_dbase_static_string_calls(assembly: str) -> O2StaticResult:
    """Replace only verified Stage-673 static wrappers; safe on reruns."""
    if re.search(r'^\s*import\s+DBaseQtRuntimeWriteText\s*,', assembly, re.I | re.M):
        return O2StaticResult(assembly)
    match = re.search(r'^\s*bits\s+(32|64)\b', assembly, re.I | re.M)
    if not match:
        return O2StaticResult(assembly)
    bits = int(match.group(1))
    lines = assembly.splitlines(keepends=True)
    content = [s.strip() for s in lines]
    uses: dict[str, int] = {}
    calls = 0
    saved = 0

    def replace(i: int, end: int, new_lines: list[str]) -> None:
        for k in range(i, end):
            original = lines[k]
            nl = '\r\n' if original.endswith('\r\n') else '\n' if original.endswith('\n') else ''
            lines[k] = (new_lines[k-i] if k-i < len(new_lines) else '    ; O2: statische Ausgabe') + nl

    i = 0
    while i < len(lines):
        if bits == 32 and i + 6 < len(lines) and _clean(content[i]) == 'push __dbase_output_debug_visible':
            chunk = content[i:i+7]
            valid = (len(chunk) == 7 and
                _clean(chunk[1]) == 'push dword ptr [__dbase_output_format_screen]' and
                _clean(chunk[2]) == 'push dword ptr [__dbase_output_debug_override]' and
                _clean(chunk[5]) == 'call dbaseqtruntimewrite' and
                _clean(chunk[6]) == 'add esp, 20')
            length = re.fullmatch(r'push\s+(\d+)', chunk[3], re.I)
            literal = re.fullmatch(r'push\s+(__dbase_text_\d+)', chunk[4], re.I)
            if valid and length and literal:
                label = literal.group(1)
                if re.search(r'^\s*' + re.escape(label) + r':\s*$', assembly, re.I | re.M):
                    value = int(length.group(1))
                    if label.casefold() not in uses:
                        uses[label.casefold()] = value
                    if uses[label.casefold()] == value:
                        desc = '__dbase_o2_' + label.lstrip('_')
                        replace(i, i+7, [f'    push {desc}',
                                         '    call DBaseQtRuntimeWriteText', '    add esp, 4'])
                        calls += 1
                        saved += 4
                        i += 7
                        continue
        if bits == 64 and i + 8 < len(lines):
            chunk = content[i:i+9]
            valid = (len(chunk) == 9 and
                     _clean(chunk[2]) == 'mov r8d, dword ptr [__dbase_output_debug_override]' and
                     _clean(chunk[3]) == 'mov r9d, dword ptr [__dbase_output_format_screen]' and
                     _clean(chunk[4]) == 'sub rsp, 40' and
                     _clean(chunk[5]) == 'mov rax, __dbase_output_debug_visible' and
                     _clean(chunk[6]) == 'mov qword ptr [rsp+32], rax' and
                     _clean(chunk[7]) == 'call dbaseqtruntimewrite' and
                     _clean(chunk[8]) == 'add rsp, 40')
            literal = re.fullmatch(r'mov\s+rcx,\s*(__dbase_text_\d+)', chunk[0], re.I)
            length = re.fullmatch(r'mov\s+edx,\s*(\d+)', chunk[1], re.I)
            if valid and literal and length:
                label = literal.group(1)
                if re.search(r'^\s*' + re.escape(label) + r':\s*$', assembly, re.I | re.M):
                    value = int(length.group(1))
                    if label.casefold() not in uses:
                        uses[label.casefold()] = value
                    if uses[label.casefold()] == value:
                        desc = '__dbase_o2_' + label.lstrip('_')
                        replace(i, i+9, [f'    mov rcx, {desc}',
                                         '    sub rsp, 40',
                                         '    call DBaseQtRuntimeWriteText',
                                         '    add rsp, 40'])
                        calls += 1
                        saved += 5
                        i += 9
                        continue
        i += 1

    # A valid EXE module must register the state even if all static output
    # calls happen in separately compiled Programme objects linked later.
    source = ''.join(lines)
    has_startup = re.search(r'^\s*__dbase_qt_init_ok_\d+:\s*$', source, re.I | re.M) is not None
    has_cleanup = re.search(r'^\s*__dbase_program_cleanup_\d+:\s*$', source, re.I | re.M) is not None
    if not (calls or (has_startup and has_cleanup)):
        return O2StaticResult(assembly)
    if has_startup != has_cleanup:
        # Do not construct a half-initialized binding in malformed ASM.
        return O2StaticResult(assembly)
    newline = '\r\n' if '\r\n' in assembly else '\n'
    source = ''.join(lines)
    if has_startup:
        if bits == 32:
            bind = ['    push __dbase_o2_output_state',
                    '    call DBaseQtBindOutputState', '    add esp, 4']
            unbind = ['    push 0', '    call DBaseQtBindOutputState', '    add esp, 4']
        else:
            bind = ['    mov rcx, __dbase_o2_output_state',
                    '    sub rsp, 40', '    call DBaseQtBindOutputState', '    add rsp, 40']
            unbind = ['    xor ecx, ecx', '    sub rsp, 40',
                      '    call DBaseQtBindOutputState', '    add rsp, 40']
        source = re.sub(r'(?im)^(\s*__dbase_qt_init_ok_\d+:\s*\r?\n)',
                        lambda m: m.group(1) + newline.join(bind) + newline, source, count=1)
        source = re.sub(r'(?im)^(\s*__dbase_program_cleanup_\d+:\s*\r?\n)',
                        lambda m: m.group(1) + newline.join(unbind) + newline, source, count=1)

    # Only suppress Stage-673 import when all uses of it disappeared.
    if not re.search(r'^\s*call\s+DBaseQtRuntimeWrite\s*$', source, re.I | re.M):
        source = re.sub(r'^\s*import DBaseQtRuntimeWrite, "libd64_qt5.dll", "DBaseQtRuntimeWrite"\s*$',
                        '; O2: ersetzt durch DBaseQtRuntimeWriteText', source,
                        flags=re.I | re.M)
    additions = ['; Stage 674 / O2: linked static text descriptors', 'section .data']
    for literal, length in uses.items():
        descriptor = '__dbase_o2_' + literal.lstrip('_')
        additions += [f'    align {8 if bits == 64 else 4}', f'{descriptor}:',
                      f'    dd {length}']
        if bits == 64:
            additions.append('    dd 0')
        additions.append(f'    {"dq" if bits == 64 else "dd"} {literal}')
    if has_startup:
        additions += [f'    align {8 if bits == 64 else 4}', '__dbase_o2_output_state:']
        for label in ('__dbase_output_debug_override', '__dbase_output_format_screen',
                      '__dbase_output_debug_visible'):
            additions.append(f'    {"dq" if bits == 64 else "dd"} {label}')
    if calls:
        additions.append('import DBaseQtRuntimeWriteText, "libd64_qt5.dll", "DBaseQtRuntimeWriteText"')
    if has_startup:
        additions.append('import DBaseQtBindOutputState, "libd64_qt5.dll", "DBaseQtBindOutputState"')
    if not source.endswith(('\n', '\r')):
        source += newline
    source += newline.join(additions) + newline
    return O2StaticResult(source, saved + (2 if has_startup else 0), calls)
