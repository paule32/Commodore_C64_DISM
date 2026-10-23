"""Stage 483: German Qt editing context menus without changing Qt actions.

GUI event dispatch is also checked statically because PyQt5 is not installed on
this test host; the actual menu translation is exercised with fake QAction data.
"""
from __future__ import annotations

import ast
from pathlib import Path
import re

CODE = Path(__file__).with_name('d64_dism.py').read_text(encoding='utf-8')
TREE = ast.parse(CODE)


def _translator():
    source_map = next(
        node.value for node in TREE.body
        if isinstance(node, ast.Assign)
        and any(isinstance(item, ast.Name) and item.id == '_SOURCE_EDITOR_CONTEXT_TRANSLATIONS'
                for item in node.targets)
    )
    translations = ast.literal_eval(source_map)
    function_node = next(
        node for node in TREE.body if isinstance(node, ast.FunctionDef)
        and node.name == '_translate_source_editor_context_menu'
    )
    fragment = ast.Module(body=[function_node], type_ignores=[])
    scope = {'_SOURCE_EDITOR_CONTEXT_TRANSLATIONS': translations}
    exec(compile(ast.fix_missing_locations(fragment), '<stage483>', 'exec'), scope)
    return scope['_translate_source_editor_context_menu'], translations


class FakeAction:
    def __init__(self, label, *, separator=False, enabled=True):
        self._text = label
        self._separator = separator
        self._enabled = enabled
        self.triggered = object()
        self.shortcut = object()

    def text(self):
        return self._text

    def setText(self, value):
        self._text = value

    def isSeparator(self):
        return self._separator

    def isEnabled(self):
        return self._enabled


class FakeMenu:
    def __init__(self, actions):
        self._actions = actions

    def actions(self):
        return self._actions


def _qt_menu():
    return FakeMenu([
        FakeAction('&Undo\tCtrl+Z', enabled=False),
        FakeAction('&Redo\tCtrl+Y', enabled=True),
        FakeAction('', separator=True),
        FakeAction('Cu&t\tCtrl+X', enabled=False),
        FakeAction('&Copy\tCtrl+C'),
        FakeAction('&Paste\tCtrl+V'),
        FakeAction('&Delete'),
        FakeAction('', separator=True),
        FakeAction('Select &All\tCtrl+A'),
    ])


def test_all_eight_menu_slots_german_in_requested_order():
    translate, _ = _translator()
    menu = _qt_menu()
    translate(menu)
    assert [a.text() for a in menu.actions()] == [
        'Rückgängig\tSTRG + Z',
        'Wiederherstellen\tSTRG + Y',
        '',
        'Ausschneiden\tSTRG + X',
        'Kopieren\tSTRG + C',
        'Einfügen\tSTRG + V',
        'Löschen',
        '',
        'Alles markieren\tSTRG + A',
    ]


def test_preserves_qt_action_identity_enabled_state_shortcuts_and_separators():
    translate, _ = _translator()
    menu = _qt_menu()
    before = [(id(a), a.triggered, a.shortcut, a.isEnabled(), a.isSeparator())
              for a in menu.actions()]
    translate(menu)
    assert [(id(a), a.triggered, a.shortcut, a.isEnabled(), a.isSeparator())
            for a in menu.actions()] == before


def test_only_known_qt_actions_are_translated():
    translate, _ = _translator()
    menu = FakeMenu([FakeAction('Insert Unicode Control Character'), FakeAction('Undo...')])
    translate(menu)
    assert [a.text() for a in menu.actions()] == [
        'Insert Unicode Control Character', 'Rückgängig\tSTRG + Z'
    ]


def test_core_labels_use_requested_german_wording():
    _, values = _translator()
    assert set(values) == {'undo', 'redo', 'cut', 'copy', 'paste', 'delete', 'select all'}
    assert values['select all'][0] == 'Alles markieren'
    assert values['delete'] == ('Löschen', '')


def test_standard_qlineedit_context_menu_is_translated_globally():
    # Restrict the probe to ExplorerWindow's final application event filter.
    body = CODE.rsplit('        def eventFilter(self, watched, event):', 1)[1]
    body = body.split('            # Stage 467:', 1)[0]
    assert 'event.type() == QEvent.ContextMenu' in body
    assert 'isinstance(watched, QLineEdit)' in body
    assert 'watched.contextMenuPolicy() == Qt.DefaultContextMenu' in body
    assert '_execute_german_source_editor_context_menu(' in body
    assert 'event.globalPos()' in body
    assert 'event.accept()' in body and 'return True' in body
    assert 'application.installEventFilter(self)' in CODE


def test_special_qt_context_menus_are_preserved():
    assert 'watched.contextMenuPolicy() == Qt.DefaultContextMenu' in CODE
    assert 'line_edit.setContextMenuPolicy(Qt.CustomContextMenu)' in CODE
    # SourceTextEdit custom menus (including ASM `%include`) must remain intact.
    assert 'def _assembler_operand_context_at_point' in CODE
    assert 'operand_context = self._assembler_operand_context_at_point(event.pos())' in CODE


def test_dbf_grid_editor_menu_uses_same_select_all_translation():
    assert '"select all": "Alles markieren"' in CODE
    assert '_dbase_install_grid_editor_context_menu(editor)' in CODE


def test_existing_editing_keyboard_logic_not_replaced():
    assert 'action.setText(translated' in CODE
    assert 'menu = editor.createStandardContextMenu()' in CODE
    assert 'self._dbase_form_save_all_editors()' in CODE
