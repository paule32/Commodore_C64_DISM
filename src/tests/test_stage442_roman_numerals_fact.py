# -*- coding: utf-8 -*-
"""Stage 442: Roman numerals page, text-only QPlainTextEdit and tree integration."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parent
PAGE = (ROOT / 'roman_numerals_fact.py').read_text(encoding='utf-8')
MAIN = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')


def _page_data():
    tree = ast.parse(PAGE)
    selected = [node for node in tree.body if
                (isinstance(node, (ast.Assign, ast.AnnAssign)) and
                 any(name in ast.unparse(node) for name in (
                    'ROMAN_SYMBOLS', 'ROMAN_VALUES', 'ROMAN_THIRD_COLUMN'))) or
                (isinstance(node, ast.FunctionDef) and node.name in (
                    'roman_numeral', 'roman_table_rows'))]
    mod = ast.Module(body=selected, type_ignores=[])
    compiled = compile(ast.fix_missing_locations(mod), '<roman_data>', 'exec')
    env = {}
    exec(compiled, env)
    return env


def _main_class():
    tree = ast.parse(MAIN)
    return next(node for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef) and
                node.name == 'MathematicsLearningDockWidget')


def _method_source(cls, name):
    method = next(node for node in cls.body
                  if isinstance(node, ast.FunctionDef) and node.name == name)
    return ast.get_source_segment(MAIN, method)


def test_full_roman_reference_table_exact_rows():
    data = _page_data()
    table = data['roman_table_rows']()
    assert len(table) == 20
    assert [row[0][0] for row in table] == list(range(1, 21))
    assert [row[1][0] for row in table] == list(range(21, 41))
    assert [row[2][0] for row in table] == list(range(41, 51)) + [
        60, 70, 80, 90, 100, 200, 300, 400, 500, 1000]
    assert table[0] == ((1, 'I'), (21, 'XXI'), (41, 'XLI'))
    assert table[8] == ((9, 'IX'), (29, 'XXIX'), (49, 'XLIX'))
    assert table[9] == ((10, 'X'), (30, 'XXX'), (50, 'L'))
    assert table[13] == ((14, 'XIV'), (34, 'XXXIV'), (90, 'XC'))
    assert table[19] == ((20, 'XX'), (40, 'XL'), (1000, 'M'))


def test_roman_alphabet_and_subtractive_notation():
    data = _page_data()
    conv = data['roman_numeral']
    assert data['ROMAN_SYMBOLS'] == ('I', 'V', 'X', 'L', 'C', 'D', 'M')
    assert data['ROMAN_VALUES'] == (1, 5, 10, 50, 100, 500, 1000)
    for number, expected in (
        (4, 'IV'), (9, 'IX'), (19, 'XIX'), (40, 'XL'),
        (49, 'XLIX'), (90, 'XC'), (400, 'CD'), (900, 'CM'),
        (3999, 'MMMCMXCIX'),
    ):
        assert conv(number) == expected
    for invalid in (0, 4000, -1, True, '19'):
        try:
            conv(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid roman numeral accepted: ' + repr(invalid))


def test_widget_is_read_only_qplain_text_with_native_qt_formatting():
    tree = ast.parse(PAGE)
    cls = next(node for node in tree.body
               if isinstance(node, ast.ClassDef) and
               node.name == 'RomanNumeralsFactWidget')
    assert isinstance(cls.bases[0], ast.Name) and cls.bases[0].id == 'QPlainTextEdit'
    assert 'self.setReadOnly(True)' in PAGE
    assert 'self.setLineWrapMode(QPlainTextEdit.NoWrap)' in PAGE
    assert 'QTextCursor' in PAGE and 'QTextCharFormat' in PAGE
    assert 'QTextBlockFormat' in PAGE and 'setTabPositions' in PAGE
    assert "'RÖMISCHE ZAHLEN'" in PAGE
    assert 'for row in roman_table_rows()' in PAGE
    assert 'setStyleSheet(' in PAGE
    assert '.png' not in PAGE and '.jpg' not in PAGE
    assert 'QPainter' not in PAGE and 'QPixmap' not in PAGE


def test_tree_leaf_under_zahlen_opened_with_single_click():
    assert 'from roman_numerals_fact import RomanNumeralsFactWidget' in MAIN
    cls = _main_class()
    populate = _method_source(cls, '_populate_facts_tree')
    init = _method_source(cls, '__init__')
    dispatch = _method_source(cls, 'open_fact')
    onclick = _method_source(cls, '_handle_fact_click')
    assert "zahlen = QTreeWidgetItem(['Zahlen'])" in populate
    assert "roman_item = QTreeWidgetItem(['Römische . . .'])" in populate
    assert "roman_item.setData(0, Qt.UserRole, 'roman_numerals')" in populate
    assert "zahlen.addChild(roman_item)" in populate
    assert "self._fact_items['roman_numerals'] = roman_item" in populate
    assert 'self.roman_numerals_widget = RomanNumeralsFactWidget(' in init
    assert 'self.content_stack.addWidget(self.roman_numerals_widget)' in init
    assert "elif fact_key == 'roman_numerals':" in dispatch
    assert 'self.content_stack.setCurrentWidget(self.roman_numerals_widget)' in dispatch
    assert 'self.open_fact(fact_key, title)' in onclick


def test_theme_is_propagated_and_page_remains_selectable_text():
    cls = _main_class()
    theme = _method_source(cls, 'set_dark_mode')
    assert 'self.roman_numerals_widget.set_dark_mode(enabled)' in theme
    assert 'self._build_text()' in PAGE
    assert 'self.setUndoRedoEnabled(False)' in PAGE
    assert 'setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)' not in PAGE
    assert 'self.setTextCursor(cursor)' in PAGE
