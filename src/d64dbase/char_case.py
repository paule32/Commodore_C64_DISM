"""Stage 326: one-character case predicates for the Windows-1252 dBase ABI.

The native dBase value slots store text in Windows-1252 (see
``_DBaseEmitter.text_literal``).  A character predicate always returns a
numeric Boolean, 0 or 1.  Non-character strings (length != 1) return 0 at
runtime; non-text arguments are rejected by semantic analysis.
"""
from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=2)
def _ranges(upper: bool) -> tuple[tuple[int, int], ...]:
    values = []
    for byte in range(256):
        try:
            char = bytes((byte,)).decode("cp1252")
        except UnicodeDecodeError:
            continue
        if char.isupper() if upper else char.islower():
            values.append(byte)
    ranges: list[tuple[int, int]] = []
    for byte in values:
        if ranges and ranges[-1][1] == byte - 1:
            ranges[-1] = ranges[-1][0], byte
        else:
            ranges.append((byte, byte))
    return tuple(ranges)


def is_char_case(value: object, *, upper: bool) -> bool:
    """Model the same single-byte predicate as the emitted PE32/PE64 code."""
    if not isinstance(value, str) or len(value) != 1:
        return False
    try:
        payload = value.encode("cp1252")
    except UnicodeEncodeError:
        return False
    return any(lo <= payload[0] <= hi for lo, hi in _ranges(upper))


def _cp1252_is_case(byte: int, upper: bool) -> bool:
    try:
        char = bytes((byte,)).decode("cp1252")
    except UnicodeDecodeError:
        return False
    return char.isupper() if upper else char.islower()


def _contiguous_ranges(values: list[int]) -> tuple[tuple[int, int], ...]:
    result: list[tuple[int, int]] = []
    for value in values:
        if result and result[-1][1] == value - 1:
            result[-1] = result[-1][0], value
        else:
            result.append((value, value))
    return tuple(result)


def emit_char_case_check(
    source_slot: str, *, is64: bool, label_prefix: str, upper: bool,
    temp_number: str = "__dbase_temp_number", encoding: str = "cp1252",
    has_shadow_space: bool = False,
) -> list[str]:
    """Call Stage-448 shared runtime and leave a numerical Boolean on ST(0).

    Keeps the original frontend ABI; no long inlined character tables.
    """
    from .char_case_runtime import export_name
    public = export_name(upper=upper, encoding=encoding)
    ptr_type = "qword" if is64 else "dword"
    if is64:
        lines = [
            f"    mov rcx, {ptr_type} ptr [{source_slot}_ptr]",
            f"    mov edx, dword ptr [{source_slot}_len]",
            *([] if has_shadow_space else ["    sub rsp, 40"]),
            f"    call {public}",
            *([] if has_shadow_space else ["    add rsp, 40"]),
        ]
    else:
        lines = [
            f"    push dword ptr [{source_slot}_len]",
            f"    push dword ptr [{source_slot}_ptr]",
            f"    call {public}",
            "    add esp, 8",
        ]
    return lines + [
        f"    mov dword ptr [{temp_number}], eax",
        f"    fild dword ptr [{temp_number}]",
    ]
