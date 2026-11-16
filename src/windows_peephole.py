"""Stage 609: conservative size peephole pass for generated dBASE/Pascal PE ASM.

Disabled by default; each control is independently opt-in.  The pass only
rewrites register-immediate instructions in .text when safety can be proven.
Import directives, data, user ASM sidecars and ABI prologues are left intact.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping

KEYS = ('register_width', 'processor_flags', 'stack_state')


def normalize_peephole_options(value=None) -> dict[str, bool]:
    data = value if isinstance(value, Mapping) else {}
    def boolean(item):
        return str(item).strip().lower() in ('1', 'true', 'yes', 'on') if isinstance(item, str) else bool(item)
    return {key: boolean(data.get(key, False)) for key in KEYS}


@dataclass(frozen=True)
class PeepholeResult:
    assembly: str
    source_map: dict[int, int]
    replacements: int
    byte_savings: int


_INSTRUCTION = re.compile(r'^(\s*)mov\s+(eax|rax)\s*,\s*(0|1)\s*(;.*)?$', re.I)
_SECTION = re.compile(r'^\s*(?:section|segment)\s+(\.[\w]+)', re.I)
_LABEL = re.compile(r'^\s*(?:[a-z_.$?][\w.$?]*|\.\w+):', re.I)
_READ_FLAGS = re.compile(r'^(?:j(?!mp\b)[a-z]{1,3}|set[a-z]{1,3}|cmov[a-z]{1,3}|adc|sbb|rcl|rcr|lahf|pushf[a-z]*|into)\b', re.I)
_WRITE_FLAGS = re.compile(r'^(?:cmp|test|xor|and|or|add|sub|inc|dec|neg|shl|shr|sar|sal|imul|mul|div|idiv|bt|bts|btr|btc)\b', re.I)
_SAFE_NO_FLAGS = re.compile(r'^(?:mov|movzx|movsx|lea|push|pop|nop|cdq|cqo|movsxd|xchg)\b', re.I)
_RET = re.compile(r'^ret(?:\s+\d+)?$', re.I)


def _code(line: str) -> str:
    return line.split(';', 1)[0].strip().lower()


def _flags_dead(lines: list[str], at: int) -> bool:
    """Only rewrite MOV->XOR when flags cannot be observed on any path.

    Look through a single *straight-line* region. Never cross labels, macros,
    conditional/unconditional control transfers or unknown instructions. A
    known flag write or RET proves the previous flags dead. Calls are barriers.
    """
    for raw in lines[at + 1:]:
        instr = _code(raw)
        if not instr:
            continue
        if _SECTION.match(instr) or _LABEL.match(instr) or instr.startswith(('%', '.', 'global ', 'extern ', 'import ', 'bits ')):
            return False
        if _RET.fullmatch(instr):
            return True
        if _READ_FLAGS.match(instr):
            return False
        if _WRITE_FLAGS.match(instr):
            return True
        if not _SAFE_NO_FLAGS.match(instr):
            return False
    return False


def _stack_safe_at_return(lines: list[str], at: int) -> bool:
    """Balanced PUSH/POP substitute is restricted to a terminal return value."""
    for raw in lines[at + 1:]:
        instr = _code(raw)
        if not instr:
            continue
        return bool(_RET.fullmatch(instr))
    return False


def optimize_windows_assembly(assembly: str, *, target: str = 'pe32',
                              options=None, source_map=None) -> PeepholeResult:
    """Return optimized text and its remapped Pascal assembler/source lines.

    The original assembly is returned without any change when unchecked.
    Replacements do not affect other labels, flags, or the final stack depth.
    """
    flags = normalize_peephole_options(options)
    source_map = dict(source_map or {})
    if not flags['register_width'] or not (flags['processor_flags'] or flags['stack_state']):
        return PeepholeResult(assembly, source_map, 0, 0)
    if str(target).strip().casefold() not in ('pe32', 'pe64', 'win32', 'win64'):
        return PeepholeResult(assembly, source_map, 0, 0)
    is64 = str(target).strip().casefold() in ('pe64', 'win64')
    lines = assembly.splitlines(keepends=True)
    output = []
    remap = {}
    replacements = saved = 0
    in_text = False
    for i, raw in enumerate(lines):
        current = _code(raw)
        section = _SECTION.match(current)
        if section:
            in_text = section.group(1).lower() in ('.text', '.code')
        new_lines = [raw]
        match = _INSTRUCTION.match(raw.rstrip('\r\n')) if in_text else None
        if match:
            indent, reg, number, comment = match.groups()
            reg = reg.lower()
            number = int(number)
            # RAX zero-extension through EAX is defined in 64-bit mode.
            if reg == 'eax' or is64:
                newline = '\r\n' if raw.endswith('\r\n') else '\n' if raw.endswith('\n') else ''
                suffix = (' ' + comment.strip()) if comment else ''
                replacement = None
                byte_delta = 0
                # A transient balanced stack operation does not modify EFLAGS.
                if number == 1 and flags['stack_state'] and _stack_safe_at_return(lines, i):
                    replacement = [f'{indent}push 1{suffix}{newline}',
                                   f'{indent}pop {"rax" if is64 else "eax"}{newline}']
                    old_size = 7 if reg == 'rax' else 5
                    byte_delta = old_size - 3
                elif flags['processor_flags'] and _flags_dead(lines, i):
                    if number == 0:
                        replacement = [f'{indent}xor eax, eax{suffix}{newline}']
                        byte_delta = (7 if reg == 'rax' else 5) - 2
                    else:
                        replacement = [f'{indent}xor eax, eax{suffix}{newline}',
                                       f'{indent}inc eax{newline}']
                        byte_delta = (7 if reg == 'rax' else 5) - (4 if is64 else 3)
                if replacement and byte_delta > 0:
                    new_lines = replacement
                    replacements += 1
                    saved += byte_delta
        for line in new_lines:
            output.append(line)
            if i + 1 in source_map:
                remap[len(output)] = source_map[i + 1]
    return PeepholeResult(''.join(output), remap, replacements, saved)
