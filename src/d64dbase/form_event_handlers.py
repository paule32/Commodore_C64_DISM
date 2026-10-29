"""Shared, Qt-independent helpers for WFM designer event navigation (Stage 494)."""

from __future__ import annotations

import re
from typing import Mapping


_PROCEDURE_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")


def normalized_focus_events(events: Mapping) -> dict:
    """Migrate the former OnGetFocus spelling without losing existing bindings.

    An existing OnGotFocus binding takes precedence if both spellings exist.
    Non-focus events are preserved without changing spelling or order.
    """
    result = dict(events or {})
    old_keys = [key for key in result if str(key).casefold() == 'ongetfocus']
    new_keys = [key for key in result if str(key).casefold() == 'ongotfocus']
    if old_keys and not new_keys:
        result['OnGotFocus'] = result[old_keys[0]]
    for key in old_keys:
        result.pop(key, None)
    return result


def resolve_event_procedure(text: str, placeholder: str) -> str:
    """Use the actual cell value or the visible placeholder on double-click."""
    name = str(text or '').strip() or str(placeholder or '').strip()
    if '::' in name:
        name = name.rsplit('::', 1)[-1].strip()
    if not _PROCEDURE_IDENTIFIER.fullmatch(name):
        raise ValueError(f'Ungültiger WFM-Prozedurname: {name!r}')
    return name


def find_event_procedure_offset(source: str, name: str):
    """Find an existing procedure/function without matching name prefixes."""
    if not _PROCEDURE_IDENTIFIER.fullmatch(str(name or '')):
        return None
    m = re.search(
        rf'(?im)^[ \t]*(?:procedure|function)[ \t]+'
        rf'{re.escape(name)}(?=[ \t(]|$)',
        str(source or ''),
    )
    return m.start() if m else None
