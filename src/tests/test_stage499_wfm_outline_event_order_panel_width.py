"""Stage 499: sorted WFM outline, insertion of event procedures, +10px panel."""

import ast
from functools import lru_cache
from pathlib import Path
import re
from types import SimpleNamespace

from d64dbase.form_method_order import source_outline_sort_key, insert_event_method_sorted
from d64dbase.wfm import DBaseWfmMethod
from d64dbase.source_roundtrip import wfm_method_source_lines

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / 'd64_dism.py').read_text('utf-8')


def method(name):
    tree = ast.parse(SOURCE)
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    namespace = {'re': re, 'Qt': SimpleNamespace(UserRole=32),
                 'QTreeWidgetItem': FakeTreeItem}
    exec(compile(module, '<d64_dism method>', 'exec'), namespace)
    return namespace[name]


class FakeTreeItem:
    def __init__(self, parent, texts):
        self.parent = parent
        self.name = texts[0]
        self.children = []
        self.data = {}
        if parent is not None:
            parent.children.append(self)

    def setExpanded(self, value): self.expanded = value
    def setData(self, col, role, value): self.data[(col, role)] = value
    def setToolTip(self, col, tip): self.tooltip = tip


class FakeTree:
    def __init__(self): self.children = []
    def blockSignals(self, flag): self.blocked = flag
    def clear(self): self.children = []


class FakeEditor:
    def __init__(self, source): self.source = source
    def toPlainText(self): return self.source


def test_procedure_outline_special_prefix_then_natural_alpha():
    names = ['Button10_onClick', '__del__', 'zeta', '__init__',
             'Button2_onClick', 'Alpha', 'button1_onClick']
    assert sorted(names, key=lambda n: source_outline_sort_key(n, 'procedure')) == [
        '__init__', '__del__', 'Alpha', 'button1_onClick',
        'Button2_onClick', 'Button10_onClick', 'zeta',
    ]


def test_function_outline_main_then_natural_alpha():
    names = ['Zed', 'get10', '__main__', 'get2', 'alpha']
    assert sorted(names, key=lambda n: source_outline_sort_key(n, 'function')) == [
        '__main__', 'alpha', 'get2', 'get10', 'Zed',
    ]


def test_outline_reorders_labels_but_keeps_correct_source_line():
    source = ('CLASS Form1 OF FORM\n'
              '  LOCAL MyValue = 1\n'
              '  FUNCTION Later()\n'
              '    return 2\n'
              '  PROCEDURE Button10_onClick(Sender)\n'
              '    return\n'
              '  PROCEDURE __del__\n'
              '    return\n'
              '  FUNCTION __main__()\n'
              '    return 0\n'
              '  PROCEDURE Button2_onClick(Sender)\n'
              '    return\n'
              '  PROCEDURE __init__\n'
              '    return\n'
              '  FUNCTION alpha()\n'
              '    return 1\n'
              'ENDCLASS\n')
    tree = FakeTree()
    host = SimpleNamespace(dbase_form_source_outline=tree,
                           dbase_form_build_document=SimpleNamespace(raw_editor=FakeEditor(source)))
    method('_refresh_dbase_form_source_outline')(host)
    proc, func, globs = tree.children
    assert proc.name == 'Prozeduren' and func.name == 'Funktionen'
    assert [child.name for child in proc.children] == [
        '__init__', '__del__', 'Button2_onClick', 'Button10_onClick'
    ]
    assert [child.data[(0, 32)] for child in proc.children] == [13, 7, 11, 5]
    assert [child.name for child in func.children] == ['__main__', 'alpha', 'Later']
    assert [child.data[(0, 32)] for child in func.children] == [9, 15, 3]
    assert [child.name for child in globs.children] == ['MyValue']
    assert tree.blocked is False


def _handler(name, body=None):
    body = body or ['    ? "unveraendert"', '    RETURN']
    return DBaseWfmMethod(name=name, source_lines=[f'    procedure {name}(Sender)'] + body,
                          source_start_line=10)


def test_new_handlers_sorted_and_manual_method_body_untouched():
    init = DBaseWfmMethod(name='__init__', source_lines=['    procedure __init__', '        return'])
    manual = DBaseWfmMethod(name='SomeManualMethod', source_lines=['    procedure SomeManualMethod',
                     '        ? "HANDSCHRIFTLICH"', '        return'], source_start_line=9)
    button10 = _handler('Button10_onClick')
    button2 = _handler('Button2_onClick')
    original_manual_lines = wfm_method_source_lines(manual)
    methods = [init, button10, manual, button2]
    methods = insert_event_method_sorted(methods, _handler('Button1_onLostFocus'))
    assert [m.name for m in methods] == [
        '__init__', 'Button1_onLostFocus', 'Button2_onClick', 'Button10_onClick', 'SomeManualMethod',
    ]
    assert wfm_method_source_lines(manual) == original_manual_lines
    assert '? "HANDSCHRIFTLICH"' in '\n'.join(original_manual_lines)


def test_custom_bound_event_names_sorted_too():
    x = _handler('MyHandler')
    z = _handler('ZEvent')
    result = insert_event_method_sorted([z, x], _handler('Button1_onClick'),
                                         bound_names=('MyHandler', 'ZEvent'))
    assert [method.name for method in result] == ['Button1_onClick', 'MyHandler', 'ZEvent']


def test_duplicate_is_not_added_even_with_case_difference():
    item = _handler('Button2_onClick')
    existing = [item]
    assert insert_event_method_sorted(existing, _handler('button2_ONCLICK')) == existing
    assert existing[0] is item


def test_no_event_handlers_uses_original_append_position():
    original = [DBaseWfmMethod(name='__init__'), DBaseWfmMethod(name='__del__')]
    result = insert_event_method_sorted(original, _handler('Button1_onClick'))
    assert [m.name for m in result] == ['__init__', '__del__', 'Button1_onClick']


def test_designer_inserts_using_sorter_before_sync():
    root = ast.parse(SOURCE)
    fn = next(n for n in ast.walk(root) if isinstance(n, ast.FunctionDef)
              and n.name == '_open_dbase_form_event_procedure')
    text = ast.get_source_segment(SOURCE, fn)
    assert 'insert_event_method_sorted(' in text
    assert text.index('insert_event_method_sorted(') < text.index('source = self._sync_dbase_form_source()')
    assert 'methods.append(method)' not in text


def test_designer_left_panel_widened_exactly_10_px():
    root = ast.parse(SOURCE)
    fn = next(n for n in ast.walk(root) if isinstance(n, ast.FunctionDef)
              and n.name == 'show_dbase_form_designer')
    text = ast.get_source_segment(SOURCE, fn)
    assert '[340, 100000]' in text
    assert '[330, 100000]' not in text
