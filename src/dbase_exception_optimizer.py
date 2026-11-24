# -*- coding: utf-8 -*-
"""Stage 682: conservative O3 removal of unused dBASE exception scaffolding.

The state is .bss (it uses no PE raw-data bytes), not an initialized table.
Moving the state into a shared DLL would change ownership and concurrency
semantics.  Instead, drop the generated *unreachable* unhandled-exception
handler, then its entire unreferenced BSS slot group.

Never shrink a live packed value slot: `lea reg, [slot_type]` is permitted to
access the following num/ptr/len fields without naming them individually.
"""
from __future__ import annotations

import re

_LABEL = re.compile(r'^\s*([A-Za-z_.$?@][\w.$?@]*):(?:\s*;.*)?$')
_DEF = re.compile(r'^\s*(__dbase_exception_(?:id|code|objects_head|(?:message|class|object|cstr)_(?:type|num|ptr|len))):\s*$', re.I)
_SECTION = re.compile(r'^\s*section\s+([\w.]+)', re.I)
_RESERVE = re.compile(r'^\s*res(?:b|w|d|q)\s+\d+\s*(?:;.*)?$', re.I)
_UNHANDLED = re.compile(r'^\s*(__dbase_exception_unhandled_\d+):\s*$', re.I)
_CONTINUE = re.compile(r'^\s*__dbase_exception_continue_\d+:\s*$', re.I)


def _mentioned(lines: list[str], symbol: str, *, skip: set[int] = frozenset()) -> bool:
    pattern = re.compile(r'(?<![\w.$?@])' + re.escape(symbol) + r'(?![\w.$?@])', re.I)
    return any(pattern.search(line.split(';', 1)[0]) for i, line in enumerate(lines)
               if i not in skip)


def compact_unreferenced_exception_state(assembly: str) -> tuple[str, int]:
    """Prune unreachable generated exception handling and unused .bss.

    The pass acts only on recognizable compiler-emitted handler sections, and
    leaves any live exception-state group intact. Safe to apply repeatedly.
    """
    lines = assembly.splitlines(keepends=True)
    removed = 0
    in_text = False
    i = 0
    while i < len(lines):
        section = _SECTION.match(lines[i])
        if section:
            in_text = section.group(1).casefold() == '.text'
        start = _UNHANDLED.match(lines[i]) if in_text else None
        if not start:
            i += 1
            continue
        end = next((j for j in range(i + 1, len(lines))
                    if _CONTINUE.match(lines[j])
                    or _SECTION.match(lines[j])), None)
        if end is None or not _CONTINUE.match(lines[end]):
            i += 1
            continue
        # Recognize exactly the fallback emitted by the dBASE generator.
        block = ''.join(lines[i:end])
        if ('__dbase_exception_class' not in block or
            '__dbase_exception_message' not in block or
            'DBaseQtProcessEvents' not in block):
            i += 1
            continue
        internal_labels = [match.group(1) for item in lines[i:end]
                           if (match := _LABEL.match(item))]
        indices = set(range(i, end))
        if any(_mentioned(lines, name, skip=indices) for name in internal_labels):
            i += 1
            continue
        # Keep the following __dbase_exception_continue_N label and everything
        # after it; earlier branches may still target that continuation.
        # After deletion the branch over the handler targets the immediately
        # following continuation. Remove it now rather than relying on a
        # second O1 run (O3 must be idempotent).
        if i > 0 and re.fullmatch(
                r'\s*jmp\s+' + re.escape(lines[end].split(':', 1)[0].strip()) +
                r'\s*(?:;.*)?', lines[i - 1].rstrip('\r\n'), flags=re.I):
            ending = '\r\n' if lines[i - 1].endswith('\r\n') else '\n'
            lines[i - 1] = '    ; O3: unreachable exception handler skipped' + ending
            removed += 1
        del lines[i:end]
        removed += end - i

    definitions = [(i, match.group(1)) for i, item in enumerate(lines)
                   if (match := _DEF.match(item))]
    if not definitions:
        return ''.join(lines), removed

    # A pointer to any member of a packed slot can be used to access the
    # others by offset, therefore prune *only* if all exception state is dead.
    definition_lines = {i for i, _ in definitions}
    if any(_mentioned(lines, name, skip=definition_lines) for _, name in definitions):
        return ''.join(lines), removed
    # Require the exact reserve directive after every exception definition;
    # unknown storage syntax must not be rewritten.
    if any(i + 1 >= len(lines) or not _RESERVE.match(lines[i + 1])
           for i, _ in definitions):
        return ''.join(lines), removed
    drop = {j for i, _ in definitions for j in (i, i+1)}
    removed += len(drop)
    return ''.join(item for i, item in enumerate(lines) if i not in drop), removed
