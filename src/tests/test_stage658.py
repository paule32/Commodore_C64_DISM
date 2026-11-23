# -*- coding: utf-8 -*-
"""Stage 658: clicking a Turbo Help leaf must never use a bool as editor."""
from pathlib import Path
import test_stage654 as support


def test_leaf_click_after_bool_return_from_dock_launcher(tmp_path, monkeypatch):
    support._bind(monkeypatch)
    path = tmp_path / "Kapitel.thlp"
    path.write_text('%topic "index"\nHallo\n', encoding='utf-8')
    window = support.FakeMainWindow([path])
    actual_launcher = window.show_turbo_help_compiler_dock

    def bool_return_launcher():
        actual_launcher()  # creates/activates real editor but returns Qt boolean
        return True

    window.show_turbo_help_compiler_dock = bool_return_launcher
    window._project_turbo_help_open(support.FakeItem(path))
    editor = window.turbo_help_compiler_editor
    assert isinstance(editor, support.FakeEditor)
    assert editor.loaded == [path]
    assert window.errors == []


def test_stale_bool_editor_reference_recovers_real_dock_widget(tmp_path, monkeypatch):
    support._bind(monkeypatch)
    path = tmp_path / "Kapitel.thlp"
    path.write_text('%topic "index"\nHallo\n', encoding='utf-8')
    window = support.FakeMainWindow([path])
    actual_launcher = window.show_turbo_help_compiler_dock
    actual_launcher()
    previous = window.turbo_help_compiler_editor
    window.turbo_help_compiler_editor = True

    def bool_return_launcher():
        actual_launcher()
        return False

    window.show_turbo_help_compiler_dock = bool_return_launcher
    window._project_turbo_help_open(support.FakeItem(path))
    assert window.turbo_help_compiler_editor is previous
    assert previous.loaded == [path]
    assert len(support.FakeEditor.instances) == 1
    assert window.errors == []


def test_bool_launcher_without_editor_reports_error_instead_of_exception(tmp_path, monkeypatch):
    support._bind(monkeypatch)
    path = tmp_path / "Kapitel.thlp"
    path.write_text('%topic "index"\nHallo\n', encoding='utf-8')
    window = support.FakeMainWindow([path])
    window.show_turbo_help_compiler_dock = lambda: True
    window._project_turbo_help_open(support.FakeItem(path))
    assert len(window.errors) == 1
    assert "Editor" in window.errors[0][1]


def test_bool_launcher_with_existing_pending_tab_activates_it(tmp_path, monkeypatch):
    support._bind(monkeypatch)
    path = tmp_path / "Kapitel.thlp"
    path.write_text('%topic "index"\nHallo\n', encoding='utf-8')
    window = support.FakeMainWindow([path])
    window.show_turbo_help_compiler_dock()
    editor = window.turbo_help_compiler_editor
    existing_tab = support.FakeTextEditor()
    leaf = support.FakeItem(None)
    # FakeItem returns a string; simulate an unsaved leaf without data path.
    leaf.data = lambda _col, _role: None
    window._turbo_help_pending_leaves[existing_tab] = leaf
    window.show_turbo_help_compiler_dock = lambda: True
    window._project_turbo_help_open(leaf)
    assert editor.tabs.current is existing_tab
    assert existing_tab.focused
    assert window.errors == []


def test_bool_launcher_without_editor_prevents_new_document_crash(tmp_path, monkeypatch):
    support._bind(monkeypatch)
    window = support.FakeMainWindow([tmp_path / "Temp.thlp"])
    window.show_turbo_help_compiler_dock = lambda: False
    # Extract _project_turbo_help_new from production code.
    import textwrap
    source = (Path(__file__).resolve().parent / 'd64_dism.py').read_text('utf-8')
    start = source.index('        def _project_turbo_help_new(')
    end = source.index('\n        def ', start + 16)
    namespace = {}
    exec(compile(textwrap.dedent(source[start:end]), 'd64_dism.py', 'exec'), namespace)
    support.FakeMainWindow._project_turbo_help_new = namespace['_project_turbo_help_new']
    window._project_turbo_help_new()
    assert window.errors and 'Editor' in window.errors[0][1]
