# -*- coding: utf-8 -*-
"""WFM Stage 451: conservative label-oriented control-flow simplification.

Only generated __dbase_wfm_flow_ labels are transformed.  Explicit labels in
handwritten assembly and data are intentionally left untouched.
"""
from __future__ import annotations

import re

_INVERT = {
    'je':'jne','jne':'je','jz':'jnz','jnz':'jz',
    'ja':'jbe','jbe':'ja','jae':'jb','jb':'jae',
    'jg':'jle','jle':'jg','jge':'jl','jl':'jge',
    'js':'jns','jns':'js','jp':'jnp','jnp':'jp',
}
_CONDITION = re.compile(r'^(\s*)(j[a-z]+)\s+(__dbase_wfm_flow_\w+)\s*$', re.I)
_JUMP = re.compile(r'^\s*jmp\s+(__dbase_wfm_flow_\w+)\s*$', re.I)
_LABEL = re.compile(r'^(__dbase_wfm_flow_\w+):\s*$', re.I)


def optimize_wfm_branches(source: str) -> str:
    """Eliminate branch-to-next and branch-over-jump, preserving semantics.

    Do not optimize across intervening comments or instructions: condition
    flags and externally reachable labels must be preserved exactly.
    """
    lines = source.splitlines(keepends=True)
    for _ in range(4):
        out = []
        changed = False
        i = 0
        while i < len(lines):
            a = _CONDITION.fullmatch(lines[i].strip('\r\n'))
            if a and i + 2 < len(lines):
                b = _JUMP.fullmatch(lines[i+1].strip('\r\n'))
                c = _LABEL.fullmatch(lines[i+2].strip('\r\n'))
                opposite = _INVERT.get(a.group(2).lower())
                if b and c and opposite and a.group(3).casefold() == c.group(1).casefold():
                    newline = '\r\n' if lines[i].endswith('\r\n') else '\n'
                    out.append(f'{a.group(1)}{opposite} {b.group(1)}{newline}')
                    out.append(lines[i+2])
                    changed = True
                    i += 3
                    continue
            # A jump directly to the next instruction is redundant.
            b = _JUMP.fullmatch(lines[i].strip('\r\n'))
            if b and i+1 < len(lines):
                c = _LABEL.fullmatch(lines[i+1].strip('\r\n'))
                if c and b.group(1).casefold() == c.group(1).casefold():
                    changed = True
                    i += 1
                    continue
            out.append(lines[i]);i += 1
        lines = out
        if not changed:break
    return ''.join(lines)
