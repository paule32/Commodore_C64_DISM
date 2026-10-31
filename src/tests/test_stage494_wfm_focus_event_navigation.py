"""Stage 494: designer events, focus renaming, double-click navigation.

Qt is not available in CI, so GUI instance methods are extracted and exercised
with small widget doubles; helper functions are tested directly.
"""
import ast
from functools import lru_cache
from pathlib import Path
import re
from types import SimpleNamespace

import pytest

from d64dbase.form_event_handlers import (
    find_event_procedure_offset, normalized_focus_events, resolve_event_procedure,
)
from d64dbase.wfm import DBaseWfmMethod

SOURCE = Path(__file__).with_name('d64_dism.py').read_text('utf-8')


@lru_cache(None)
def _method_tree():
    return ast.parse(SOURCE)

def method_for(name):
    tree = _method_tree()
    nodes = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    assert len(nodes) == 1, (name, len(nodes))
    module = ast.fix_missing_locations(ast.Module(body=[nodes[0]], type_ignores=[]))
    g = {
        '__builtins__': __builtins__,
        're': re,
        'DBaseFormControlItem': DummyControl,
        'DBaseFormWindowItem': DummyWindow,
        'QTextCursor': DummyCursor,
        'QLineEdit': DummyLineEdit,
        'Qt': SimpleNamespace(OtherFocusReason=1),
    }
    exec(compile(module, '<d64_dism function>', 'exec'), g)
    return g[name]


class DummyControl:
    def __init__(self, name='PushButton1', component_type='Button'):
        self.component_name = name
        self.component_type = component_type
        self.wfm_events = {}


class DummyWindow(DummyControl):
    pass


class DummyCursor:
    EndOfLine = 2
    KeepAnchor = 3
    def __init__(self, document): self.document = document; self.position = 0
    def setPosition(self, value): self.position = value
    def movePosition(self, *args): pass


class Document:
    def __init__(self): self.modified = False
    def setModified(self, value): self.modified = bool(value)
    def isModified(self): return self.modified


class Editor:
    def __init__(self, source):
        self.source = source
        self.doc = Document()
        self.focus = False
    def toPlainText(self): return self.source
    def document(self): return self.doc
    def setTextCursor(self, cursor): self.cursor = cursor
    def centerCursor(self): self.centered = True
    def setFocus(self, reason): self.focus = True


class DummyPanel:
    def __init__(self, host, item):
        self.host = host
        self._selected_item = item
    def _event_host(self): return self.host


class DummyLineEdit:
    def __init__(self, text='', placeholder='PushButton1_onClick'):
        self.value = text
        self.placeholder = placeholder
    def text(self): return self.value
    def placeholderText(self): return self.placeholder
    def setText(self, value): self.value = value
    def setToolTip(self, value): self.tooltip = value


class DummyButton:
    def setEnabled(self, value): self.enabled = value


class Host:
    def __init__(self): self.calls = []; self.dbase_form_modified = False
    def _open_dbase_form_event_procedure(self, *args, **kwargs):
        self.calls.append((args, kwargs))
    def show_error(self, *args): self.error = args


class MethodHost:
    def __init__(self, source='CLASS Form1 OF FORM\nENDCLASS\n', methods=None):
        self.item = DummyControl()
        self.dbase_form_scene = SimpleNamespace(wfm_methods=list(methods or []))
        self.raw_editor = Editor(source)
        self.raw_editor.doc.modified = True
        self.dbase_form_build_document = SimpleNamespace(
            raw_editor=self.raw_editor,
            assembler_panel=SimpleNamespace(hide=lambda: None),
        )
        self.dbase_form_tabs = SimpleNamespace(setCurrentWidget=lambda page: None)
        self.dbase_form_source_page = object()
        self.dbase_form_modified = False
    def _ensure_dbase_form_designer(self): pass
    def _merge_dbase_form_source_methods_events(self, **kwargs): return True
    def _find_dbase_form_method(self, name):
        return next((m for m in self.dbase_form_scene.wfm_methods if m.name.casefold() == name.casefold()), None)
    def _sync_dbase_form_source(self):
        # Models the designer serializer's merge-before-rebuild behavior.
        if self.raw_editor.doc.modified:
            # Reimporting stale content would drop the just-appended method.
            self.dbase_form_scene.wfm_methods.clear()
        source = self.raw_editor.source + '\n' + '\n'.join(
            '\n'.join(m.source_lines) for m in self.dbase_form_scene.wfm_methods
        )
        self.raw_editor.source = source
        return source
    def show_error(self, *args): self.error = args


def test_renamed_event_and_legacy_source_compatibility():
    assert '"OnGotFocus",' in SOURCE
    assert '"OnGetFocus",' not in SOURCE
    assert normalized_focus_events({'OnGetFocus': 'CLASS::Old', 'OnClick': 'CLASS::Click'}) == {
        'OnClick': 'CLASS::Click', 'OnGotFocus': 'CLASS::Old'
    }
    assert normalized_focus_events({'OnGetFocus': 'Old', 'OnGotFocus': 'New'}) == {'OnGotFocus': 'New'}


@pytest.mark.parametrize('text,placeholder,expected', [
    ('', 'PushButton1_onClick', 'PushButton1_onClick'),
    ('CLASS::CustomClick', 'PushButton1_onClick', 'CustomClick'),
    ('', 'PushButton1_onGotFocus', 'PushButton1_onGotFocus'),
    (' Other_Name ', 'PushButton1_onClick', 'Other_Name'),
])
def test_resolve_placeholder_and_binding(text, placeholder, expected):
    assert resolve_event_procedure(text, placeholder) == expected


def test_reject_bad_procedure_names():
    with pytest.raises(ValueError): resolve_event_procedure('', 'bad file name')
    with pytest.raises(ValueError): resolve_event_procedure('', '')


def test_recognize_existing_function_or_procedure_without_prefix_collision():
    src = 'PROCEDURE PushButton1_onClickExtra(Sender)\nRETURN\n' \
          '    FUNCTION PushButton1_onClick(Sender)\nreturn 1\n'
    offset = find_event_procedure_offset(src, 'pushbutton1_ONCLICK')
    assert src[offset:].startswith('    FUNCTION PushButton1_onClick')
    assert find_event_procedure_offset(src, 'PushButton1_onGotFocus') is None


def test_double_click_empty_field_uses_placeholder_and_binds_event():
    host = Host(); item = DummyControl(); panel = DummyPanel(host, item)
    panel._event_create_or_navigate = method_for('_event_create_or_navigate').__get__(panel)
    edit = DummyLineEdit(); button = DummyButton()
    panel._event_create_or_navigate('OnClick', edit, create=True, button=button)
    assert edit.text() == 'PushButton1_onClick'
    assert item.wfm_events == {'OnClick': 'CLASS::PushButton1_onClick'}
    assert button.enabled and host.dbase_form_modified
    assert host.calls[-1][0][2] == 'PushButton1_onClick'
    assert host.calls[-1][1] == {'create': True}


def test_existing_name_navigation_does_not_replace_custom_name():
    host = Host(); item = DummyControl(); panel = DummyPanel(host, item)
    panel._event_create_or_navigate = method_for('_event_create_or_navigate').__get__(panel)
    edit = DummyLineEdit('ExistingHandler')
    panel._event_create_or_navigate('OnGotFocus', edit, create=True)
    assert edit.text() == 'ExistingHandler'
    assert host.calls[0][0][2] == 'ExistingHandler'


def test_generate_once_and_reuse_existing_method_without_overwriting_body():
    host = MethodHost()
    host._open_dbase_form_event_procedure = method_for('_open_dbase_form_event_procedure').__get__(host)
    host._open_dbase_form_event_procedure(host.item, 'OnClick', 'PushButton1_onClick', create=True)
    assert len(host.dbase_form_scene.wfm_methods) == 1
    method = host.dbase_form_scene.wfm_methods[0]
    assert method.parameters == ('Sender',)
    assert method.source_lines[0] == 'procedure PushButton1_onClick(Sender)'
    assert method.source_lines[-1].strip().lower() == 'return'
    assert host.raw_editor.focus and host.raw_editor.centered
    host._open_dbase_form_event_procedure(host.item, 'OnClick', 'PushButton1_onClick', create=True)
    assert len(host.dbase_form_scene.wfm_methods) == 1


def test_existing_method_body_preserved_and_case_insensitive_lookup():
    method = DBaseWfmMethod(name='PushButton1_onClick', parameters=('Sender',),
                            body=['? "alter Quellcode"', 'return'],
                            source_lines=['procedure PushButton1_onClick(Sender)', '? "alter Quellcode"', 'return'])
    host = MethodHost(methods=[method])
    host._open_dbase_form_event_procedure = method_for('_open_dbase_form_event_procedure').__get__(host)
    host._open_dbase_form_event_procedure(host.item, 'OnClick', 'pushbutton1_ONCLICK', create=True)
    assert host.dbase_form_scene.wfm_methods == [method]
    assert '? "alter Quellcode"' in host.raw_editor.toPlainText()


def test_direct_dblclick_in_empty_input_emits_signal():
    assert 'if self.text().strip() or self.placeholderText().strip():' in SOURCE
    assert 'event_suffix = event_suffix[:1].lower() + event_suffix[1:]' in SOURCE

