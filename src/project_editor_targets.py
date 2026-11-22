"""Persist compiler/assembler toolbar targets per project source file.

The file is intentionally independent of Qt, so legacy *.pro projects and
future GUI versions can share the same encoding and decoding rules.
"""
from __future__ import annotations

import json

SECTION = 'Settings.EditorCompilerTargets'
ENTRY_KEY = '__project_editor_compiler_targets__'
VALID_TARGETS = frozenset(('c64', 'amiga', 'pe32', 'pe64', 'linux32', 'linux64'))


def write_editor_targets(parser, rows, project_path, encode_path):
    """Add the source-specific target settings to a ConfigParser."""
    parser[SECTION] = {'Title': 'Compiler- und Assemblerziele der Quelldateien'}
    count = 0
    for row in rows or ():
        if not isinstance(row, dict):
            continue
        path = str(row.get('path', '') or '').strip()
        target = str(row.get('target', '') or '').casefold().strip()
        if not path or target not in VALID_TARGETS:
            continue
        count += 1
        parser[SECTION][f'Item{count:04d}'] = json.dumps({
            'path': encode_path(path, project_path), 'target': target,
        }, ensure_ascii=False, separators=(',', ':'))


def read_editor_targets(parser, project_path, decode_path):
    """Restore targets, ignoring invalid/older entries without breaking load."""
    rows = []
    if not parser.has_section(SECTION):
        return rows
    for key, data in parser.items(SECTION):
        if not key.casefold().startswith('item'):
            continue
        try:
            row = json.loads(data)
        except (ValueError, TypeError):
            continue
        if not isinstance(row, dict):
            continue
        path = str(row.get('path', '') or '').strip()
        target = str(row.get('target', '') or '').casefold().strip()
        if path and target in VALID_TARGETS:
            rows.append({'path': decode_path(path, project_path), 'target': target})
    return rows
