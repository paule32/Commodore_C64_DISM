# -*- coding: utf-8 -*-
"""Stage 439: formula designer workspaces and global Edit menu without Qt installation."""
from __future__ import annotations
import json
from pathlib import Path
from types import SimpleNamespace
import textwrap

SOURCE = (Path(__file__).parent / 'd64_dism.py').read_text(encoding='utf-8')
FORMULA_MIME = 'application/x-d64-formula-node+json'


def _load_method(method, *, level, namespace):
    prefix = ' ' * level + 'def ' + method + '('
    start = SOURCE.index(prefix)
    end = SOURCE.find('\n' + ' ' * level + 'def ', start + len(prefix))
    code = SOURCE[start:end] if end >= 0 else SOURCE[start:]
    exec(textwrap.dedent(code), namespace)
    return namespace[method]


class FakeAction:
    def __init__(self):
        self.enabled = False
    def setEnabled(self, enabled):
        self.enabled = bool(enabled)


class FakeMime:
    def __init__(self, data=None, text=None):
        self._data = dict(data or {})
        self._text = text
    def hasFormat(self, mime):
        return mime in self._data
    def data(self, mime):
        return self._data[mime]
    def setData(self, mime, value):
        self._data[mime] = bytes(value)
    def setText(self, value):
        self._text = str(value)
    def hasText(self):
        return self._text is not None


class FakeClipboard:
    def __init__(self):
        self.mime = FakeMime()
    def mimeData(self):
        return self.mime
    def setMimeData(self, mime):
        self.mime = mime


class FakeEditor:
    def __init__(self):
        self.canvas = SimpleNamespace(selected_path=None)
        self.model = {'type': 'text', 'id': 'f1', 'text': 'x'}
        self._history = [self.model]
        self._history_index = 0
        self.editStateChanged = SimpleNamespace(emit=lambda: None)
        self.command_log = []
    def undo_formula(self): self.command_log.append('undo')
    def redo_formula(self): self.command_log.append('redo')
    def cut_selected_object(self): self.command_log.append('cut')
    def paste_selected_object(self): self.command_log.append('paste')


class FakeHost:
    def __init__(self, formula):
        self.formula = formula
        self.undo_action = FakeAction()
        self.redo_action = FakeAction()
        self.copy_action = FakeAction()
        self.cut_action = FakeAction()
        self.paste_action = FakeAction()
    def _active_formula_designer(self): return self.formula
    def _active_text_edit_widget(self): raise AssertionError('Must not dispatch to text editor')


def _fixture():
    clipboard = FakeClipboard()
    namespace = {
        'json': json,
        'QApplication': SimpleNamespace(clipboard=lambda: clipboard, beep=lambda: None),
        'FORMULA_DESIGNER_CLIPBOARD_MIME': FORMULA_MIME,
        'QMimeData': FakeMime,
        'QByteArray': bytes,
        '_formula_get_node_at_path': lambda model, path: model if path == ('focus',) else None,
        '_formula_validate_model': lambda node: None if isinstance(node, dict) and node.get('type') == 'text' else (_ for _ in ()).throw(ValueError('bad formula')),
        '_formula_to_text': lambda node: node['text'],
    }
    editor = FakeEditor()
    for name in ('_has_explicit_formula_selection', '_clipboard_has_formula', '_selected_node', '_selected_path', '_copy_selected_to_clipboard'):
        setattr(editor, name, _load_method(name, level=4, namespace=namespace).__get__(editor, FakeEditor))
    host = FakeHost(editor)
    edit_ns = {}
    for name in ('_update_edit_actions', '_run_current_text_command'):
        setattr(host, name, _load_method(name, level=8, namespace=edit_ns).__get__(host, FakeHost))
    return host, editor, clipboard


def test_initially_no_selection_no_history_actions_and_no_paste_for_plain_text():
    host, editor, clipboard = _fixture()
    clipboard.mime = FakeMime(text='ordinary text is not a formula')
    host._update_edit_actions()
    assert not any((host.undo_action.enabled, host.redo_action.enabled,
                    host.copy_action.enabled, host.cut_action.enabled,
                    host.paste_action.enabled))


def test_selected_formula_allows_copy_cut_but_not_plain_text_paste():
    host, editor, clipboard = _fixture()
    editor.canvas.selected_path = ('focus',)
    clipboard.mime = FakeMime(text='unrelated clipboard text')
    host._update_edit_actions()
    assert host.copy_action.enabled and host.cut_action.enabled
    assert not host.paste_action.enabled
    assert editor._copy_selected_to_clipboard() is True
    host._update_edit_actions()
    assert clipboard.mime.hasFormat(FORMULA_MIME)
    assert clipboard.mime.hasText()
    assert host.paste_action.enabled


def test_invalid_formula_mime_does_not_enable_paste_and_no_selection_disables_it():
    host, editor, clipboard = _fixture()
    editor.canvas.selected_path = ('focus',)
    clipboard.mime = FakeMime({FORMULA_MIME: b'{nonsense'})
    host._update_edit_actions()
    assert not host.paste_action.enabled
    clipboard.mime = FakeMime({FORMULA_MIME: b'{"type":"text","id":"v","text":"xy"}'})
    host._update_edit_actions()
    assert host.paste_action.enabled
    editor.canvas.selected_path = None
    host._update_edit_actions()
    assert not host.copy_action.enabled and not host.cut_action.enabled
    assert not host.paste_action.enabled


def test_undo_redo_follow_formula_history_not_text_widget():
    host, editor, _clipboard = _fixture()
    editor._history = [{'x': 1}, {'x': 2}, {'x': 3}]
    editor._history_index = 2
    host._update_edit_actions()
    assert host.undo_action.enabled and not host.redo_action.enabled
    editor._history_index = 1
    host._update_edit_actions()
    assert host.undo_action.enabled and host.redo_action.enabled
    editor._history_index = 0
    host._update_edit_actions()
    assert not host.undo_action.enabled and host.redo_action.enabled


def test_global_edit_menu_routes_to_formula_not_text_editor():
    host, editor, _clipboard = _fixture()
    editor.canvas.selected_path = ('focus',)
    for operation in ('undo', 'redo', 'cut', 'paste'):
        host._run_current_text_command(operation)
    assert editor.command_log == ['undo', 'redo', 'cut', 'paste']
    host._run_current_text_command('copy')
    assert host.paste_action.enabled


def test_formula_selection_does_not_get_created_implicitly_on_relayout():
    idx = SOURCE.index('    def refresh_layout(self):', SOURCE.index('class FormulaCanvasItem'))
    end = SOURCE.index('    def boundingRect(self):', idx)
    code = SOURCE[idx:end]
    assert 'if (self.selected_path is not None' in code
    assert 'self.selected_path = None' in code
    assert 'self.selected_path = _formula_find_path_for_leaf' not in code


def test_formula_entry_uses_same_exclusive_workspace_and_restores_on_close():
    idx = SOURCE.index('        def show_math_formula_designer_dock(self):')
    end = SOURCE.index('        def show_minesweeper_dock(self):', idx)
    code = SOURCE[idx:end]
    assert code.index('self._activate_exclusive_tool_workspace(dock)') < code.index('controller.show()')
    assert 'self._expand_exclusive_tool_workspace(dock)' in code
    assert 'dock.visibilityChanged.connect(self._formula_designer_visibility_changed)' in code
    assert 'dock.designer.editStateChanged.connect(self._update_edit_actions)' in code
    assert 'QApplication.clipboard().dataChanged.connect(self._update_edit_actions)' in code
    restore_start = SOURCE.index('        def _formula_designer_visibility_changed(self, visible):')
    restore_end = SOURCE.index('        def show_math_formula_designer_dock(self):', restore_start)
    assert 'self._exclusive_tool_workspace_visibility_changed(bool(visible), dock)' in SOURCE[restore_start:restore_end]
    assert 'dock.hide()  # Unsichtbar' in SOURCE
    assert 'self.main_window.resizeDocks([dock], [100000]' not in SOURCE


def test_keyboard_shortcuts_and_context_paste_require_formula_selection():
    key_start = SOURCE.index('    def keyPressEvent(self, event):', SOURCE.index('class FormulaCanvasItem'))
    key_stop = SOURCE.index('    def focusOutEvent(self, event):', key_start) if '    def focusOutEvent(self, event):' in SOURCE[key_start:] else key_start+6000
    assert 'if key == Qt.Key_C:' in SOURCE[key_start:key_start + 2800]
    assert 'paste_action.setEnabled(has_selection and self._clipboard_has_formula())' in SOURCE
    assert 'if not self._has_explicit_formula_selection() or not self._clipboard_has_formula()' in SOURCE
