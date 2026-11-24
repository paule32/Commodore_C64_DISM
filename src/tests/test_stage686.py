# -*- coding: utf-8 -*-
"""Stage 686 – GUI regression: Turbo Help leaf must not treat a bool as editor.

No PyQt5 runtime is required; the test invokes the actual project methods
using the established Stage-654 Qt substitutes.
"""
from pathlib import Path
from types import SimpleNamespace
import textwrap

import test_stage654 as support


def _bind_new_method():
    source = (Path(__file__).resolve().parent / 'd64_dism.py').read_text('utf-8')
    start = source.index('        def _project_turbo_help_new(')
    end = source.index('\n        def ', start + 16)
    ns = {
        'Path': Path,
        'PROJECT_NODE_TURBO_HELP_ROOT': 'root',
        'PROJECT_NODE_TURBO_HELP_FOLDER': 'folder',
        'QInputDialog': SimpleNamespace(getText=lambda *_args, **_kwargs: ('Kapitel.thlp', True)),
    }
    exec(compile(textwrap.dedent(source[start:end]), 'd64_dism.py', 'exec'), ns)
    support.FakeMainWindow._project_turbo_help_new = ns['_project_turbo_help_new']


def test_685_new_help_leaf_loads_file_even_when_dock_launcher_returns_bool(tmp_path, monkeypatch):
    support._bind(monkeypatch)
    _bind_new_method()
    window = support.FakeMainWindow([tmp_path / 'Other.thlp'])
    window._project_item_kind = lambda item: None
    window._turbo_help_root_directory = lambda **_kwargs: tmp_path
    window._turbo_help_file_items = lambda: iter(())
    window._add_project_turbo_help_file = lambda path, parent=None: support.FakeItem(path)
    window.project_tree = SimpleNamespace(setCurrentItem=lambda item: None)
    actual_launcher = window.show_turbo_help_compiler_dock

    def qt_slot_style_launcher():
        actual_launcher()
        return True

    window.show_turbo_help_compiler_dock = qt_slot_style_launcher
    window._project_turbo_help_new()
    path = tmp_path / 'Kapitel.thlp'
    assert path.is_file()
    assert len(support.FakeEditor.instances) == 1
    assert window.turbo_help_compiler_editor.loaded == [path]
    assert not window.errors


def test_685_missing_help_leaf_does_not_launch_dock(tmp_path, monkeypatch):
    support._bind(monkeypatch)
    window = support.FakeMainWindow([tmp_path / 'missing.thlp'])
    messages = []
    window._turbo_help_warning = messages.append
    window._project_turbo_help_open(support.FakeItem(tmp_path / 'missing.thlp'))
    assert len(messages) == 1 and 'Hilfedatei fehlt' in messages[0]
    assert not support.FakeEditor.instances


def test_685_bool_return_without_live_editor_fails_gracefully(tmp_path, monkeypatch):
    support._bind(monkeypatch)
    path = tmp_path / 'kapitel.thlp'
    path.write_text('%topic "index"\n', encoding='utf-8')
    window = support.FakeMainWindow([path])
    window.show_turbo_help_compiler_dock = lambda: False
    window._project_turbo_help_open(support.FakeItem(path))
    assert len(window.errors) == 1
    assert 'nicht verfügbar' in window.errors[0][1]
