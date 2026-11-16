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
    """Stage 587: remove stack frames only after architecture-specific proof.

    PE32: follow all reachable branches, check ESP depth, rebase positive
    EBP-relative parameter slots, retain EBX/ESI/EDI via balanced PUSH/POP.
    PE64: only true leaf routines may reference caller-owned Win64 homes via
    RSP. Never drop security cookies, frame locals or non-leaf unwind frames.
    Preserve source-to-assembler line mappings.
    """
    if is_pe64:
        return _omit_pe64_leaf_frames_with_home_rebase(lines, source_map, routine_labels)
    return _omit_pe32_frames_with_stack_proof(lines, source_map, routine_labels)


# Stage 587: flow-sensitive PE32 frame-pointer omission.
# The normal code generator emits a frame even for calls which balance their
# arguments.  Verify stack-height on every reachable basic-block edge before
# rewriting any EBP-relative parameter address.
_PE32_FRAME_EPILOGUE = (
    'mov ebx, dword ptr [ebp-4]',
    'mov esi, dword ptr [ebp-8]',
    'mov edi, dword ptr [ebp-12]',
    'mov esp, ebp',
    'pop ebp',
)
_PE32_JCC = frozenset(('je', 'jne', 'jz', 'jnz', 'ja', 'jae', 'jb',
                       'jbe', 'jg', 'jge', 'jl', 'jle', 'jo', 'jno',
                       'js', 'jns', 'jp', 'jnp', 'jc', 'jnc'))
_PE32_EBP_REF = re.compile(r'\[ebp(?P<disp>[+-]\d+)?\]', re.I)


def _omit_pe32_frames_with_stack_proof(lines, source_map, routine_labels):
    """Remove eligible IA-32 frames without changing x86 calling semantics.

    Safe for balanced CDECL calls, nested PUSH/POP temporaries and static
    frame-relative *parameters* with provable ESP depth.  Rejected: negative
    EBP offsets (locals), cookies, unknown stack operations, shadow stack,
    unresolved branch targets, and inconsistent stack depth at CFG joins.
    """
    original = list(lines)
    roots = set(routine_labels)
    starts = [i for i, line in enumerate(original)
              if line.strip().endswith(':') and line.strip()[:-1] in roots]
    if not starts:
        return original, dict(source_map)
    records = [(line, i + 1) for i, line in enumerate(original)]
    regions = []
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(records)
        for k in range(start + 1, end):
            instruction = _instruction(original[k])
            if (instruction.startswith('section ') or
                    instruction.startswith('; stage 240: cdecl') or
                    instruction.startswith('; stage 532:') or
                    instruction.startswith('; stage 583:') or
                    re.match(r'^__pas(?:_unit_[\w]+)?_(?:vmt|cookie|console|write|print|read|range|clear)_[\w]+:$', instruction)):
                end = k
                break
        regions.append((start, end))

    def transform(segment):
        ops = [_instruction(t) for t, _ in segment]
        if len(ops) < 11 or ops[1:3] != ['push ebp', 'mov ebp, esp']:
            return None
        save_index = next((i for i in range(3, len(ops) - 2)
                           if ops[i:i+3] == ['push ebx', 'push esi', 'push edi']), None)
        if save_index is None:
            return None
        if any('cookie' in t or 'exception' in t or 'try_handler' in t
               for t in ops):
            return None
        # Every return path must have the canonical register restoration.
        end_begin = set()
        epilogue_idxs = set()
        for index, op in enumerate(ops):
            if re.fullmatch(r'ret(?: \d+)?', op):
                begin = index - len(_PE32_FRAME_EPILOGUE)
                if begin < save_index + 3 or tuple(ops[begin:index]) != _PE32_FRAME_EPILOGUE:
                    return None
                end_begin.add(begin)
                epilogue_idxs.update(range(begin, index))
        if not end_begin:
            return None

        labels = {}
        for i, op in enumerate(ops):
            if re.fullmatch(r'[a-z_.$?][\w.$?]*:', op):
                if i and op[:-1] in labels:
                    return None
                labels[op[:-1]] = i

        # Track ESP from the point just after removing PUSH EBP.
        # A normal CDECL call leaves this height unchanged (caller cleanup is
        # checked explicitly by the push/add balance). An unbalanced call
        # protocol cannot reach the canonical epilogue with height 12.
        heights = {3: 0}
        pending = [3]
        forbidden = re.compile(r'\b(?:enter|leave|iret|iretd|sysenter|syscall|int|retf|pushad|popad|pusha|popa|pushf|popf|pushfd|popfd|pushfw|popfw)\b')
        while pending:
            i = pending.pop()
            height = heights[i]
            if i >= len(ops):
                return None
            op = ops[i]
            if i in epilogue_idxs:
                if i not in end_begin or height != 12:
                    return None
                continue  # canonical epilogue is replaced in one step
            if i < 3 or forbidden.search(op):
                return None
            if re.search(r'\b(?:ebp|rbp)\b', op):
                # Only EBP-based *positive* argument addresses can be
                # rebased onto ESP; locals and frame-pointer arithmetic cannot.
                matches = list(_PE32_EBP_REF.finditer(op))
                if not matches or re.search(r'\b(?:ebp|rbp)\b',
                                             _PE32_EBP_REF.sub('', op)):
                    return None
                if any(int(m.group('disp') or '0') < 8 for m in matches):
                    return None
            if re.search(r'\b(?:esp|rsp)\b', op):
                # Never silently rewrite stack-relative memory or a pushed
                # pointer to the stack itself.  Only balancing ESP arithmetic.
                if not re.fullmatch(r'(?:add|sub) esp, (?:0x[0-9a-f]+|\d+)', op):
                    return None
            delta = 0
            if re.fullmatch(r'push (?!ebp\b|esp\b|word\b).+', op):
                delta = 4
            elif re.fullmatch(r'pop (?!ebp\b|esp\b|word\b).+', op):
                delta = -4
            else:
                m = re.fullmatch(r'(add|sub) esp, (0x[0-9a-f]+|\d+)', op)
                if m:
                    num = int(m.group(2), 0)
                    if num % 4 or num > 4096:
                        return None
                    delta = num if m.group(1) == 'sub' else -num
                elif re.match(r'^(?:push|pop|add esp|sub esp)\b', op):
                    return None
            new_height = height + delta
            if not 0 <= new_height <= 4096:
                return None
            edges = []
            if op.startswith(';') or op == '' or op.endswith(':') or op.startswith('global '):
                edges = [i + 1]
            elif op.startswith('ret'):
                # A return may only occur immediately after a valid epilogue.
                return None
            else:
                jump = re.fullmatch(r'(j[a-z]+|loop[a-z]*)\s+([a-z_.$?][\w.$?]*)', op)
                if jump:
                    mnemonic, target = jump.groups()
                    if target not in labels:
                        return None
                    if mnemonic == 'jmp':
                        edges = [labels[target]]
                    elif mnemonic in _PE32_JCC:
                        edges = [i + 1, labels[target]]
                    else:
                        return None
                elif re.match(r'^(?:j[a-z]+|loop[a-z]*)\b', op):
                    return None
                else:
                    edges = [i + 1]
            for edge in edges:
                if edge >= len(ops) or edge < 3:
                    return None
                existing = heights.get(edge)
                if existing is not None and existing != new_height:
                    return None
                if existing is None:
                    heights[edge] = new_height
                    pending.append(edge)
        if [heights.get(save_index + j) for j in range(3)] != [0, 4, 8]:
            return None
        # Refuse code containing EBP references in unreachable portions too:
        # no unsupported frames must survive in a partially rewritten routine.
        for i, op in enumerate(ops):
            if i < 3 or i in epilogue_idxs:
                continue
            if re.search(r'\b(?:ebp|rbp)\b', op) and i not in heights:
                return None

        result = []
        for i, (text, origin) in enumerate(segment):
            if i in (1, 2):
                continue
            if i in epilogue_idxs:
                if i in end_begin:
                    result.extend((f'    pop {reg}', origin)
                                  for reg in ('edi', 'esi', 'ebx'))
                continue
            if i in heights and _PE32_EBP_REF.search(text):
                depth = heights[i]
                def replacement(m):
                    # Original EBP = entryESP - 4; the optimized ESP
                    # has already consumed `depth` bytes of pushes.
                    offset = int(m.group('disp') or '0') + depth - 4
                    return f'[esp+{offset}]'
                text = _PE32_EBP_REF.sub(replacement, text)
            result.append((text, origin))
        return result

    output = []
    previous = 0
    for start, end in regions:
        output.extend(records[previous:start])
        segment = records[start:end]
        output.extend(transform(segment) or segment)
        previous = end
    output.extend(records[previous:])
    new_map = {i: source_map[origin]
               for i, (_, origin) in enumerate(output, 1)
               if origin in source_map}
    return [line for line, _ in output], new_map


# PE32+ leaf-function optimisation: do not create an RBP frame just to
# access Win64 caller-provided home slots. Only no-call/no-RSP-touch leaf
# functions qualify (no UNWIND_INFO is needed for a true frameless leaf).
_PE64_RBP_PARAM = re.compile(r'\[rbp\+(\d+)\]', re.I)


def _omit_pe64_leaf_frames_with_home_rebase(lines, source_map, routine_labels):
    original = list(lines)
    roots = set(routine_labels)
    starts = [i for i, line in enumerate(original)
              if line.strip().endswith(':') and line.strip()[:-1] in roots]
    if not starts:
        return original, dict(source_map)
    records = [(line, i + 1) for i, line in enumerate(original)]
    regions = []
    for n, start in enumerate(starts):
        stop = starts[n + 1] if n + 1 < len(starts) else len(records)
        for k in range(start + 1, stop):
            op = _instruction(original[k])
            if (op.startswith('section ') or
                    op.startswith('; stage 532:') or
                    op.startswith('; stage 583:') or
                    re.match(r'^__pas(?:_unit_[\w]+)?_(?:vmt|cookie|console|write|print|read|range|clear)_[\w]+:$', op)):
                stop = k
                break
        regions.append((start, stop))

    def transform(segment):
        ops = [_instruction(text) for text, _ in segment]
        if len(ops) < 6 or ops[1:3] != ['push rbp', 'mov rbp, rsp']:
            return None
        if '_method_' in ops[0]:
            return None
        end_begins = set()
        epilogue_indices = set()
        for i, op in enumerate(ops):
            if re.fullmatch(r'ret(?: \d+)?', op):
                if i < 5 or ops[i-2:i] != ['mov rsp, rbp', 'pop rbp']:
                    return None
                end_begins.add(i - 2)
                epilogue_indices.update((i - 2, i - 1))
        if not end_begins:
            return None
        local_labels = {op[:-1] for op in ops if re.fullmatch(r'[\w.$?]+:', op)}
        for i, op in enumerate(ops):
            if i in (1, 2) or i in epilogue_indices:
                continue
            if ('cookie' in op or 'exception' in op or 'try_handler' in op or
                    re.search(r'\b(?:call|syscall|int|enter|leave|push|pop|retf)\b', op)):
                return None
            if re.search(r'\b(?:rsp|esp)\b', op):
                return None
            # Never rewrite code that changes a Win64 nonvolatile register:
            # the original code must already preserve it to satisfy the ABI.
            if re.search(r'\b(?:rbx|ebx|rsi|esi|rdi|edi|r12|r13|r14|r15)\b', op):
                return None
            if re.search(r'\brbp\b', op):
                matches = list(_PE64_RBP_PARAM.finditer(op))
                if not matches or re.search(r'\brbp\b', _PE64_RBP_PARAM.sub('', op)):
                    return None
                if any(int(m.group(1)) < 16 or int(m.group(1)) % 8
                       for m in matches):
                    return None
            jump = re.fullmatch(r'(j[a-z]+|loop[a-z]*)\s+([a-z_.$?][\w.$?]*)', op)
            if jump and jump.group(2) not in local_labels:
                return None
            if re.match(r'^(?:j[a-z]+|loop[a-z]*)\b', op) and not jump:
                return None
        out = []
        for i, (text, origin) in enumerate(segment):
            if i in (1, 2) or i in epilogue_indices:
                continue
            if _PE64_RBP_PARAM.search(text):
                text = _PE64_RBP_PARAM.sub(
                    lambda m: f'[rsp+{int(m.group(1)) - 8}]', text)
            out.append((text, origin))
        return out

    output = []
    previous = 0
    for start, stop in regions:
        output.extend(records[previous:start])
        segment = records[start:stop]
        output.extend(transform(segment) or segment)
        previous = stop
    output.extend(records[previous:])
    new_map = {i: source_map[origin]
               for i, (_, origin) in enumerate(output, 1)
               if origin in source_map}
    return [line for line, _ in output], new_map
