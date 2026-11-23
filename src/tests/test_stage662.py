# -*- coding: utf-8 -*-
"""Stage 662: project leaf lazy tabs, save-before-switch, focus and cancel safety.

The tests use actual TurboHelpEditor methods extracted from their Python AST;
Qt5 widgets are simulated because the CI container has no PyQt5 runtime.
"""
from pathlib import Path
from types import SimpleNamespace
import ast
import textwrap

import pytest
import test_stage654 as project_support

ROOT = Path(__file__).parent
MAIN = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
GUI = (ROOT / 'turbo_help_gui.py').read_text(encoding='utf-8')


class Signal:
    def __init__(self):
        self.callbacks = []
        self.emitted = []
    def connect(self, callback):
        self.callbacks.append(callback)
    def emit(self, *args):
        self.emitted.append(args)
        for callback in self.callbacks:
            callback(*args)


class Doc:
    def __init__(self):
        self.modified = False
    def isModified(self):
        return self.modified
    def setModified(self, value):
        self.modified = value


class Edit:
    def __init__(self, text, path=None):
        self._thlp_path = Path(path).resolve() if path else None
        self.content = text
        self.doc = Doc()
        self.focused = False
        self.deleted = False
    def document(self):
        return self.doc
    def toPlainText(self):
        return self.content
    def setFocus(self, *args):
        self.focused = True
    def deleteLater(self):
        self.deleted = True


class Tabs:
    def __init__(self):
        self.pages = []
        self.active = -1
        self.currentChanged = Signal()
    def count(self):
        return len(self.pages)
    def widget(self, index):
        return self.pages[index]
    def indexOf(self, widget):
        try:
            return self.pages.index(widget)
        except ValueError:
            return -1
    def currentWidget(self):
        return self.pages[self.active] if 0 <= self.active < len(self.pages) else None
    def addTab(self, edit, _title):
        self.pages.append(edit)
        if self.active < 0:
            self.setCurrentIndex(0)
        return len(self.pages) - 1
    def removeTab(self, index):
        self.pages.pop(index)
        if not self.pages:
            self.setCurrentIndex(-1)
        elif self.active >= len(self.pages):
            self.setCurrentIndex(len(self.pages)-1)
        elif index < self.active:
            self.active -= 1
        else:
            self.currentChanged.emit(self.active)
    def setCurrentIndex(self, index):
        if index != self.active:
            self.active = index
            self.currentChanged.emit(index)
    def setCurrentWidget(self, widget):
        index = self.indexOf(widget)
        if index >= 0:
            self.setCurrentIndex(index)


class Dialogs:
    save_answers = []
    errors = []
    @classmethod
    def getSaveFileName(cls, *_args):
        return (cls.save_answers.pop(0) if cls.save_answers else '', '')
    @classmethod
    def warning(cls, *args):
        cls.errors.append(args)
    @classmethod
    def critical(cls, *args):
        cls.errors.append(args)


class Harness:
    def __init__(self):
        self.tabs = Tabs()
        self.editor = None
        self.source_path = None
        self._active_tab = None
        self._tab_switch_lock = False
        self.status_label = SimpleNamespace(setText=lambda _t: None)
        self.document_saved = Signal()
        self.tabs.currentChanged.connect(self._sync_current)
    def _append_tab(self, text, path=None):
        edit = Edit(text, path)
        self.tabs.addTab(edit, '')
        self.tabs.setCurrentWidget(edit)
        edit.setFocus()
        return edit
    def _refresh_tab(self, edit):
        pass


def attach_gui_methods():
    source_tree = ast.parse(GUI)
    class_tree = next(node for node in source_tree.body if isinstance(node, ast.ClassDef)
                      and node.name == 'TurboHelpEditor')
    methods = ['_path_for', '_current_editor', '_save_changes_before_switch',
               '_sync_current', '_save_edit', 'load_document', 'new_document']
    code = '\n'.join(ast.get_source_segment(GUI, node) for node in class_tree.body
                     if isinstance(node, ast.FunctionDef) and node.name in methods)
    namespace = {
        'Path': Path,
        'Qt': SimpleNamespace(OtherFocusReason=5),
        'QFileDialog': Dialogs,
        'QMessageBox': Dialogs,
        'DEFAULT_SOURCE': '%topic "index"\nStart\n',
    }
    exec(compile(textwrap.dedent(code), 'turbo_help_gui.py', 'exec'), namespace)
    for name in methods:
        setattr(Harness, name, namespace[name])


attach_gui_methods()


@pytest.fixture(autouse=True)
def reset_dialogs():
    Dialogs.save_answers.clear()
    Dialogs.errors.clear()


def test_first_leaf_click_only_loads_that_file_not_all_project_sources(tmp_path, monkeypatch):
    project_support._bind(monkeypatch)
    paths = [tmp_path / f'{name}.thlp' for name in ('A', 'B', 'C')]
    for path in paths:
        path.write_text('%topic "index"\nTest\n', encoding='utf-8')
    window = project_support.FakeMainWindow(paths)
    window._project_turbo_help_open(project_support.FakeItem(paths[1]))
    assert len(project_support.FakeEditor.instances) == 1
    editor = window.turbo_help_compiler_editor
    assert editor.loaded == [paths[1]]
    assert editor.project_sources == paths
    window._project_turbo_help_open(project_support.FakeItem(paths[2]))
    assert editor.loaded == [paths[1], paths[2]]
    window._project_turbo_help_open(project_support.FakeItem(paths[1]))
    assert editor.loaded == [paths[1], paths[2]]
    assert len(project_support.FakeEditor.instances) == 1


def test_switch_open_documents_saves_modified_content_before_focus(tmp_path):
    first, second = tmp_path / 'first.thlp', tmp_path / 'second.thlp'
    first.write_text('%topic "index"\nErst\n', encoding='utf-8')
    second.write_text('%topic "zwei"\nZweit\n', encoding='utf-8')
    h = Harness()
    assert h.load_document(first)
    first_edit = h.editor
    assert h.load_document(second)
    second_edit = h.editor
    h.tabs.setCurrentWidget(first_edit)
    first_edit.content = '%topic "index"\nGeändert\n'
    first_edit.doc.setModified(True)
    assert h.load_document(second)
    assert first.read_text(encoding='utf-8') == first_edit.content
    assert h.editor is second_edit and second_edit.focused
    assert h.source_path == second.resolve()
    assert len(h.document_saved.emitted) == 1
    assert not first_edit.document().isModified()


def test_mouse_tab_click_saves_previous_dirty_editor(tmp_path):
    paths = [tmp_path / f'{i}.thlp' for i in range(2)]
    for path in paths:
        path.write_text('%topic "index"\nText\n', encoding='utf-8')
    h = Harness()
    assert h.load_document(paths[0])
    edit0 = h.editor
    assert h.load_document(paths[1])
    edit1 = h.editor
    edit1.content += 'Neue Zeile\n'
    edit1.doc.setModified(True)
    h.tabs.setCurrentWidget(edit0)  # QTabWidget.currentChanged fires here
    assert paths[1].read_text(encoding='utf-8').endswith('Neue Zeile\n')
    assert h.editor is edit0 and edit0.focused


def test_failed_save_as_cancels_project_leaf_switch(tmp_path):
    target = tmp_path / 'target.thlp'
    target.write_text('%topic "index"\nTarget\n', encoding='utf-8')
    h = Harness()
    unsaved = h.new_document()
    unsaved.content += 'noch nicht gespeichert'
    unsaved.doc.setModified(True)
    Dialogs.save_answers = ['']
    assert not h.load_document(target)
    assert h.tabs.count() == 1
    assert h.editor is unsaved and h.tabs.currentWidget() is unsaved
    assert h.source_path is None


def test_failed_save_as_rolls_back_mouse_tab_switch(tmp_path):
    target = tmp_path / 'target.thlp'
    target.write_text('%topic "index"\nTarget\n', encoding='utf-8')
    h = Harness()
    assert h.load_document(target)
    target_edit = h.editor
    unsaved = h.new_document()
    unsaved.doc.setModified(True)
    Dialogs.save_answers = ['']
    h.tabs.setCurrentWidget(target_edit)
    assert h.editor is unsaved and h.tabs.currentWidget() is unsaved
    assert unsaved.focused and unsaved.doc.isModified()


def test_first_save_as_on_tab_switch_assigns_thlp_path_and_persists(tmp_path):
    target = tmp_path / 'second.thlp'
    target.write_text('%topic "second"\nAndere Quelle\n', encoding='utf-8')
    h = Harness()
    first_edit = h.new_document()
    first_edit.doc.setModified(True)
    dest = tmp_path / 'saved.thlp'
    Dialogs.save_answers = [str(dest)]
    assert h.load_document(target)
    assert dest.read_text(encoding='utf-8') == first_edit.content
    assert h.tabs.count() == 2
    assert h._path_for(first_edit) == dest.resolve()
    assert h.editor is h.tabs.currentWidget() and h.source_path == target.resolve()


def test_no_unrequested_autoload_and_editor_api_fallback():
    assert 'for path in editor.project_sources:' not in MAIN[
        MAIN.index('        def show_turbo_help_compiler_dock('):
        MAIN.index('        def _turbo_help_project_executable(')]
    assert 'editor = TurboHelpEditor(None, self)' in MAIN
    assert 'callable(getattr(candidate, "load_document", None))' in MAIN
    assert 'self._save_changes_before_switch()' in GUI
