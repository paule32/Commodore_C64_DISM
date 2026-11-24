# -*- coding: utf-8 -*-
"""Stage 690: Turbo Help tab close asks before saving, with safe discard.

Qt-free tests execute the actual close_document method from turbo_help_gui.py
against the existing Stage 662 tab/file stubs. They do not claim a native
Windows UI smoke test.
"""
import ast
from pathlib import Path

import pytest
from test_stage662 import Harness, Edit, Dialogs

# Stage 662 extracts Qt methods with an incomplete stand-in namespace.
# Supply the missing Qt editor class to its shared function globals.
Harness._sync_current.__globals__['TurboHelpSourceEditor'] = Edit

SOURCE = (Path(__file__).parent / 'turbo_help_gui.py').read_text(encoding='utf-8')
TREE = ast.parse(SOURCE)
EDITOR_CLASS = next(n for n in TREE.body if isinstance(n, ast.ClassDef)
                    and n.name == 'TurboHelpEditor')
CLOSE_NODE = next(n for n in EDITOR_CLASS.body if isinstance(n, ast.FunctionDef)
                  and n.name == 'close_document')

class MessageBox:
    Question, Yes, No, Cancel = 101, 102, 103, 104

class Prompt:
    def __init__(self, answer):
        self.answer = answer
        self.buttons = None
        self.default = None
        self.exec_count = 0
    def setStandardButtons(self, buttons):
        self.buttons = buttons
    def setDefaultButton(self, button):
        self.default = button
    def exec_(self):
        self.exec_count += 1
        return self.answer

ns = {'QMessageBox': MessageBox, 'TurboHelpSourceEditor': Edit}
module = ast.Module(body=[CLOSE_NODE], type_ignores=[])
ast.fix_missing_locations(module)
exec(compile(module, 'turbo_help_gui.py', 'exec'), ns)
Harness.close_document = ns['close_document']


def with_answer(h, answer):
    prompt = Prompt(answer)
    requests = []
    def box(icon, title, text):
        requests.append((icon, title, text))
        return prompt
    h._help_message_box = box
    return prompt, requests


@pytest.fixture(autouse=True)
def reset_dialogs():
    Dialogs.save_answers.clear()
    Dialogs.errors.clear()


def test_first_untouched_tab_discard_while_settings_active(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    h = Harness()
    blank = h.new_document()
    settings = object()  # root-click creates a non-source Settings tab
    h.tabs.addTab(settings, 'Settings')
    h.tabs.setCurrentWidget(settings)
    assert h._path_for(blank) is None
    assert not blank.document().isModified()
    prompt, requests = with_answer(h, MessageBox.No)
    assert h.close_document(blank)
    assert h.tabs.pages == [settings]
    assert blank.deleted
    assert h.tabs.currentWidget() is settings
    assert list(tmp_path.glob('*.thlp')) == []
    assert h.document_saved.emitted == []
    assert requests[0][0] == MessageBox.Question
    assert 'Unbenannt.thlp' in requests[0][2]
    assert prompt.buttons == (MessageBox.Yes | MessageBox.No | MessageBox.Cancel)
    assert prompt.default == MessageBox.Cancel
    assert prompt.exec_count == 1


def test_yes_saves_new_file_before_closing(tmp_path):
    h = Harness()
    blank = h.new_document()
    blank.content = '%topic "intro"\nBeispiel\n'
    path = tmp_path / 'intro.thlp'
    Dialogs.save_answers = [str(path)]
    prompt, _ = with_answer(h, MessageBox.Yes)
    assert h.close_document(blank)
    assert path.read_text(encoding='utf-8') == blank.content
    assert blank.deleted and h.tabs.count() == 0
    assert len(h.document_saved.emitted) == 1
    assert prompt.exec_count == 1


def test_no_discards_modified_existing_document_without_overwriting(tmp_path):
    path = tmp_path / 'original.thlp'
    original = '%topic "hello"\nOriginal\n'
    path.write_text(original, encoding='utf-8')
    h = Harness()
    assert h.load_document(path)
    edit = h.editor
    edit.content = '%topic "hello"\nChanged\n'
    edit.doc.setModified(True)
    with_answer(h, MessageBox.No)
    assert h.close_document(edit)
    assert path.read_text(encoding='utf-8') == original
    assert edit.deleted and h.tabs.count() == 0
    assert h.document_saved.emitted == []


@pytest.mark.parametrize('answer', [MessageBox.Cancel, 0])
def test_cancel_or_window_close_keeps_unnamed_tab(answer):
    h = Harness()
    blank = h.new_document()
    with_answer(h, answer)
    assert not h.close_document(blank)
    assert h.tabs.currentWidget() is blank
    assert h.tabs.count() == 1 and not blank.deleted
    assert h._path_for(blank) is None


def test_yes_but_canceled_save_as_keeps_tab():
    h = Harness()
    blank = h.new_document()
    Dialogs.save_answers = ['']
    with_answer(h, MessageBox.Yes)
    assert not h.close_document(blank)
    assert h.tabs.count() == 1 and not blank.deleted
    assert h.document_saved.emitted == []


def test_unmodified_existing_file_closes_without_prompt(tmp_path):
    path = tmp_path / 'saved.thlp'
    path.write_text('%topic "index"\n', encoding='utf-8')
    h = Harness()
    assert h.load_document(path)
    edit = h.editor
    def unexpected(*_args):
        raise AssertionError('Unmodified saved files must close without questions')
    h._help_message_box = unexpected
    assert h.close_document(edit)
    assert edit.deleted and h.tabs.count() == 0


def test_closing_active_modified_tab_does_not_trigger_save_before_switch(tmp_path):
    p1, p2 = tmp_path / 'first.thlp', tmp_path / 'second.thlp'
    p1.write_text('%topic "one"\n', encoding='utf-8')
    p2.write_text('%topic "two"\n', encoding='utf-8')
    h = Harness()
    assert h.load_document(p1)
    first = h.editor
    assert h.load_document(p2)
    second = h.editor
    second.content += 'unsaved change\n'
    second.document().setModified(True)
    with_answer(h, MessageBox.No)
    assert h.close_document(second)
    assert p2.read_text(encoding='utf-8') == '%topic "two"\n'
    assert h.tabs.currentWidget() is first
    assert h.editor is first
    assert len(h.document_saved.emitted) == 0


def test_close_button_tooltip_mentions_confirmation():
    assert 'Tab schließen (bei Änderungen mit Speicherrückfrage)' in SOURCE
    assert 'prompt = self._help_message_box(' in SOURCE
