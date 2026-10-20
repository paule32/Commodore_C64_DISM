# -*- coding: utf-8 -*-
"""Stage 444: formatierte roemische Zahlen, sieben Kopfspalten und Dark-Mode."""
from __future__ import annotations

import ast
from pathlib import Path

SOURCE = (Path(__file__).parent / 'roman_numerals_fact.py').read_text(encoding='utf-8')
TREE = ast.parse(SOURCE)


def _function(name):
    return next(node for node in TREE.body if isinstance(node, ast.FunctionDef)
                and node.name == name)


def _method(name):
    cls = next(node for node in TREE.body if isinstance(node, ast.ClassDef)
               and node.name == 'RomanNumeralsFactWidget')
    return next(node for node in cls.body if isinstance(node, ast.FunctionDef)
                and node.name == name)


def _standalone_function(name):
    node = _function(name)
    isolated = ast.Module(body=[node], type_ignores=[])
    scope = {}
    exec(compile(ast.fix_missing_locations(isolated), '<column_stops>', 'exec'), scope)
    return scope[name]


def test_tabs_are_based_on_maximum_text_width_not_old_absolute_offsets():
    stops = _standalone_function('roman_column_stops')
    widths = (32, 80, 32, 128, 60, 80)
    actual = stops(widths, gap=18)
    assert len(actual) == 5
    start = 0
    for column, stop in enumerate(actual):
        assert stop >= start + widths[column] + 18
        start = stop
    assert 'body_tabs = [88, 215, 275, 404, 464]' not in SOURCE
    layout = ast.get_source_segment(SOURCE, _method('_body_tab_positions'))
    assert 'QFontMetricsF' in SOURCE
    assert 'roman_table_rows()' in layout
    assert 'max(self._text_width(value' in layout
    assert 'roman_column_stops(widths' in layout


def test_all_seven_roman_symbol_columns_have_six_measured_tabs():
    content = ast.get_source_segment(SOURCE, _method('_build_text'))
    tabs = ast.get_source_segment(SOURCE, _method('_header_tab_positions'))
    assert "line('\\t'.join(ROMAN_SYMBOLS)" in content
    assert "line('\\t'.join(str(value) for value in ROMAN_VALUES)" in content
    assert 'zip(ROMAN_SYMBOLS, ROMAN_VALUES)' in tabs
    assert 'roman_column_stops(widths' in tabs
    assert "left=36, tabs=header_tabs" in content


def test_three_number_roman_pairs_keep_independent_six_body_columns():
    content = ast.get_source_segment(SOURCE, _method('_build_text'))
    assert 'for row in roman_table_rows()' in content
    assert "pieces.append((str(value) + '\\t', False))" in content
    assert 'pieces.append((symbol, True))' in content
    assert 'body_tabs = self._body_tab_positions()' in content
    assert 'self.setReadOnly(True)' in SOURCE
    assert 'self.setLineWrapMode(QPlainTextEdit.NoWrap)' in SOURCE


def test_real_dark_and_light_text_colors_and_theme_reformatting():
    assert "'background': '#17212d'" in SOURCE
    assert "'text': '#f1f5fb'" in SOURCE
    assert "'title': '#8bc4ff'" in SOURCE
    assert "'background': '#fdfdfb'" in SOURCE
    assert "'text': '#191919'" in SOURCE
    body = ast.get_source_segment(SOURCE, _method('_build_text'))
    theme = ast.get_source_segment(SOURCE, _method('set_dark_mode'))
    assert "colors = ROMAN_DARK_COLORS if self._dark_mode else ROMAN_LIGHT_COLORS" in body
    assert "colors['text']" in body
    assert "color=colors['title']" in body
    assert "color=colors['rule']" in body
    assert "if changed:" in theme
    assert "self._build_text()" in theme
    assert 'self.verticalScrollBar().setValue(vertical)' in theme
    assert 'self.horizontalScrollBar().setValue(horizontal)' in theme


def test_widget_can_scroll_when_dock_is_too_narrow():
    assert 'self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)' in SOURCE
    assert 'self.setMinimumSize(0, 0)' in SOURCE
    assert 'self.setLineWrapMode(QPlainTextEdit.NoWrap)' in SOURCE
    assert 'setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)' not in SOURCE
    assert 'self.horizontalScrollBar().setValue(0)' in SOURCE
