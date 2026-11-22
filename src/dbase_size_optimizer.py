# -*- coding: utf-8 -*-
"""Stage 672: O0/O1 size optimizer for compiler-generated dBASE Intel ASM.

O0 is a strict identity transform.  O1 only rewrites provably equivalent
control-flow patterns inside the .text section.  Every source line is retained:
removed instructions become comments so diagnostics/source maps remain aligned.
No global labels, imports, sections, data directives, exception state, or ABI
instructions are removed or relocated.  Register self-moves are intentionally
untouched: in PE32+, ``mov eax, eax`` clears the high 32 bits of RAX.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

_O1 = 'O1'
_LEVELS = frozenset(('O0', 'O1'))
_LABEL = re.compile(r'^\s*([A-Za-z_.$?@][\w.$?@]*):\s*(?:;.*)?$', re.I)
_JMP = re.compile(r'^([ \t]*)jmp[ \t]+([A-Za-z_.$?@][\w.$?@]*)\s*(?:;.*)?$', re.I)
_JCC = re.compile(r'^([ \t]*)(j[a-z]+)[ \t]+([A-Za-z_.$?@][\w.$?@]*)\s*(?:;.*)?$', re.I)
_SECTION = re.compile(r'^\s*section\s+([^\s;]+)', re.I)
_INVERSE = {
    'je':'jne', 'jne':'je', 'jz':'jnz', 'jnz':'jz',
    'ja':'jbe', 'jbe':'ja', 'jae':'jb', 'jb':'jae',
    'jg':'jle', 'jle':'jg', 'jge':'jl', 'jl':'jge',
    'js':'jns', 'jns':'js', 'jp':'jnp', 'jnp':'jp',
    'jo':'jno', 'jno':'jo', 'jc':'jnc', 'jnc':'jc',
}


def normalize_dbase_optimization_level(value: object) -> str:
    result = str(value or 'O0').strip().upper()
    return result if result in _LEVELS else 'O0'


@dataclass(frozen=True)
class DBaseSizeOptimizationResult:
    assembly: str
    level: str
    replacements: int = 0


def optimize_dbase_size_assembly(assembly: str, *, level: str = 'O0') -> DBaseSizeOptimizationResult:
    """Optimize only safe generated control-flow, retaining exact line numbers.

    Conditions are never moved across instructions, and the label namespace is
    unchanged.  The result is idempotent.  ``replacements`` counts eliminated
    machine instructions, not guessed byte sizes (branch encodings vary).
    """
    level = normalize_dbase_optimization_level(level)
    if level != _O1:
        return DBaseSizeOptimizationResult(assembly, level)
    lines = assembly.splitlines(keepends=True)
    text_section = False
    changed = 0

    def parts(i: int):
        return lines[i].rstrip('\r\n')

    def comment(i: int) -> str:
        ending = lines[i][len(parts(i)):]
        return '    ; O1: entfallene Instruktion' + ending

    i = 0
    while i < len(lines):
        section = _SECTION.match(parts(i))
        if section:
            text_section = section.group(1).lower() == '.text'
        if not text_section:
            i += 1
            continue

        line = parts(i)
        jump = _JMP.fullmatch(line)
        if jump and i + 1 < len(lines):
            following = _LABEL.fullmatch(parts(i + 1))
            if following and jump.group(2).casefold() == following.group(1).casefold():
                lines[i] = comment(i)
                changed += 1
                i += 1
                continue
            # Consecutive unconditional jumps: second is unreachable, provided
            # there are no labels/preprocessor directives between them.
            next_jump = _JMP.fullmatch(parts(i + 1))
            if next_jump:
                lines[i + 1] = comment(i + 1)
                changed += 1
                i += 2
                continue

        branch = _JCC.fullmatch(line)
        if branch and i + 2 < len(lines):
            fallback = _JMP.fullmatch(parts(i + 1))
            label = _LABEL.fullmatch(parts(i + 2))
            inverse = _INVERSE.get(branch.group(2).lower())
            if (fallback and label and inverse and
                    branch.group(3).casefold() == label.group(1).casefold()):
                ending = lines[i][len(line):]
                lines[i] = f'{branch.group(1)}{inverse} {fallback.group(2)}' + ending
                lines[i + 1] = comment(i + 1)
                changed += 1
                i += 3
                continue

        i += 1

    # Stage 672: static runtime text output calls share one dispatch body.
    # Called only in O1, after the original control-flow peepholes.
    from dbase_output_compactor import compact_dbase_static_outputs
    compacted = compact_dbase_static_outputs(''.join(lines))
    return DBaseSizeOptimizationResult(
        compacted.assembly, level, changed + compacted.instructions_saved)

