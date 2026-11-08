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


def omit_safe_pascal_stack_frames(lines, source_map, routine_labels, *, is_pe64=False):
    """Stage 538: optional frame-pointer omission for *provably frame-free* routines.

    Never change stack-cookie instrumentation, exceptions, stack variables,
    frame-relative parameters, Win64 caller home/shadow space or non-leaf
    AMD64 calls.  On x86 we preserve EBX/ESI/EDI through balanced PUSH/POP.
    Original source-line associations are retained after rewriting.
    """
    source = list(lines)
    recognized = set(routine_labels)
    starts = [i for i, line in enumerate(source)
              if line.strip().endswith(':') and line.strip()[:-1] in recognized]
    if not starts:
        return source, dict(source_map)
    # Keep the source-map origin along with each instruction during edits.
    records = [(line, idx + 1) for idx, line in enumerate(source)]
    regions = []
    for index, start in enumerate(starts):
        stop = starts[index + 1] if index + 1 < len(starts) else len(records)
        # The last routine is followed by metadata, export stubs and/or runtime.
        for j in range(start + 1, stop):
            op = records[j][0].strip().lower()
            if (op.startswith('section ') or
                    op.startswith('; stage 240: cdecl') or
                    op.startswith('; stage 532:') or
                    re.match(r'^__pas(?:_unit_[\w]+)?_(?:vmt|cookie|console|write|print|read|range|clear)_[\w]+:$', op)):
                stop = j
                break
        regions.append((start, stop))

    def safe_frame(segment):
        if len(segment) < (7 if is_pe64 else 10):
            return None
        ins = [_instruction(line) for line, _ in segment]
        # First instructions must be the exact compiler-emitted prologue.
        required_prologue = (['push rbp', 'mov rbp, rsp'] if is_pe64
                             else ['push ebp', 'mov ebp, esp'])
        if ins[1:3] != required_prologue:
            return None
        if any('cookie' in op or 'exception' in op or 'try_handler' in op
               for op in ins):
            return None
        if is_pe64:
            # Win64 method functions modify nonvolatile RSI, which requires
            # valid unwind metadata. Without an emitted UNWIND_INFO record, do
            # not turn these routines into apparent frameless leaf functions.
            if '_method_' in ins[0]:
                return None
            pro_end = 3
            epilogue = ['mov rsp, rbp', 'pop rbp']
            # Win64 requires stack alignment + shadow space for CALL; do not
            # rewrite any routine performing a call (including indirect calls).
            if any(re.match(r'^(call|syscall|int)\b', op) for op in ins[pro_end:]):
                return None
        else:
            if ins[3:6] != ['push ebx', 'push esi', 'push edi']:
                return None
            pro_end = 6
            epilogue = [
                'mov ebx, dword ptr [ebp-4]',
                'mov esi, dword ptr [ebp-8]',
                'mov edi, dword ptr [ebp-12]',
                'mov esp, ebp', 'pop ebp',
            ]

        end_positions = set()
        for i, op in enumerate(ins):
            if re.fullmatch(r'ret(?: \d+)?', op):
                begin = i - len(epilogue)
                if begin < pro_end or ins[begin:i] != epilogue:
                    return None
                end_positions.update(range(begin, i))
        if not end_positions:
            return None
        for i, op in enumerate(ins):
            if i in end_positions or i in (1, 2):
                continue
            if not is_pe64 and i in (3, 4, 5):
                continue
            if re.search(r'\b(?:ebp|rbp)\b', op):
                return None
            # No local stack allocations or hidden stack-frame manipulations.
            if re.search(r'\b(?:sub|and|mov|lea|xchg|leave)\s+(?:e|r)sp\b', op):
                return None
            if is_pe64 and re.search(r'\b(?:rsp|esp)\b', op):
                return None
            if not is_pe64:
                # IA-32: deliberately restrict omission to leaf code without
                # dynamic PUSH/POP. Frame teardown must not mask imbalanced
                # stack use in a CALL, an early branch, or exception cleanup.
                if re.match(r'^(?:call|push|pop|enter|leave|int|syscall)\b', op):
                    return None
                if '_jit_exception_' in op or '_jit_raise' in op:
                    return None
        return pro_end, epilogue, end_positions

    output = []
    previous = 0
    for start, stop in regions:
        output.extend(records[previous:start])
        segment = records[start:stop]
        proof = safe_frame(segment)
        if proof is None:
            output.extend(segment)
        else:
            pro_end, epilogue, ends = proof
            skip = set((1, 2)) | ends
            for i, (line, origin) in enumerate(segment):
                if i in skip:
                    # Replace the x86 saved-register loads with matching POPs.
                    if not is_pe64 and i == 0:
                        pass
                    if i in ends and _instruction(line) == epilogue[0]:
                        if not is_pe64:
                            # At the beginning of each epilogue, restore registers.
                            output.extend((f'    pop {reg}', origin)
                                          for reg in ('edi', 'esi', 'ebx'))
                    continue
                output.append((line, origin))
        previous = stop
    output.extend(records[previous:])
    new_map = {}
    for index, (_, origin) in enumerate(output, 1):
        if origin in source_map:
            new_map[index] = source_map[origin]
    return [line for line, _ in output], new_map
