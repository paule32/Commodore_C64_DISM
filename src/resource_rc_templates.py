# -*- coding: utf-8 -*-
"""Stage 457: insertable Microsoft RC source templates for the resource editor.

No Qt dependency: the same template generator can be tested and used by other
editors without starting the GUI.  Names are unique within the active source.
"""
from __future__ import annotations

import re

RESOURCE_TEMPLATE_KINDS = ("Dialog", "Text", "Icon", "Bitmap", "Cursor", "RCDATA")


def _next_suffix(source: str, prefix: str) -> int:
    occupied = {
        int(match.group(1))
        for match in re.finditer(r"\b" + re.escape(prefix) + r"_(\d+)\b", source, re.I)
    }
    index = 1
    while index in occupied:
        index += 1
    return index


def rc_template(kind: str, source: str = "") -> str:
    """Return a complete RC resource declaration suitable for cursor insertion."""
    key = str(kind).strip().casefold()
    if key == "dialog":
        index = _next_suffix(source, "IDD_DIALOG")
        base = 1000 + 10 * index
        return (
            f"IDD_DIALOG_{index} DIALOGEX 0, 0, 220, 120\n"
            "STYLE DS_SETFONT | DS_MODALFRAME | WS_POPUP | WS_CAPTION | WS_SYSMENU\n"
            'CAPTION "Neuer Dialog"\n'
            'FONT 9, "Segoe UI"\n'
            "BEGIN\n"
            '    LTEXT "Dialogvorlage", -1, 12, 12, 190, 14\n'
            f'    DEFPUSHBUTTON "OK", {base + 1}, 105, 92, 50, 14\n'
            f'    PUSHBUTTON "Abbrechen", {base + 2}, 161, 92, 50, 14\n'
            "END\n"
        )
    if key == "text":
        # STRINGTABLE entries use numeric resource IDs, not the IDS_TEXT
        # helper label.  Avoid duplicates when the button is clicked twice.
        used_ids = {int(token) for token in re.findall(r'(?m)^\s*(\d+)\s+"', source)}
        index = 1
        while 2000 + index in used_ids:
            index += 1
        return (
            f"// Text-Ressource {index}\n"
            "STRINGTABLE\nBEGIN\n"
            f'    {2000 + index} "Neuer Text"\n'
            "END\n"
        )
    if key in {"icon", "bitmap", "cursor"}:
        prefix, extension = {
            "icon": ("IDI_ICON", "ico"),
            "bitmap": ("IDB_BITMAP", "bmp"),
            "cursor": ("IDC_CURSOR", "cur"),
        }[key]
        index = _next_suffix(source, prefix)
        return f'{prefix}_{index} {key.upper()} "{key}_{index}.{extension}"\n'
    if key == "rcdata":
        index = _next_suffix(source, "IDR_RCDATA")
        return (
            f"IDR_RCDATA_{index} RCDATA\n"
            "BEGIN\n"
            "    0x0001, 0x0002, 0x0003\n"
            "END\n"
        )
    raise ValueError(f"Unbekannte Ressourcen-Vorlage: {kind!r}")


def insertable_rc_template(kind: str, source: str, cursor_position: int) -> str:
    """Insert a resource on its own lines, preserving surrounding RC text."""
    text = rc_template(kind, source)
    before = source[:max(0, int(cursor_position))]
    after = source[max(0, int(cursor_position)):]
    prefix = "" if not before or before.endswith("\n") else "\n"
    # Add a blank line between declarations but not at the start of a file.
    if before and before.strip() and not before.endswith("\n\n"):
        prefix += "\n"
    suffix = "\n" if after.strip() and not after.startswith("\n") else ""
    return prefix + text + suffix
