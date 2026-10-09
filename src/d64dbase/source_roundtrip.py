"""Lossless WFM user-code serialization and source editor caret mapping.

Stage 307: the graphic designer owns properties, not the indentation of the
user's methods or the custom preamble preceding the WFM END HEADER marker.
"""

from bisect import bisect_right
from difflib import SequenceMatcher
import re
from typing import List

_HEADER_END = re.compile(r"^\s*\*\*\s*END\s+HEADER\s*--\s*do not remove this line\s*$", re.I)


def wfm_header_lines(source: str) -> List[str]:
    """Return the existing preamble INCLUDING its end-marker, if present."""
    lines = str(source).splitlines()
    for i, line in enumerate(lines):
        if _HEADER_END.match(line):
            return lines[:i + 1]
    return []


def wfm_method_source_lines(method) -> List[str]:
    """Preserve every original METHOD source line, including nested indentation.

    Only code synthesized by the designer (source_start_line == 0) is indented
    inside CLASS OF FORM. Parsed lines are never stripped or reindented.
    """
    original = list(getattr(method, "source_lines", None) or [])
    if original:
        if (not int(getattr(method, "source_start_line", 0) or 0)
                and original[0] and not original[0][0].isspace()):
            return ["    " + line if line else line for line in original]
        return original

    kind = str(getattr(method, "kind", "procedure") or "procedure")
    name = str(getattr(method, "name", "") or "")
    params = tuple(str(p) for p in getattr(method, "parameters", ()) or ())
    signature = "    " + kind + " " + name + (("(" + ", ".join(params) + ")") if params else "")
    body = list(getattr(method, "body", ()) or ())
    if not body:
        expr = str(getattr(method, "return_expr", "") or "")
        body = ["return" + ((" " + expr) if expr else "")]
    # Normalize only designer-generated method bodies, keeping relative depth.
    populated = [str(s) for s in body if str(s).strip()]
    base = min((len(s) - len(s.lstrip(" \t")) for s in populated), default=0)
    return [signature] + ["        " + str(s)[base:] if str(s).strip() else str(s) for s in body]


def _line_starts(lines: List[str]) -> List[int]:
    positions = [0]
    for line in lines:
        positions.append(positions[-1] + len(line))
    return positions


def remap_source_offset(old: str, new: str, offset: int) -> int:
    """Keep caret/selection on the same logical line after designer rebuild.

    Identical lines are mapped exactly. Changed sections map to the nearest
    replacement line/column rather than resetting the caret to position zero.
    """
    if old == new:
        return min(max(0, int(offset)), len(new))
    if int(offset) >= len(old):
        return len(new)
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    starts_old = _line_starts(old_lines)
    starts_new = _line_starts(new_lines)
    offset = min(max(0, int(offset)), len(old))
    line = min(bisect_right(starts_old, offset) - 1, len(old_lines) - 1) if old_lines else 0
    column = offset - starts_old[line] if old_lines else 0
    target_line = min(line, len(new_lines) - 1) if new_lines else 0
    for tag, a, b, x, y in SequenceMatcher(
        None, old_lines, new_lines,
        # Large WFM files repeat many WITH/ENDWITH lines: avoid O(N^2).
        autojunk=max(len(old_lines), len(new_lines)) >= 200,
    ).get_opcodes():
        if a <= line < b:
            if tag == "equal":
                target_line = x + (line - a)
            else:
                target_line = min(x + (line - a), max(x, y - 1))
            break
    if not new_lines:
        return 0
    target_line = min(max(0, target_line), len(new_lines) - 1)
    return min(len(new), starts_new[target_line] + min(column, len(new_lines[target_line].rstrip("\r\n"))))
