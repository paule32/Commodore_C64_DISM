#!/usr/bin/env python3
"""Apply the Pascal tree / editor popup patch to the repository reference revision.

Target: paule32/Commodore_C64_DISM, main, src/d64_dism.py
Git blob: 5f9f8a5b3e8b3ca1120d6a137a868b70e66f4b46

The patch is deliberately SHA-locked so unrelated source versions are not modified.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
from pathlib import Path
import sys

BASE_BLOB = '5f9f8a5b3e8b3ca1120d6a137a868b70e66f4b46'
TARGET = Path('d64_dism.py')


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def patch_text(source: str) -> str:
    original_lines = source.split('\n')
    inserts: dict[int, str] = {}
    changes: dict[int, str] = {}

    def insert_before(line: int, code: str) -> None:
        if line in inserts:
            raise ValueError(f'Insertion line {line} specified twice')
        inserts[line] = code

    def replace(line: int, expected: str, code: str) -> None:
        actual = original_lines[line - 1]
        if expected not in actual:
            raise ValueError(f'Unexpected source at line {line}: {actual!r}, expected {expected!r}')
        changes[line] = code

    def replace_range(start: int, end: int, code: str) -> None:
        for line in range(start, end + 1):
            changes[line] = code if line == start else ''

    # Persisted Pascal entries are still read from the existing *.pro lists,
    # but all new tree items (including those reconstructed at project load)
    # become immediate children of their respective group.
    replace(136768, '("units", "Units",',
            '                            ("units", "Unit", PROJECT_NODE_PASCAL_UNIT_ROOT),')
    if 'if role == "units":' not in '\n'.join(original_lines[139538:139549]):
        raise ValueError('Pascal namespace grouping was not found at expected source location')
    replace_range(139537, 139549, '''            parent_item = group_item
            display_title = title.strip() or resolved.name or path_text
            # Pascal-Units und -Module sind direkte Dateiblaetter unter
            # dem jeweiligen Zielknoten; keine Namespace-Unterordner anlegen.''')

    # The C64 ephemeral marker also occupied Qt.UserRole+307 in the legacy
    # Pascal namespace model. Limit deletion/activation strictly to C64 leaves.
    insert_before(141599, '''        @staticmethod
        def _is_unsaved_c64_project_leaf(item: QTreeWidgetItem) -> bool:
            """Check only actual unsaved C64 files, never Pascal namespace folders."""
            return (
                bool(item.data(0, Qt.UserRole + 307))
                and str(item.data(0, Qt.UserRole + 301) or "").casefold()
                    in {"basic", "assembler"}
                and str(item.data(0, Qt.UserRole + 305) or "").casefold() == "c64"
                and item.parent() is not None
            )

''')
    replace(141607, 'if bool(item.data', '            if self._is_unsaved_c64_project_leaf(item):')
    replace(141627, 'if not bool(item.data', '            if not self._is_unsaved_c64_project_leaf(item):')
    replace(141931, 'if bool(item.data', '            if self._is_unsaved_c64_project_leaf(item):')
    replace(143080, 'if bool(item.data', '            if self._is_unsaved_c64_project_leaf(item):')

    # Context-menu targets were already wired to _project_new_pascal_leaf().
    # Only their incorrectly configured architecture entries change.
    replace(141879, '"unit", "pe32"',
            '                ("Neu:  MS Windows 64 Bit Unit", "unit", "pe64"),')
    replace(141889, '"module", "pe64"',
            '                ("Neu:  Module 32 Bit", "module", "pe32"),')

    # Share the existing main-window QSS rather than recreating QActions.
    # Styling happens each time the editor context menu is opened (theme safe).
    insert_before(12918, '''def _style_editor_context_menu(menu, editor=None):
    """Style an editor menu like the main menu without rebuilding its actions."""
    window = editor if isinstance(editor, QWidget) else menu.parentWidget()
    while isinstance(window, QWidget):
        if callable(getattr(window, "_green_beige_menu_stylesheet", None)):
            break
        window = window.parentWidget()
    else:
        window = next(
            (w for w in QApplication.topLevelWidgets()
             if callable(getattr(w, "_green_beige_menu_stylesheet", None))),
            None,
        )
    if window is None:
        return menu
    stylesheet = window._green_beige_menu_stylesheet()
    for popup in (menu, *menu.findChildren(QMenu)):
        popup.setObjectName("green_beige_popup_menu")
        popup.setAttribute(Qt.WA_StyledBackground, True)
        popup.setStyleSheet(stylesheet)
    return menu


''')

    # These are deliberately insertions, not replacements: the existing
    # signals, action identities, disabled states and shortcuts stay intact.
    menu_inserts = [
        (12922, '        _style_editor_context_menu(menu, editor)'),
        (6835, '        _style_editor_context_menu(menu, self)'),
        (13482, '        _style_editor_context_menu(menu, self)'),
        (58481, '            _style_editor_context_menu(menu, self)'),
        (58652, '            _style_editor_context_menu(menu, self)'),
        (64246, '            _style_editor_context_menu(standard_menu, self)'),
        (64352, '                _style_editor_context_menu(wrapper, self)'),
        (64361, '                _style_editor_context_menu(menu, self)'),
        (68608, '            _style_editor_context_menu(menu, self)'),
        (76826, '            _style_editor_context_menu(menu)'),
        (80140, '            _style_editor_context_menu(menu, widget)'),
        (80256, '            _style_editor_context_menu(menu, self)'),
        (80391, '            _style_editor_context_menu(menu)'),
        (80482, '            _style_editor_context_menu(menu)'),
        (83584, '            _style_editor_context_menu(menu, self)'),
        (85284, '            _style_editor_context_menu(menu, self)'),
        (87015, '            _style_editor_context_menu(menu, self)'),
        (91797, '            _style_editor_context_menu(menu, self)'),
        (103888, '            _style_editor_context_menu(menu, self)'),
        (144135, '            _style_editor_context_menu(menu, self)'),
    ]
    for line, code in menu_inserts:
        if not ('QMenu(' in original_lines[line - 2]
                or 'createStandardContextMenu' in original_lines[line - 2]
                or 'exec_(' in original_lines[line - 1]
                or '_translate_source_editor_context_menu' in original_lines[line - 2]):
            raise ValueError(f'Unexpected editor menu context at line {line}')
        insert_before(line, code)

    output_lines: list[str] = []
    for number, original in enumerate(original_lines, start=1):
        if number in inserts:
            output_lines.extend(inserts[number].split('\n'))
        if number in changes:
            if changes[number]:
                output_lines.extend(changes[number].split('\n'))
        else:
            output_lines.append(original)
    result = '\n'.join(output_lines)
    assert result.count('def _style_editor_context_menu(') == 1
    assert result.count('self._is_unsaved_c64_project_leaf(item)') == 4
    assert 'namespace, leaf_title = project_pascal_unit_tree_parts(' not in result
    ast.parse(result, filename=str(TARGET))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path.cwd(),
                        help='Root of the cloned Commodore_C64_DISM repository')
    parser.add_argument('--check', action='store_true', help='Validate without writing')
    args = parser.parse_args()
    file_path = (args.repo / TARGET).resolve()
    if not file_path.is_file():
        parser.error(f'Not found: {file_path}')
    raw = file_path.read_bytes()
    # Git on Windows can check out CRLF while the canonical Git blob uses LF.
    source_bytes = raw.replace(b'\r\n', b'\n')
    sha = git_blob_sha(source_bytes)
    if sha != BASE_BLOB:
        parser.error(f'Unexpected revision for {file_path}: {sha}; expected {BASE_BLOB}. No changes made.')
    try:
        text = source_bytes.decode('utf-8')
        modified = patch_text(text)
    except (UnicodeError, ValueError, AssertionError, SyntaxError) as exc:
        print(f'Patch validation failed, file left unchanged: {exc}', file=sys.stderr)
        return 1
    print(f'Validated {TARGET}, base blob {sha}, {modified.count(chr(10)) + 1} output lines')
    if args.check:
        print('Dry run: no files changed')
        return 0
    backup = file_path.with_name(file_path.name + '.before_pascal_menu_fix.bak')
    if backup.exists():
        parser.error(f'Backup already exists: {backup}; no files changed')
    backup.write_bytes(raw)
    try:
        output_bytes = modified.encode('utf-8')
        if b'\r\n' in raw:
            output_bytes = output_bytes.replace(b'\n', b'\r\n')
        file_path.write_bytes(output_bytes)
    except OSError:
        file_path.write_bytes(raw)
        raise
    print(f'Updated: {file_path}')
    print(f'Original copy: {backup}')
    print('Syntax checked by Python ast.parse(). GUI behavior must be tested under PyQt5.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
