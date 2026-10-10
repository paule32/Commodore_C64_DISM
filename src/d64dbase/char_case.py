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
) -> list[str]:
    """Emit a bounds-checked comparison for exactly one Windows-1252 byte.

    Leaves a double-precision x87 value 0 or 1 on ST0, consistent with the
    existing dBase numerical-Boolean convention.  Does not call a DLL.
    """
    true_label = label_prefix + "_true"
    false_label = label_prefix + "_false"
    done_label = label_prefix + "_done"
    if encoding not in {"cp1252", "utf8"}:
        raise ValueError(f"Unsupported dBase character encoding: {encoding}")
    ptr = ("rdx" if is64 else "edx") if encoding == "utf8" else ("rax" if is64 else "eax")
    ptr_type = "qword" if is64 else "dword"
    code = [
        f"    mov {ptr}, {ptr_type} ptr [{source_slot}_ptr]",
        f"    test {ptr}, {ptr}",
        f"    je {false_label}",
    ]
    if encoding == "utf8":
        one = label_prefix + "_one_byte"
        value_ready = label_prefix + "_value_ready"
        code.extend((
            f"    cmp dword ptr [{source_slot}_len], 1",
            f"    je {one}",
            f"    cmp dword ptr [{source_slot}_len], 2",
            f"    jne {false_label}",
            f"    movzx eax, byte ptr [{ptr}]",
            f"    cmp eax, 194",     # Valid UTF-8 two-byte lead
            f"    jb {false_label}",
            f"    cmp eax, 223",
            f"    ja {false_label}",
            f"    and eax, 31",
            f"    shl eax, 6",
            f"    movzx ecx, byte ptr [{ptr}+1]",
            f"    cmp ecx, 128",
            f"    jb {false_label}",
            f"    cmp ecx, 191",
            f"    ja {false_label}",
            f"    and ecx, 63",
            f"    or eax, ecx",
            f"    jmp {value_ready}",
            f"{one}:",
            f"    movzx eax, byte ptr [{ptr}]",
            f"    cmp eax, 127",
            f"    ja {false_label}",
            f"{value_ready}:",
        ))
        upper_or_lower = sorted({
            ord(bytes((byte,)).decode("cp1252"))
            for byte in range(256)
            if _cp1252_is_case(byte, upper)
        })
        case_ranges = _contiguous_ranges(upper_or_lower)
    else:
        code.extend((
            f"    cmp dword ptr [{source_slot}_len], 1",
            f"    jne {false_label}",
            f"    movzx eax, byte ptr [{ptr}]",
        ))
        case_ranges = _ranges(upper)
    for index, (lo, hi) in enumerate(case_ranges):
        if lo == hi:
            code.extend((f"    cmp eax, {lo}", f"    je {true_label}"))
        else:
            after_label = f"{label_prefix}_next_{index}"
            code.extend((
                f"    cmp eax, {lo}",
                f"    jb {after_label}",
                f"    cmp eax, {hi}",
                f"    jbe {true_label}",
                f"{after_label}:",
            ))
    code.extend((
        f"{false_label}:",
        f"    mov dword ptr [{temp_number}], 0",
        f"    jmp {done_label}",
        f"{true_label}:",
        f"    mov dword ptr [{temp_number}], 1",
        f"{done_label}:",
        f"    fild dword ptr [{temp_number}]",
    ))
    return code
