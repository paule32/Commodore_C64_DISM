# -*- coding: utf-8 -*-
"""Safe, source-preserving language variants for Windows RC projects.

A LANGUAGE statement in RC changes the *following* declarations.  Changing
one resource therefore requires restoring the previous language immediately
after its declaration. Candidate edits are recompiled and checked against the
original resource keys and bytes before the editor accepts them.
"""
from __future__ import annotations

import re
from typing import Callable, Iterable

_HEADER = re.compile(
    r'^\s*(?:STRINGTABLE\b|'
    r'(?:[A-Za-z_$][\w$@.]*|0[xX][\da-fA-F]+|\d+|"[^"]+")\s+'
    r'(?:DIALOGEX|DIALOG|MENUEX|MENU|ACCELERATORS|VERSIONINFO|TOOLBAR|'
    r'RCDATA|ICON|CURSOR|BITMAP|HTML|MANIFEST|MESSAGETABLE|FONT|DLGINCLUDE)\b)',
    re.IGNORECASE,
)
_LANG = re.compile(r'^\s*LANGUAGE\s+([^,\s]+)\s*,\s*([^\s/]+)', re.IGNORECASE)
_BRACES = re.compile(r'\bBEGIN\b|\bEND\b|\{|\}', re.IGNORECASE)
_STRINGS = re.compile(r'L?"(?:\\.|[^"\\])*"')


def language_statement(langid: int) -> str:
    langid = int(langid)
    if not 0 <= langid <= 0xFFFF:
        raise ValueError('LANGID außerhalb des 16-Bit-Bereichs')
    return f'LANGUAGE 0x{langid & 0x3ff:04X}, 0x{langid >> 10:02X}'


def _clean(line: str) -> str:
    # Ignore quoted text containing RC control words (e.g. "BEGIN").
    return _STRINGS.sub('""', line.split('//', 1)[0])


def _declarations(source: str) -> list[tuple[int, int]]:
    """Locate editable top-level RC declarations (line start, exclusive end)."""
    lines = source.splitlines(keepends=True)
    result = []
    i = 0
    while i < len(lines):
        if not _HEADER.match(_clean(lines[i])):
            i += 1
            continue
        start = i
        depth = 0
        opened = False
        end = i + 1
        header = _clean(lines[i]).upper()
        block_kind = bool(re.search(
            r'\b(STRINGTABLE|DIALOGEX|DIALOG|MENUEX|MENU|ACCELERATORS|'
            r'VERSIONINFO|TOOLBAR|RCDATA)\b', header))
        if block_kind:
            j = i
            while j < len(lines):
                for match in _BRACES.finditer(_clean(lines[j])):
                    token = match.group().upper()
                    if token in ('BEGIN', '{'):
                        depth += 1
                        opened = True
                    elif token in ('END', '}') and opened:
                        depth -= 1
                if opened and depth == 0:
                    end = j + 1
                    break
                if j > i and not opened and _HEADER.match(_clean(lines[j])):
                    break
                j += 1
        result.append((start, end))
        i = max(i + 1, end)
    return result


def _current_language(lines: list[str], line_number: int, default=0x0409) -> int:
    language = default
    for line in lines[:line_number]:
        match = _LANG.match(_clean(line))
        if not match:
            continue
        try:
            main = int(match.group(1), 0)
            sub = int(match.group(2), 0)
            language = ((sub & 0x3f) << 10) | (main & 0x3ff)
        except ValueError:
            # The real RC compiler will verify any symbolic expressions.
            continue
    return language


def _entries_map(entries: Iterable) -> dict:
    mapping = {}
    for entry in entries:
        key = (entry.type_id, entry.name_id, int(entry.language) & 0xffff)
        if key in mapping:
            raise ValueError(f'Doppelte Ressource: {key!r}')
        mapping[key] = (bytes(entry.data), int(entry.codepage))
    return mapping


def edit_resource_language(
    source: str, entry, language: int, compile_source: Callable[[str], Iterable],
    *, duplicate: bool = False,
) -> tuple[str, list, int]:
    """Return (new_rc_text, compiled_entries, selected_index).

    Has no IO or Qt side effects. A failing candidate never changes an
    existing resource, the editor buffer or files on disk.
    """
    target = int(language)
    statement = language_statement(target)
    oldkey = (entry.type_id, entry.name_id, int(entry.language) & 0xffff)
    newkey = (entry.type_id, entry.name_id, target)
    if not duplicate and newkey == oldkey:
        current = list(compile_source(source))
        return source, current, next(i for i, v in enumerate(current) if v.key() == oldkey)
    baseline = _entries_map(compile_source(source))
    if oldkey not in baseline:
        raise ValueError('Die ausgewählte Ressource ist nicht mehr im RC-Quelltext vorhanden.')
    if newkey in baseline:
        raise ValueError(f'Die Sprache 0x{target:04X} existiert für diese Ressource bereits.')
    lines = source.splitlines(keepends=True)
    for start, end in _declarations(source):
        block = ''.join(lines[start:end]).rstrip('\r\n') + '\n'
        if duplicate:
            candidate = source.rstrip('\r\n') + '\n\n' + statement + '\n' + block
        else:
            previous_lang = _current_language(lines, start)
            replacement = statement + '\n' + block + language_statement(previous_lang) + '\n'
            candidate = ''.join(lines[:start]) + replacement + ''.join(lines[end:])
        try:
            compiled = list(compile_source(candidate))
            changed = _entries_map(compiled)
        except Exception:
            continue
        if newkey not in changed or changed[newkey] != baseline[oldkey]:
            continue
        if duplicate:
            if all(changed.get(key) == value for key, value in baseline.items()):
                return candidate, compiled, next(i for i, v in enumerate(compiled) if v.key() == newkey)
        else:
            expected = dict(baseline)
            del expected[oldkey]
            expected[newkey] = baseline[oldkey]
            if expected == changed:
                return candidate, compiled, next(i for i, v in enumerate(compiled) if v.key() == newkey)
    raise ValueError(
        'Die Ressource konnte im RC-Quelltext nicht eindeutig zugeordnet werden. '
        'Sprachvarianten bei eingebundenen Dateien oder gemeinsamen STRINGTABLE-Blöcken '
        'bitte direkt im RC-Quelltext anlegen.'
    )
