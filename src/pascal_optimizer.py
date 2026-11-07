"""Stage 537: conservative architecture-independent PE32/PE64 assembler passes.

Keep syntax valid for the project's integrated assemblers. Never rewrite a
stack cookie, an import, a call, or a memory operation through an unknown
pointer. O0 is byte-for-byte unchanged; source maps are remapped on deletion.
"""
from __future__ import annotations
import re
from typing import Dict, Iterable, Tuple

VALID_LEVELS = (0, 1, 2, 3)

def normalize_optimization_level(value) -> int:
    try:
        if isinstance(value, str):
            value = value.strip().upper().removeprefix('O')
        number = int(value)
    except (TypeError, ValueError):
        number = 0
    return number if number in VALID_LEVELS else 0


def _instruction(text):
    return text.strip().lower()


def optimize_assembler(lines: Iterable[str], source_map: Dict[int, int],
                       level: int) -> Tuple[list[str], Dict[int, int]]:
    level = normalize_optimization_level(level)
    original = list(lines)
    if not level:
        return original, dict(source_map)
    # Immutable input indices are attached to every retained instruction.
    data = [(line, i + 1) for i, line in enumerate(original)]
    def code_indices(items):
        in_code = True
        enabled = []
        for line, _ in items:
            stripped = line.strip().lower()
            if stripped.startswith('section '):
                in_code = stripped.split(None, 1)[1].split()[0] in ('.text', '.code')
            enabled.append(in_code)
        return enabled

    # Safe Peephole: PUSH EAX / MOV ECX,... / POP EAX is a no-op around
    # an instruction that does not use ESP, push/pop flags or modify EAX.
    for _pass in range(3):
        flags = code_indices(data)
        changed = False
        new = []
        i = 0
        while i < len(data):
            text, index = data[i]
            op = _instruction(text)
            if (i + 2 < len(data) and flags[i:i+3] == [True]*3
                    and op in ('push eax', 'push rax')
                    and re.fullmatch(r'mov (?:ecx|r11), (?!.*\b(?:esp|rsp)\b).+',
                                     _instruction(data[i+1][0]))
                    and _instruction(data[i+2][0]) == ('pop eax' if op == 'push eax' else 'pop rax')):
                new.append(data[i+1]); i += 3; changed = True; continue
            # Redundant identity MOV has no architectural effect.
            match = re.fullmatch(r'mov ([a-z][a-z0-9]*), \1', op)
            if flags[i] and match:
                i += 1; changed = True; continue
            # A RET terminates its basic block; a following unconditional JMP
            # is dead if it lies before the next label/section/directive.
            if (i + 1 < len(data) and flags[i]
                    and re.fullmatch(r'ret(?: \d+)?', op)
                    and _instruction(data[i+1][0]).startswith('jmp ')):
                new.append(data[i]); i += 2; changed = True; continue
            new.append(data[i]); i += 1
        data = new
        if not changed:
            break

    if level >= 2:
        # Consecutive operations that explicitly copy an immediate into a
        # volatile register can use the immediate directly, preserving EAX.
        flags = code_indices(data)
        new = []
        i = 0
        while i < len(data):
            if i + 1 < len(data) and flags[i] and flags[i+1]:
                first = re.fullmatch(r'mov eax, (-?(?:0x[0-9a-f]+|\d+))',
                                     _instruction(data[i][0]))
                if first and _instruction(data[i+1][0]) == 'mov edx, eax':
                    new.extend([data[i], (f'    mov edx, {first.group(1)}', data[i+1][1])])
                    i += 2; continue
            new.append(data[i]); i += 1
        data = new
    if level >= 3:
        # Local jump threading: redirect a jump to a one-instruction jump block;
        # labels remain so externally reachable entry points are unchanged.
        redirects = {}
        flags = code_indices(data)
        for i in range(len(data)-1):
            name = _instruction(data[i][0]); next_op = _instruction(data[i+1][0])
            if flags[i] and flags[i+1] and re.fullmatch(r'__pas[_a-z0-9]*:', name) \
                    and re.fullmatch(r'jmp __pas[_a-z0-9]+', next_op):
                redirects[name[:-1]] = next_op.split()[-1]
        new = []
        for text, origin in data:
            op = _instruction(text)
            match = re.fullmatch(r'(jmp|je|jne|jz|jnz|jl|jle|jg|jge|ja|jae|jb|jbe) (__pas[_a-z0-9]+)', op)
            if match:
                destination = match.group(2)
                visited = set()
                while destination in redirects and destination not in visited:
                    visited.add(destination)
                    destination = redirects[destination]
                if destination not in visited and destination != match.group(2):
                    text = f'    {match.group(1)} {destination}'
            new.append((text, origin))
        data = new
        # Remove unconditional jump directly into immediately following label.
        new = []
        for i, item in enumerate(data):
            if (i+1 < len(data) and re.fullmatch(r'jmp [a-z_][\w]*', _instruction(item[0]))
                    and _instruction(data[i+1][0]) == _instruction(item[0]).split()[1]+':'):
                continue
            new.append(item)
        data = new
    output_lines = [line for line, _ in data]
    new_map = {}
    for i, (_, source_index) in enumerate(data, 1):
        if source_index in source_map:
            new_map[i] = source_map[source_index]
    return output_lines, new_map
