# -*- coding: utf-8 -*-
"""Stage 520: building either resource DLL never rearranges the Qt workspace."""
from __future__ import annotations
import ast
import textwrap
from pathlib import Path
from types import SimpleNamespace
import pytest

SOURCE = Path(__file__).with_name("d64_dism.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
EDITOR = next(c for c in TREE.body
              if isinstance(c, ast.ClassDef) and c.name == "WindowsResourceEditorWidget")


def method(name, ns):
    node = next(n for n in EDITOR.body if isinstance(n, ast.FunctionDef) and n.name == name)
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    exec(compile(module, '<resource-editor>', 'exec'), ns)
    return ns[name]


@pytest.mark.parametrize("machine", ("x86", "x64"))
def test_dll_button_build_preserves_main_and_dock_geometry(machine, tmp_path):
    """Simulate the click with geometry checks and forbid every layout call."""
    calls = []
    ns = {
        "ResourceCompilerError": RuntimeError,
        "build_resource_dll_files": lambda path, entries, **options: (
            calls.append((path, tuple(entries), options))
            or (tmp_path / 'built.res', tmp_path / 'built.o', tmp_path / 'built.dll')),
    }
    build = method('compile_to_resource_dll', ns)
    resource = SimpleNamespace(type_id=10, codepage=65001)
    rc = tmp_path / 'Source.rc'
    rc.write_text('#pragma code_page(65001)\n100 RCDATA\nBEGIN\n"Hallo"\nEND\n', encoding='utf8')

    class Editor:
        current_path = rc
        compile_to_resource_dll = build
        current_target = 'pe64'
        def __init__(self):
            self.main_window_rect = (100, 100, 1100, 750)
            self.resource_dock_rect = (220, 140, 820, 540)
            self.splitter_widths = (250, 720)
            self.selected_tab = 'RC-Quelltext'
            self.entries = ['previous resource tree entry']
            self.messages = []
        def _selected_dll_codepage(self):
            return 65001
        def _resource_dll_source_entries(self):
            return [resource]
        def _resource_build_options(self, architecture, codepage):
            assert codepage == 65001
            return dict(include_native_utf16=False, compress_enabled=True,
                        compress_mode='custom')
        def _populate_tree(self, *args):
            raise AssertionError('The resource tree must not be rebuilt')
        def _compile_current_rc(self):
            raise AssertionError('The editor must use the independent compiler')
        def set_target(self, *args):
            raise AssertionError('Do not change the editor target during a DLL build')
        def _set_status(self, message):
            self.messages.append(message)
        def _critical(self, *args):
            raise AssertionError(args)

    widget = Editor()
    initial = (widget.main_window_rect, widget.resource_dock_rect,
               widget.splitter_widths, widget.selected_tab, widget.current_target,
               list(widget.entries))
    assert widget.compile_to_resource_dll(machine)
    assert (widget.main_window_rect, widget.resource_dock_rect,
            widget.splitter_widths, widget.selected_tab, widget.current_target,
            list(widget.entries)) == initial
    assert len(calls) == 1
    assert calls[0][-1]['machine'] == machine
    assert ('win32' if machine == 'x86' else 'win64') in widget.messages[-1]


def test_resource_dll_source_compiles_without_touching_tree(tmp_path):
    path = tmp_path / 'Resource.rc'
    path.write_text('test', encoding='utf8')
    calls=[]
    ns={'ResourceCompilerError':RuntimeError,
        'compile_rc': lambda source, include_dirs: calls.append((source,include_dirs)) or SimpleNamespace(entries=['new binary']),
        'read_res': lambda source: ['binary resource']}
    source_method=method('_resource_dll_source_entries',ns)

    class Editor:
        _resource_dll_source_entries=source_method
        current_path=path
        _dirty=True
        def save(self):
            self._dirty=False
            return True
        def _populate_tree(self):
            raise AssertionError('No tree rebuild during a DLL build')
    editor=Editor()
    assert editor._resource_dll_source_entries()==['new binary']
    assert calls==[(path,[tmp_path])]
    editor.current_path=tmp_path/'Resource.res'
    assert editor._resource_dll_source_entries()==['binary resource']


def test_long_status_and_path_do_not_set_minimum_dock_width():
    ui=SOURCE[SOURCE.index('    def _build_ui(self):', SOURCE.index('class WindowsResourceEditorWidget')):
              SOURCE.index('    def _show_resource_tree_context_menu', SOURCE.index('class WindowsResourceEditorWidget'))]
    assert 'self.status.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)' in ui
    assert 'self.status.setMinimumWidth(0)' in ui
    assert 'self.file_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)' in ui
    status=SOURCE[SOURCE.index('    def _set_status(self, text: str):', SOURCE.index('class WindowsResourceEditorWidget')):
                  SOURCE.index('    def _source_changed(self):', SOURCE.index('class WindowsResourceEditorWidget'))]
    assert 'elidedText' in status and 'self.status.setToolTip(text)' in status
    assert 'self.status_message.emit(text)' in status  # full status survives
