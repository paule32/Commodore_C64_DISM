# -*- coding: utf-8 -*-
"""Stage 673: call a shared Qt5 runtime DLL dispatch for static O1 output.

The pass accepts only the exact compiler-generated selector and *identical*
static literal/length pairs in the GUI and console branches.  It deliberately
leaves dynamic output intact: its arguments must be loaded after
DBaseQtSetDebugVisible, which can synchronously run GUI code.

Every original source line remains in place.  The dispatch is exported by libd64_qt5.dll.  No local routine is emitted.
All original source line numbers, data, VMT and selector labels are preserved.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_START = re.compile(r'cmp dword ptr \[__dbase_output_debug_override\], -1', re.I)
_TEXT = re.compile(r'__dbase_text_\d+', re.I)
_INT = re.compile(r'\d+')

@dataclass(frozen=True)
class OutputCompaction:
    assembly: str
    instructions_saved: int = 0
    blocks: int = 0


def _line(lines: list[str], index: int) -> str:
    if 0 <= index < len(lines):
        return lines[index].strip()
    return ''


def _capture(lines: list[str], index: int, regex: str) -> str | None:
    m = re.fullmatch(regex, _line(lines, index), re.I)
    return m.group(1) if m else None


def _check(lines: list[str], index: int, expected: str) -> bool:
    return _line(lines, index).casefold() == expected.casefold()


def _match_block(lines: list[str], i: int, bits: int):
    """Return (exclusive end, literal, size, labels) or None.

    Labels are captured rather than guessed, and the signature matches the
    *complete* branch structure emitted by _emit_runtime_output_choice.
    """
    if not _START.fullmatch(_line(lines, i)):
        return None
    ready = _capture(lines, i + 1, r'jne (__dbase_output_override_ready_\d+)')
    console = _capture(lines, i + 3, r'je (__dbase_output_console_\d+)')
    show = _capture(lines, i + 4, r'jmp (__dbase_output_show_done_\d+)')
    if not (ready and console and show):
        return None
    if not all((
        _check(lines, i + 2, 'cmp dword ptr [__dbase_output_format_screen], 0'),
        _check(lines, i + 5, ready + ':'),
        _check(lines, i + 6, 'cmp dword ptr [__dbase_output_debug_override], 0'),
        _check(lines, i + 7, 'je ' + console),
        _check(lines, i + 8, show + ':'),
        _check(lines, i + 9, 'cmp dword ptr [__dbase_output_debug_visible], 0'),
        _check(lines, i + 11, 'mov dword ptr [__dbase_output_debug_visible], 1'),
    )):
        return None
    visible = _capture(lines, i + 10, r'jne (__dbase_output_already_visible_\d+)')
    if not visible:
        return None
    if bits == 32:
        if not all((
            _check(lines, i + 12, 'push 1'),
            _check(lines, i + 13, 'call DBaseQtSetDebugVisible'),
            _check(lines, i + 14, 'add esp, 4'),
            _check(lines, i + 15, visible + ':'),
        )):
            return None
        first = 16
        length = _capture(lines, i + first, r'push (\d+)')
        literal = _capture(lines, i + first + 1, r'push (__dbase_text_\d+)')
        done = _capture(lines, i + first + 4, r'jmp (__dbase_output_done_\d+)')
        if not (length and literal and done):
            return None
        if not all((
            _check(lines, i + first + 2, 'call DBaseQtAppendDebug'),
            _check(lines, i + first + 3, 'add esp, 8'),
            _check(lines, i + first + 5, console + ':'),
            _check(lines, i + first + 6, 'push ' + length),
            _check(lines, i + first + 7, 'push ' + literal),
            _check(lines, i + first + 8, 'call DBaseConsoleWrite'),
            _check(lines, i + first + 9, 'add esp, 8'),
            _check(lines, i + first + 10, done + ':'),
        )):
            return None
        end = i + first + 11
    else:
        if not all((
            _check(lines, i + 12, 'mov ecx, 1'),
            _check(lines, i + 13, 'sub rsp, 40'),
            _check(lines, i + 14, 'call DBaseQtSetDebugVisible'),
            _check(lines, i + 15, 'add rsp, 40'),
            _check(lines, i + 16, visible + ':'),
        )):
            return None
        first = 17
        literal = _capture(lines, i + first, r'mov rcx, (__dbase_text_\d+)')
        length = _capture(lines, i + first + 1, r'mov edx, (\d+)')
        done = _capture(lines, i + first + 5, r'jmp (__dbase_output_done_\d+)')
        if not (length and literal and done):
            return None
        if not all((
            _check(lines, i + first + 2, 'sub rsp, 40'),
            _check(lines, i + first + 3, 'call DBaseQtAppendDebug'),
            _check(lines, i + first + 4, 'add rsp, 40'),
            _check(lines, i + first + 6, console + ':'),
            _check(lines, i + first + 7, 'mov rcx, ' + literal),
            _check(lines, i + first + 8, 'mov edx, ' + length),
            _check(lines, i + first + 9, 'sub rsp, 40'),
            _check(lines, i + first + 10, 'call DBaseConsoleWrite'),
            _check(lines, i + first + 11, 'add rsp, 40'),
            _check(lines, i + first + 12, done + ':'),
        )):
            return None
        end = i + first + 13
    return end, literal, length, (ready, console, show, visible, done)


def _instruction_count(lines: list[str]) -> int:
    return sum(bool(s.strip()) and not s.strip().startswith(';') and
               not s.strip().endswith(':') and not s.strip().lower().startswith('section ')
               for s in lines)


def compact_dbase_static_outputs(assembly: str, *, min_blocks: int = 3) -> OutputCompaction:
    """Centralize three or more identical-shape static output selectors.

    Unsupported output forms (dynamic strings, runtime number buffers, other
    debug writers) are left untouched.  No transformation occurs if a selector
    label is referenced from outside its original block.
    """
    if re.search(r'^\s*import\s+DBaseQtRuntimeWrite\s*,', assembly, re.M | re.I):
        return OutputCompaction(assembly)
    arch = re.search(r'^\s*bits\s+(32|64)\b', assembly, re.M | re.I)
    if arch is None:
        return OutputCompaction(assembly)
    bits = int(arch.group(1))
    lines = assembly.splitlines(keepends=True)
    section = None
    blocks = []
    i = 0
    while i < len(lines):
        raw = lines[i].strip()
        m = re.match(r'^section\s+([^\s;]+)', raw, re.I)
        if m:
            section = m.group(1).casefold()
        if section == '.text':
            candidate = _match_block(lines, i, bits)
            if candidate:
                end, literal, length, labels = candidate
                body = ''.join(lines[i:end])
                # A label can only disappear as an executable destination when
                # no other code jumps to that internal selector label.
                if all(len(re.findall(r'(?<![\w.$?@])' + re.escape(name) + r'(?![\w.$?@])',
                                      assembly, flags=re.I)) ==
                       len(re.findall(r'(?<![\w.$?@])' + re.escape(name) + r'(?![\w.$?@])',
                                      body, flags=re.I)) for name in labels):
                    blocks.append((i, end, literal, length))
                    i = end
                    continue
        i += 1
    if len(blocks) < min_blocks:
        return OutputCompaction(assembly)

    original = 0
    rewritten = 0
    for start, end, literal, length in blocks:
        original += _instruction_count(lines[start:end])
        if bits == 32:
            wrapper = [
                '    push __dbase_output_debug_visible',
                '    push dword ptr [__dbase_output_format_screen]',
                '    push dword ptr [__dbase_output_debug_override]',
                f'    push {length}',
                f'    push {literal}',
                '    call DBaseQtRuntimeWrite',
                '    add esp, 20',
            ]
        else:
            # Windows x64: RCX/RDX/R8/R9, fifth arg at rsp+32.
            # 40 bytes supplies shadow space + stack alignment.
            wrapper = [
                f'    mov rcx, {literal}',
                f'    mov edx, {length}',
                '    mov r8d, dword ptr [__dbase_output_debug_override]',
                '    mov r9d, dword ptr [__dbase_output_format_screen]',
                '    sub rsp, 40',
                '    mov rax, __dbase_output_debug_visible',
                '    mov qword ptr [rsp+32], rax',
                '    call DBaseQtRuntimeWrite',
                '    add rsp, 40',
            ]
        rewritten += len(wrapper)
        for j, text in enumerate(wrapper):
            ending = '\r\n' if lines[start+j].endswith('\r\n') else ('\n' if lines[start+j].endswith('\n') else '')
            lines[start+j] = text + ending
        for pos in range(start+len(wrapper), end):
            if re.fullmatch(r'[\w.$?@]+:', lines[pos].strip()):
                continue  # preserve label names and original line mapping
            ending = '\r\n' if lines[pos].endswith('\r\n') else ('\n' if lines[pos].endswith('\n') else '')
            lines[pos] = '    ; O1: zentraler Ausgabeaufruf' + ending

    saved = original - rewritten
    if saved <= 0:
        return OutputCompaction(assembly)
    # Preserve all original source line numbers by appending the import at
    # EOF. The internal assembler accepts import directives after .bss.
    newline = '\r\n' if '\r\n' in assembly else '\n'
    if not assembly.endswith(('\n', '\r')):
        lines.append(newline)
    result = (''.join(lines) +
              '; Stage 673 / O1: Ausgabe-Verteilung in libd64_qt5.dll' + newline +
              'import DBaseQtRuntimeWrite, "libd64_qt5.dll", "DBaseQtRuntimeWrite"' + newline)
    return OutputCompaction(result, saved, len(blocks))
