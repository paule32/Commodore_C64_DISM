from __future__ import annotations

import re
from typing import Iterable, List, Optional, Sequence, Tuple

MAX_BASIC_LINE_NUMBER = 65535
MAX_BASIC_COLUMNS = 80

_BASIC_LINE_RE = re.compile(r"^\s*(\d+)\s?(.*)$")


class C64BasicLineNumberError(ValueError):
    """Raised when editor-side BASIC line numbering cannot be serialized."""


def split_numbered_basic_source(
    source: str,
) -> Tuple[List[str], List[Optional[int]]]:
    """Strip leading BASIC line numbers while preserving them separately.

    Lines without an explicit number are returned with ``None``.  Numbers above
    the C64 16-bit BASIC limit are also represented as ``None`` so the editor can
    mark those lines as invalid instead of ever displaying a number > 65535.
    """

    normalized = str(source).replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    # A file-ending newline is a terminator, not an additional BASIC program
    # line. Explicit numbered empty lines (e.g. "20") remain preserved.
    if len(lines) > 1 and normalized.endswith("\n") and lines[-1] == "":
        lines.pop()
    if not lines:
        lines = [""]
    numbers: List[Optional[int]] = []
    bodies: List[str] = []

    for raw in lines:
        match = _BASIC_LINE_RE.match(raw)
        if match is None:
            bodies.append(raw)
            numbers.append(None)
            continue
        number = int(match.group(1))
        bodies.append(match.group(2))
        numbers.append(number if 0 <= number <= MAX_BASIC_LINE_NUMBER else None)

    return bodies, numbers


def wrap_basic_lines(
    lines: Sequence[str],
    numbers: Sequence[Optional[int]],
    *,
    max_columns: int = MAX_BASIC_COLUMNS,
) -> Tuple[List[str], List[Optional[int]]]:
    """Hard-wrap source lines to ``max_columns`` characters.

    Only the first physical chunk retains the original BASIC line number.
    Continuation chunks receive ``None`` and are numbered by
    :func:`assign_missing_basic_numbers`.
    """

    width = max(1, int(max_columns))
    out_lines: List[str] = []
    out_numbers: List[Optional[int]] = []

    for index, text in enumerate(lines):
        number = numbers[index] if index < len(numbers) else None
        value = str(text)
        if len(value) <= width:
            out_lines.append(value)
            out_numbers.append(number)
            continue
        start = 0
        first = True
        while start < len(value):
            out_lines.append(value[start:start + width])
            out_numbers.append(number if first else None)
            first = False
            start += width

    if not out_lines:
        return [""], [None]
    return out_lines, out_numbers


def assign_missing_basic_numbers(
    numbers: Sequence[Optional[int]],
    *,
    maximum: int = MAX_BASIC_LINE_NUMBER,
) -> List[Optional[int]]:
    """Assign valid C64 BASIC numbers while preserving existing numbers.

    Runs between two existing BASIC numbers are distributed across the free
    integer interval (10/20 with one inserted line therefore becomes
    10/15/20). At the end of a program the editor prefers the classic BASIC
    +10 convention and automatically falls back to +1 near 65535.
    """

    limit = max(0, int(maximum))
    result: List[Optional[int]] = []
    for number in numbers:
        if number is None:
            result.append(None)
            continue
        value = int(number)
        result.append(value if 0 <= value <= limit else None)

    index = 0
    count = len(result)
    while index < count:
        if result[index] is not None:
            index += 1
            continue

        start = index
        while index < count and result[index] is None:
            index += 1
        end = index
        run_length = end - start

        previous = result[start - 1] if start > 0 else None
        following = result[end] if end < count else None
        assigned: List[Optional[int]] = [None] * run_length

        if previous is None and following is None:
            # Entirely new document: traditional 10,20,30... numbering first,
            # then use the final 65531..65535 values before reporting overflow.
            value = 10
            slot = 0
            while slot < run_length and value <= limit:
                assigned[slot] = value
                slot += 1
                value += 10
            if slot < run_length:
                value = max(1, ((assigned[slot - 1] or 0) + 1) if slot else 1)
                while slot < run_length and value <= limit:
                    assigned[slot] = value
                    slot += 1
                    value += 1

        elif previous is not None and following is None:
            previous_value = int(previous)
            # Prefer +10, but don't waste the remaining 16-bit BASIC range.
            if previous_value + 10 * run_length <= limit:
                assigned = [
                    previous_value + 10 * offset
                    for offset in range(1, run_length + 1)
                ]
            else:
                available = limit - previous_value
                for offset in range(run_length):
                    value = previous_value + offset + 1
                    assigned[offset] = value if offset < available else None

        elif previous is None and following is not None:
            following_value = int(following)
            available = following_value  # valid values are 0..following-1
            if following_value >= 10 * (run_length + 1):
                first = following_value - 10 * run_length
                assigned = [first + 10 * offset for offset in range(run_length)]
            elif available >= run_length:
                # Evenly distribute from 0 up to the following line number.
                span = following_value
                last_value = -1
                for offset in range(1, run_length + 1):
                    value = (span * offset) // (run_length + 1)
                    value = max(last_value + 1, value)
                    if value >= following_value:
                        value = following_value - (run_length - offset + 1)
                    assigned[offset - 1] = value if 0 <= value < following_value else None
                    if assigned[offset - 1] is not None:
                        last_value = int(assigned[offset - 1])

        else:
            previous_value = int(previous)
            following_value = int(following)
            free = following_value - previous_value - 1
            if free >= run_length:
                span = following_value - previous_value
                last_value = previous_value
                for offset in range(1, run_length + 1):
                    value = previous_value + (span * offset) // (run_length + 1)
                    value = max(last_value + 1, value)
                    max_here = following_value - (run_length - offset + 1)
                    value = min(value, max_here)
                    assigned[offset - 1] = value
                    last_value = value

        result[start:end] = assigned

    return result


def validate_basic_line_numbers(numbers: Sequence[Optional[int]]) -> None:
    seen = set()
    for physical, number in enumerate(numbers, 1):
        if number is None:
            raise C64BasicLineNumberError(
                f"Physische BASIC-Zeile {physical} besitzt keine freie "
                "Zeilennummer im Bereich 0..65535."
            )
        value = int(number)
        if not 0 <= value <= MAX_BASIC_LINE_NUMBER:
            raise C64BasicLineNumberError(
                f"BASIC-Zeilennummer {value} liegt außerhalb 0..65535."
            )
        if value in seen:
            raise C64BasicLineNumberError(
                f"BASIC-Zeilennummer {value} ist doppelt vorhanden."
            )
        seen.add(value)


def serialize_numbered_basic_source(
    lines: Sequence[str],
    numbers: Sequence[Optional[int]],
    *,
    newline: str = "\n",
) -> str:
    validate_basic_line_numbers(numbers)
    if len(lines) != len(numbers):
        raise C64BasicLineNumberError(
            "Interner BASIC-Editorfehler: Textzeilen und Gutter-Zeilen stimmen nicht überein."
        )
    return newline.join(
        f"{int(number)} {str(text)}" if str(text) else f"{int(number)}"
        for text, number in zip(lines, numbers)
    )


def sequential_basic_numbers(
    count: int,
    *,
    preferred_step: int = 10,
    maximum: int = MAX_BASIC_LINE_NUMBER,
) -> List[int]:
    """Return a strictly ascending BASIC line-number sequence.

    The classic 10,20,30,... layout is used whenever it fits into the C64
    16-bit line-number range.  For very large sources the largest uniform step
    below 10 is chosen automatically.  More than ``maximum`` physical BASIC
    lines cannot be represented without duplicate/invalid numbers.
    """

    total = max(0, int(count))
    limit = max(1, int(maximum))
    if total == 0:
        return []
    if total > limit:
        raise C64BasicLineNumberError(
            f"Das BASIC-Programm besitzt {total} physische Zeilen; im Bereich "
            f"1..{limit} können höchstens {limit} eindeutige Zeilennummern vergeben werden."
        )

    wanted = max(1, int(preferred_step))
    step = wanted if wanted * total <= limit else max(1, limit // total)
    return [step * index for index in range(1, total + 1)]


def _basic_reference_mask(text: str) -> str:
    """Mask quoted strings/comments while keeping source offsets stable."""

    value = str(text)
    chars = list(value)
    masked = list(value)
    in_string = False
    index = 0
    while index < len(chars):
        char = chars[index]
        if char == '"':
            masked[index] = ' '
            in_string = not in_string
            index += 1
            continue
        if in_string:
            masked[index] = ' '
            index += 1
            continue
        if char == "'":
            for tail in range(index, len(masked)):
                masked[tail] = ' '
            break
        index += 1

    visible = ''.join(masked)
    rem = re.search(r"(?i)(?<![A-Za-z0-9_])REM\b", visible)
    if rem is not None:
        start = rem.start()
        visible = visible[:start] + (' ' * (len(visible) - start))
    return visible


_BASIC_DIRECT_REFERENCE_RE = re.compile(
    r"(?i)\b(?:GOTO|GOSUB|THEN|RESTORE)\s+(\d+)"
)


def rewrite_basic_line_references(
    text: str,
    line_number_map: dict,
) -> str:
    """Rewrite direct BASIC line-number references without touching strings/REM.

    This covers the line-reference constructs currently accepted by the local
    C64 BASIC compiler: GOTO, GOSUB, numeric THEN and RESTORE.  Unknown targets
    are deliberately left untouched so renumbering never invents a destination.
    """

    value = str(text)
    if not line_number_map:
        return value
    mask = _basic_reference_mask(value)
    replacements = []
    for match in _BASIC_DIRECT_REFERENCE_RE.finditer(mask):
        old = int(match.group(1))
        if old not in line_number_map:
            continue
        replacements.append((match.start(1), match.end(1), str(int(line_number_map[old]))))

    for start, end, replacement in reversed(replacements):
        value = value[:start] + replacement + value[end:]
    return value



# ---------------------------------------------------------------------------
# Stage ASM 72: BASIC-Quelltext beim "Aktualisieren" kompakt formatieren.
# Nur syntaktisch bedeutungslose Leerzeichen an Ausdrucksoperatoren werden
# entfernt. Strings sowie REM-/Apostroph-Kommentare bleiben bytegenau erhalten.
# ---------------------------------------------------------------------------
_BASIC_COMPACT_OPERATOR_RE = re.compile(
    r"\s*(<=|>=|<>|=|\+|-|\*|/|\^|<|>)\s*"
)
_BASIC_OPEN_PAREN_SPACE_RE = re.compile(r"\(\s+")
_BASIC_CLOSE_PAREN_SPACE_RE = re.compile(r"\s+\)")


def _compact_basic_code_fragment(fragment: str) -> str:
    """Compact whitespace inside one unprotected BASIC code fragment."""

    value = str(fragment)
    value = _BASIC_COMPACT_OPERATOR_RE.sub(lambda match: match.group(1), value)
    value = _BASIC_OPEN_PAREN_SPACE_RE.sub("(", value)
    value = _BASIC_CLOSE_PAREN_SPACE_RE.sub(")", value)
    return value


def compact_basic_expression_spacing(text: str) -> str:
    """Remove redundant expression whitespace without touching literals/comments.

    Examples::

        A= 2 + 3 * 4      -> A=2+3*4
        FOR I = 1 TO 5    -> FOR I=1 TO 5

    Spaces that separate BASIC keywords, variable names and operands are kept.
    Quoted strings, ``REM`` comments and apostrophe comments are copied exactly.
    """

    source = str(text)
    output: List[str] = []
    code: List[str] = []
    index = 0

    def flush_code() -> None:
        if code:
            output.append(_compact_basic_code_fragment("".join(code)))
            code.clear()

    while index < len(source):
        ch = source[index]

        # String literals are protected completely, including all spaces and
        # operator-looking characters between the quotes.
        if ch == '"':
            flush_code()
            start = index
            index += 1
            while index < len(source):
                if source[index] == '"':
                    index += 1
                    break
                index += 1
            output.append(source[start:index])
            continue

        # Apostrophe comments are accepted by the local BASIC editor/compiler
        # and remain untouched from the comment marker to end-of-line.
        if ch == "'":
            flush_code()
            output.append(source[index:])
            break

        # Protect REM only when it is a standalone BASIC keyword. This avoids
        # mistaking identifiers such as REMOTE or XREM for comments.
        if source[index:index + 3].casefold() == "rem":
            previous_ok = index == 0 or not (
                source[index - 1].isalnum() or source[index - 1] == "_"
            )
            after = index + 3
            following_ok = after >= len(source) or not (
                source[after].isalnum() or source[after] == "_"
            )
            if previous_ok and following_ok:
                flush_code()
                output.append(source[index:])
                break

        code.append(ch)
        index += 1

    flush_code()
    return "".join(output)


def renumber_basic_program(
    lines: Sequence[str],
    numbers: Sequence[Optional[int]],
    *,
    preferred_step: int = 10,
    maximum: int = MAX_BASIC_LINE_NUMBER,
    max_columns: int = MAX_BASIC_COLUMNS,
    update_references: bool = True,
) -> Tuple[List[str], List[int], dict]:
    """Renumber all physical C64 BASIC editor lines.

    Existing semantic line numbers are replaced by a fresh ascending sequence;
    10,20,30,... is preferred whenever it fits below 65535. Direct references
    (GOTO/GOSUB/THEN/RESTORE) are rewritten to preserve control flow.

    The editor already guarantees that every physical BASIC line is at most 80
    characters wide. Renumbering never invents an extra physical line merely
    because a rewritten target gains a digit: if that rare case would exceed
    the 80-column limit, the operation is rejected and the user can shorten the
    affected statement first. This is safer than silently splitting a BASIC
    statement and changing program semantics.
    """

    source_lines = [str(item) for item in lines]
    source_numbers = [
        int(number) if number is not None else None for number in numbers
    ]
    if len(source_lines) != len(source_numbers):
        raise C64BasicLineNumberError(
            "Interner BASIC-Editorfehler: Textzeilen und Gutter-Zeilen stimmen nicht überein."
        )

    new_numbers = sequential_basic_numbers(
        len(source_lines), preferred_step=preferred_step, maximum=maximum
    )
    mapping = {
        int(old): int(new_numbers[index])
        for index, old in enumerate(source_numbers)
        if old is not None
    }

    new_lines = []
    width = max(1, int(max_columns))
    for index, original_text in enumerate(source_lines):
        compact_text = compact_basic_expression_spacing(original_text)
        body = (
            rewrite_basic_line_references(compact_text, mapping)
            if update_references
            else compact_text
        )
        if len(body) > width:
            old_number = source_numbers[index]
            label = str(old_number) if old_number is not None else str(index + 1)
            raise C64BasicLineNumberError(
                f"BASIC-Zeile {label} würde nach dem Aktualisieren {len(body)} Zeichen "
                f"besitzen. Erlaubt sind maximal {width} Zeichen. Bitte die Zeile "
                "zuerst verkürzen."
            )
        new_lines.append(body)

    return new_lines, new_numbers, mapping

# ---------------------------------------------------------------------------
# Stage ASM 59: Eingabe-Konvention fuer den C64-BASIC-Editor.
# Ausserhalb von Strings und REM-Kommentaren werden Buchstaben automatisch in
# Grossbuchstaben ueberfuehrt. Ziffern/Sonderzeichen bleiben unveraendert, so
# dass SHIFT+Ziffer weiterhin die jeweilige Tastaturbelegung (!, $, %, ...)
# liefert und normale Ziffern trotz BASIC-Grossschreibmodus direkt tippbar sind.
# ---------------------------------------------------------------------------
def basic_input_context(prefix: str) -> Tuple[bool, bool]:
    """Return ``(in_string, in_rem_comment)`` at the end of one BASIC line."""
    text = str(prefix or "")
    in_string = False
    index = 0
    while index < len(text):
        ch = text[index]
        if ch == '"':
            in_string = not in_string
            index += 1
            continue
        if not in_string and text[index:index + 3].casefold() == "rem":
            previous_ok = index == 0 or not (text[index - 1].isalnum() or text[index - 1] == "_")
            after = index + 3
            following_ok = after >= len(text) or not (text[after].isalnum() or text[after] == "_")
            if previous_ok and following_ok:
                return False, True
        index += 1
    return in_string, False


def transform_basic_typed_text(line_prefix: str, inserted: str) -> str:
    """Apply Stage-59 BASIC uppercase rules to newly inserted editor text.

    ``line_prefix`` is the already existing text before the insertion point on
    the current physical BASIC line. Newlines reset string/REM state.
    """
    current = str(line_prefix or "")
    source = str(inserted or "").replace("\r\n", "\n").replace("\r", "\n")
    output: List[str] = []
    for ch in source:
        if ch == "\n":
            output.append(ch)
            current = ""
            continue
        in_string, in_rem = basic_input_context(current)
        value = ch
        if not in_string and not in_rem and ch.isalpha():
            value = ch.upper()
        output.append(value)
        current += value
    return "".join(output)
