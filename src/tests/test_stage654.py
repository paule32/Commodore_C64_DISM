# -*- coding: utf-8 -*-
"""Stage 654: regressions for Turbo Help project click and dock-editor lifetime.

PyQt5 is not available in the automated test environment, so the two real
ExplorerWindow methods are tested with small Qt-like fakes extracted from AST.
"""
from __future__ import annotations

import ast
from pathlib import Path
import re
import sys
import types

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / 'd64_dism.py').read_text('utf-8')


def _methods():
    # Extract only the two actual methods; parsing the whole 150k-line GUI
    # for each test is unnecessarily expensive.
    import textwrap
    blocks = []
    for name in ('_turbo_help_active_editor', 'show_turbo_help_compiler_dock', '_project_turbo_help_open'):
        start = SOURCE.index(f'        def {name}(')
        end = SOURCE.find('\n        def ', start + 16)
        if end < 0:
            raise AssertionError(name)
        blocks.append(textwrap.dedent(SOURCE[start:end]))
    return compile('\n\n'.join(blocks), str(ROOT / 'd64_dism.py'), 'exec')


class Signal:
    def connect(self, callback):
        self.target = callback


class FakeTabs:
    def __init__(self):
        self.current = None

    def setCurrentWidget(self, editor):
        self.current = editor


class FakeTextEditor:
    def setFocus(self, *_args):
        self.focused = True


class FakeEditor:
    instances = []

    def __init__(self, path, parent):
        self.path = path
        self.parent = parent
        self.compiled = Signal()
        self.document_saved = Signal()
        self.editor = FakeTextEditor()
        self.tabs = FakeTabs()
        self.loaded = []
        self.project_sources = []
        self.use_project_list = False
        self.__class__.instances.append(self)

    def load_document(self, path):
        path = Path(path).resolve()
        if path not in self.loaded:
            self.loaded.append(path)
        return True


class FakeQt:
    UserRole = 100
    LeftDockWidgetArea = 1
    RightDockWidgetArea = 2
    TopDockWidgetArea = 4
    BottomDockWidgetArea = 8
    OtherFocusReason = 1


class FakeDock:
    def __init__(self, title, parent):
        self.title = title
        self.parent = parent
        self._widget = None
        self.visibilityChanged = Signal()
        self.calls = []

    def widget(self):
        return self._widget

    def setWidget(self, widget):
        self._widget = widget

    def setObjectName(self, *args):
        pass

    def setFeatures(self, *args):
        pass

    def setAllowedAreas(self, *args):
        pass

    def setMinimumSize(self, *args):
        pass

    def setSizePolicy(self, *args):
        pass

    def setTitleBarWidget(self, *args):
        pass

    def show(self):
        self.calls.append('show')

    def hide(self):
        self.calls.append('hide')

    def raise_(self):
        self.calls.append('raise')


class FakeItem:
    def __init__(self, path):
        self.path = path

    def data(self, column, role):
        return str(self.path) if role == FakeQt.UserRole + 302 else None


class FakeRoot:
    def __init__(self, paths):
        self.items = [FakeItem(p) for p in paths]

    def childCount(self):
        return len(self.items)

    def child(self, i):
        return self.items[i]


class FakeStatus:
    def showMessage(self, *_args):
        pass


class FakeMainWindow:
    def __init__(self, paths):
        self.project_turbo_help_root = FakeRoot(paths)
        self.current_project_path = str(paths[0])
        self._turbo_help_pending_leaves = {}
        self.added = []
        self.errors = []

    # Stage 655 introduced a project-name callback during editor setup.
    # Keep the Stage 654 GUI fixture compatible with that later API.
    def _turbo_help_project_executable(self):
        return Path(self.current_project_path).with_suffix('.exe')

    def _turbo_help_compiled(self, *_args):
        pass

    def _turbo_help_document_saved(self, *_args):
        pass

    def _dock_features(self):
        return 0

    def addDockWidget(self, *_args):
        self.added.append(_args[-1])

    def _exclusive_tool_workspace_visibility_changed(self, *_args):
        pass

    def _activate_exclusive_tool_workspace(self, *_args):
        pass

    def _expand_exclusive_tool_workspace(self, *_args):
        pass

    def statusBar(self):
        return FakeStatus()

    def show_error(self, title, message):
        self.errors.append((title, message))


def _bind(monkeypatch):
    fake_module = types.ModuleType('turbo_help_gui')
    fake_module.TurboHelpEditor = FakeEditor
    monkeypatch.setitem(sys.modules, 'turbo_help_gui', fake_module)
    namespace = {
        '__file__': str(ROOT / 'd64_dism.py'),
        'Path': Path,
        'Qt': FakeQt,
        'QDockWidget': FakeDock,
        'QSizePolicy': types.SimpleNamespace(Expanding=1),
        'DockTitleBar': lambda _dock: object(),
        'QTimer': types.SimpleNamespace(singleShot=lambda _ms, func: func()),
    }
    exec(_methods(), namespace)
    FakeMainWindow._turbo_help_active_editor = namespace['_turbo_help_active_editor']
    FakeMainWindow.show_turbo_help_compiler_dock = namespace['show_turbo_help_compiler_dock']
    FakeMainWindow._project_turbo_help_open = namespace['_project_turbo_help_open']
    FakeEditor.instances.clear()


def test_first_click_opens_dock_and_editor_without_existing_attrs(tmp_path, monkeypatch):
    _bind(monkeypatch)
    path = tmp_path / 'System.SysUtils.thlp'
    path.write_text('%topic "index"\nHello\n', encoding='utf-8')
    window = FakeMainWindow([path])
    assert not hasattr(window, 'turbo_help_compiler_editor')
    window._project_turbo_help_open(FakeItem(path))
    assert window.turbo_help_compiler_editor is FakeEditor.instances[0]
    assert window.turbo_help_compiler_dock.widget() is window.turbo_help_compiler_editor
    assert window.turbo_help_compiler_editor.loaded == [path]
    assert len(window.added) == 1
    window._project_turbo_help_open(FakeItem(path))
    assert len(FakeEditor.instances) == 1
    assert len(window.added) == 1
    assert window.turbo_help_compiler_editor.loaded == [path]


def test_existing_dock_without_editor_attr_recovers_editor_and_tabs(tmp_path, monkeypatch):
    _bind(monkeypatch)
    path = tmp_path / 'Help.thlp'
    path.write_text('%topic "index"\nOk\n', encoding='utf-8')
    window = FakeMainWindow([path])
    editor = FakeEditor(path, window)
    editor.loaded.append(path)
    dock = FakeDock('Hilfecompiler', window)
    dock.setWidget(editor)
    window.turbo_help_compiler_dock = dock
    assert not hasattr(window, 'turbo_help_compiler_editor')
    window._project_turbo_help_open(FakeItem(path))
    assert window.turbo_help_compiler_editor is editor
    assert dock.widget() is editor
    assert len(FakeEditor.instances) == 1
    assert len(window.added) == 0


def test_existing_dock_without_editor_recreates_editor(tmp_path, monkeypatch):
    _bind(monkeypatch)
    path = tmp_path / 'Help.thlp'
    path.write_text('%topic "index"\nOk\n', encoding='utf-8')
    window = FakeMainWindow([path])
    dock = FakeDock('Hilfecompiler', window)
    window.turbo_help_compiler_dock = dock
    window._project_turbo_help_open(FakeItem(path))
    assert isinstance(window.turbo_help_compiler_editor, FakeEditor)
    assert dock.widget() is window.turbo_help_compiler_editor


def test_missing_source_is_reported_without_opening_dock(tmp_path, monkeypatch):
    _bind(monkeypatch)
    path = tmp_path / 'NotFound.thlp'
    window = FakeMainWindow([path])
    window._project_turbo_help_open(FakeItem(path))
    assert window.errors and 'Hilfedatei fehlt' in window.errors[0][1]
    assert not FakeEditor.instances


def test_stage654_initialization_and_no_host():
    assert 'self.turbo_help_compiler_editor = None' in SOURCE
    assert 'self.turbo_help_compiler_dock = None' in SOURCE
    assert 'editor = self._turbo_help_active_editor()' in SOURCE
    assert 'if isinstance(dock_widget, TurboHelpEditor):' in SOURCE
    assert 'turbo_help_bridge_host' not in SOURCE
