"""NASM-compatible logical line locations for the integrated Windows COFF assembler.

Only source positions change.  %line produces no machine instructions, data,
imports, exports, or COFF relocations.  The preceding macro processor expands
%include; this adapter preserves its location map for included files.
"""
from __future__ import annotations

import os
import posixpath
import re
from typing import Iterable

_LINE = re.compile(
    r'^\s*%line\s+(\d+)(?:\+(\d+))?(?:\s+("[^"\r\n]*"|\S+))?\s*(?:;.*)?$',
    flags=re.IGNORECASE,
)
_START = re.compile(r'^\s*%line(?:\s|$)', flags=re.IGNORECASE)


def strip_line_directives(source: str, filename: str):
    """Remove %line before macro expansion, preserving physical line count.

    Returns (source_without_directives, {physical_1_based: (file, logical_line)}).
    %line N resets the *following* line to logical line N (NASM semantics).
    %line N+M increments subsequent logical lines by M.  An optional quoted
    filename overrides the error-report filename, not the include resolver.
    """
    if not _START.search(source):
        # Fast path: if no line begins with %line, do not modify source.
        if not any(_START.match(row) for row in source.splitlines()):
            return source, {}
    physical = 0
    logical = 1
    increment = 1
    report_file = str(filename)
    mapping = {}
    output = []
    seen_marker = False
    for raw in source.splitlines(keepends=True):
        physical += 1
        if _START.match(raw):
            directive = _LINE.fullmatch(raw.rstrip('\r\n'))
            if directive is None:
                raise ValueError(f"Ungültige %line-Direktive in Zeile {physical}: {raw.strip()}")
            logical = int(directive.group(1))
            increment = int(directive.group(2) or 1)
            if logical < 1 or increment < 0:
                raise ValueError(f"Ungültige %line-Zeilennummer in Zeile {physical}")
            if directive.group(3):
                report_file = directive.group(3).strip('"')
            seen_marker = True
            # Keep a physical newline so preprocessor error positions remain
            # stable; the assembler sees a blank, not an unknown directive.
            output.append('\r\n' if raw.endswith('\r\n') else
                          '\n' if raw.endswith('\n') else '')
        else:
            output.append(raw)
            if seen_marker:
                mapping[physical] = (report_file, logical)
            logical += increment
    return ''.join(output), mapping


def _path_key(path) -> str:
    value = str(path).replace('\\', '/').casefold()
    if value.startswith('<') or value.startswith('/') or re.match(r'^[a-z]:/', value):
        return posixpath.normpath(value)
    return posixpath.normpath(os.path.abspath(value).replace('\\', '/'))


def remap_asm_locations(locations: Iterable[tuple[str, int]], filename: str,
                        remapping: dict[int, tuple[str, int]]):
    """Map only the containing ASM file; included-file line numbers are local."""
    source_key = _path_key(filename)
    result = []
    for file, physical in locations:
        if _path_key(file) == source_key and physical in remapping:
            result.append(remapping[physical])
        else:
            result.append((file, physical))
    return tuple(result)
