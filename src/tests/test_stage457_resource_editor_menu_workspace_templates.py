# -*- coding: utf-8 -*-
"""Stage 457: dock workspace preservation, menu wiring and RC insertion."""
from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace
from typing import MutableMapping, Mapping, Sequence, Optional, Union, Iterable, Any, Dict, List, Tuple
import struct
import ast
import os
import sys
import tempfile
from dataclasses import dataclass, field
import textwrap

import pytest
from resource_rc_templates import rc_template, insertable_rc_template, RESOURCE_TEMPLATE_KINDS

SOURCE = Path(__file__).with_name("d64_dism.py").read_text(encoding="utf-8")


def _extract_method(name):
    indent = "        " if "        def " + name + "(" in SOURCE else "    "
    prefix = indent + "def " + name + "("
    start = SOURCE.index(prefix)
    end = SOURCE.find("\n" + indent + "def ", start + len(prefix))
    return textwrap.dedent(SOURCE[start:end if end > start else len(SOURCE)])


class FakeDock:
    def __init__(self, visible=False):
        self.visible = visible
        self.shown = 0
        self.hidden = 0

    def isVisible(self):
        return self.visible

    def hide(self):
        self.visible = False
        self.hidden += 1

    def show(self):
        self.visible = True
        self.shown += 1

    def raise_(self):
        pass


class FakeWorkspaceHost:
    def __init__(self):
        self._windows_resource_editor_workspace_active = False
        self._windows_resource_editor_hidden_docks = []
        self._windows_resource_editor_replaced_central_widget = False
        self.windows_resource_editor_dock = FakeDock(False)
        self.right_dock = FakeDock(True)
        self.bottom_dock = FakeDock(True)
        self.filesystem_dock = FakeDock(True)
        self.hidden_before = FakeDock(False)
        self._central = FakeDock(True)
        self._docks = [self.windows_resource_editor_dock, self.right_dock,
                       self.bottom_dock, self.filesystem_dock, self.hidden_before]

    def findChildren(self, cls):
        return self._docks

    def centralWidget(self):
        return self._central


def _workspace_functions():
    scope = {"QDockWidget": FakeDock}
    for name in ("_restore_windows_resource_editor_workspace", "_prepare_windows_resource_editor_workspace"):
        exec(_extract_method(name), scope)
    for name in ("_restore_windows_resource_editor_workspace", "_prepare_windows_resource_editor_workspace"):
        setattr(FakeWorkspaceHost, name, scope[name])


def test_resource_editor_workspace_preserves_project_information_only():
    _workspace_functions()
    host = FakeWorkspaceHost()
    host._prepare_windows_resource_editor_workspace(host.windows_resource_editor_dock)
    assert host.right_dock.isVisible()            # project / information
    assert not host.bottom_dock.isVisible()       # protocol must disappear
    assert not host.filesystem_dock.isVisible()
    assert not host.hidden_before.isVisible()
    assert not host.centralWidget().isVisible()
    assert host._windows_resource_editor_workspace_active
    host.windows_resource_editor_dock.show()
    host.windows_resource_editor_dock.hide()
    host._restore_windows_resource_editor_workspace()
    assert host.right_dock.isVisible() and host.right_dock.hidden == 0
    assert host.bottom_dock.isVisible()
    assert host.filesystem_dock.isVisible()
    assert host.centralWidget().isVisible()
    assert not host.hidden_before.isVisible()
    assert not host._windows_resource_editor_workspace_active
    assert host.filesystem_dock.shown == 1
    host._restore_windows_resource_editor_workspace()  # idempotent
    assert host.filesystem_dock.shown == 1


def test_hidden_project_information_not_spuriously_shown():
    _workspace_functions()
    host = FakeWorkspaceHost()
    host.right_dock.hide()
    host._prepare_windows_resource_editor_workspace(host.windows_resource_editor_dock)
    host._restore_windows_resource_editor_workspace()
    assert not host.right_dock.isVisible()


def test_menu_item_above_resource_builder_and_no_checked_bool_path():
    assert 'QAction("Resource Editor", self)' in SOURCE
    assert 'self.resource_editor_action.triggered.connect(\n                lambda _checked=False: self.show_windows_resource_editor()' in SOURCE
    assert SOURCE.index('tools_menu.addAction(self.resource_editor_action)') < SOURCE.index('tools_menu.addAction(self.resource_action)')
    assert '"Resource Builder", self' in SOURCE


def test_second_toolbar_contains_six_templates_below_compiler_buttons():
    editor = SOURCE[SOURCE.index('class WindowsResourceEditorWidget(QWidget):'):]
    assert editor.index('self.act_refresh = add_action') < editor.index('self.template_toolbar = QToolBar')
    assert editor.index('root.addWidget(self.template_toolbar)') < editor.index('info = QHBoxLayout()')
    for kind in RESOURCE_TEMPLATE_KINDS:
        assert kind in editor
    assert 'lambda _checked=False, resource_kind=label: self.insert_resource_template(resource_kind)' in editor
    assert 'if self.source_edit.isReadOnly():' in editor


@pytest.mark.parametrize('kind', RESOURCE_TEMPLATE_KINDS)
def test_every_button_has_real_source_template(kind):
    snippet = rc_template(kind)
    assert snippet.endswith('\n') and len(snippet.strip()) > 15
    assert kind.upper() in snippet.upper() or kind == 'Text'


def test_dialog_id_generation_and_non_destructive_insertion():
    dialog = rc_template('Dialog')
    assert 'DIALOGEX' in dialog and 'CAPTION "Neuer Dialog"' in dialog
    assert 'DEFPUSHBUTTON' in dialog and 'PUSHBUTTON' in dialog
    assert 'FONT' in dialog and 'BEGIN' in dialog and 'END' in dialog
    next_dialog = rc_template('Dialog', dialog)
    assert 'IDD_DIALOG_2 ' in next_dialog
    existing = '// Mein RC-Quelltext\n'
    snippet = insertable_rc_template('Dialog', existing, len(existing))
    assert (existing + snippet).startswith(existing)
    assert 'IDD_DIALOG_1' in snippet
    assert insertable_rc_template('Text', '', 0).startswith('// Text-')
    assert '2002 "Neuer Text"' in rc_template('Text', rc_template('Text'))
    with pytest.raises(ValueError):
        rc_template('NichtVorhanden')


def test_dialog_and_text_template_compile_in_real_internal_rc_parser(tmp_path):
    # Reuse the pure RC compiler already shipped in d64_dism.py, without
    # importing PyQt5 (the CI environment has no native Qt5 runtime).
    source_lines = SOURCE.splitlines(keepends=True)
    start_constants = SOURCE.index('RT_CURSOR       = 1')
    end_constants = SOURCE.index('\n# ---------------------------------------------------------------------------\n# Projektdateien', start_constants)
    start_parser = SOURCE.index('class ResourceCompilerError(Exception):')
    end_parser = SOURCE.index('def resource_dialog_stylesheet', start_parser)
    globals_ = {
        'os': os, 'sys': sys, 're': re, 'struct': struct, 'ast': ast,
        'Path': Path, 'dataclass': dataclass, 'field': field,
        'Union': Union, 'Optional': Optional, 'MutableMapping': MutableMapping,
        'Mapping': Mapping, 'Sequence': Sequence, 'Iterable': Iterable,
        'Any': Any, 'Dict': Dict, 'List': List, 'Tuple': Tuple,
    }
    exec(SOURCE[start_constants:end_constants], globals_)
    exec(SOURCE[start_parser:end_parser], globals_)
    path = tmp_path / 'vorlagen.rc'
    path.write_text(rc_template('Dialog') + '\n' + rc_template('Text'), encoding='utf-8')
    entries = globals_['compile_rc'](path).entries
    assert any(entry.type_id == globals_['RT_DIALOG'] and len(entry.data) > 40 for entry in entries)
    assert any(entry.type_id == globals_['RT_STRING'] for entry in entries)


class _FakeCursor:
    def __init__(self, editor):
        self.editor = editor
        self.pos = len(editor.value)
        self.selected = None
    def position(self): return self.pos
    def hasSelection(self): return self.selected is not None
    def selectionStart(self): return self.selected[0] if self.selected else self.pos
    def removeSelectedText(self):
        a,b = self.selected
        self.editor.value = self.editor.value[:a] + self.editor.value[b:]
        self.pos = a
        self.selected = None
    def insertText(self, text):
        self.editor.value = self.editor.value[:self.pos] + text + self.editor.value[self.pos:]
        self.pos += len(text)


class _FakeRCEditor:
    def __init__(self, value='', readonly=False):
        self.value = value
        self.readonly = readonly
        self.cursor = _FakeCursor(self)
        self.focused = False
    def isReadOnly(self): return self.readonly
    def textCursor(self): return self.cursor
    def toPlainText(self): return self.value
    def setTextCursor(self, cursor): self.cursor = cursor
    def setFocus(self, reason): self.focused = True


def test_template_button_insertion_into_editor_and_readonly_protection():
    namespace = {'Qt': SimpleNamespace(OtherFocusReason=9)}
    exec(_extract_method('insert_resource_template'), namespace)
    method = namespace['insert_resource_template']
    class Host:
        insert_resource_template = method
        def __init__(self, source, readonly=False):
            self.source_edit = _FakeRCEditor(source, readonly)
            self.tabs = SimpleNamespace(setCurrentIndex=lambda index: setattr(self, 'tab', index))
            self._dirty = False
            self.messages = []
        def _set_status(self, message): self.messages.append(message)
        def _warning(self, title, message): self.messages.append(title + ':' + message)
    editor = Host('STRINGTABLE\nBEGIN\n  20 "Vorhanden"\nEND\n')
    assert editor.insert_resource_template('Dialog') is True
    assert editor.source_edit.value.startswith('STRINGTABLE')
    assert 'IDD_DIALOG_1 DIALOGEX' in editor.source_edit.value
    assert editor.source_edit.focused and editor._dirty and editor.tab == 0
    # Repetition uses a distinct RC symbol.
    assert editor.insert_resource_template('Dialog') is True
    assert 'IDD_DIALOG_2 DIALOGEX' in editor.source_edit.value
    binary = Host('// .res read-only', readonly=True)
    assert binary.insert_resource_template('Dialog') is False
    assert binary.source_edit.value == '// .res read-only'
    assert binary.messages[0].startswith('Resourcen-Editor:')


def test_rcdata_template_compiles_with_internal_resource_parser(tmp_path):
    source = SOURCE
    a = source.index('RT_CURSOR       = 1')
    b = source.index('\n# ---------------------------------------------------------------------------\n# Projektdateien', a)
    c = source.index('class ResourceCompilerError(Exception):')
    d = source.index('def resource_dialog_stylesheet', c)
    scope = {'os': os, 'sys': sys, 're': re, 'struct': struct, 'ast': ast,
             'Path': Path, 'dataclass': dataclass, 'field': field,
             'Union': Union, 'Optional': Optional, 'MutableMapping': MutableMapping,
             'Mapping': Mapping, 'Sequence': Sequence, 'Iterable': Iterable,
             'Any': Any, 'Dict': Dict, 'List': List, 'Tuple': Tuple}
    exec(source[a:b], scope)
    exec(source[c:d], scope)
    path = tmp_path / 'data.rc'
    path.write_text(rc_template('RCDATA'), encoding='utf8')
    result = scope['compile_rc'](path)
    assert len(result.entries) == 1
    entry = result.entries[0]
    assert entry.type_id == scope['RT_RCDATA']
    assert entry.data == struct.pack('<3H', 1, 2, 3)
