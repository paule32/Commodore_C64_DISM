# -*- coding: utf-8 -*-
"""Stage 426: Trigonometrie tree node and right-triangle fact page."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parent
MAIN = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
PAGE = (ROOT / 'trigonometry_right_triangle_fact.py').read_text(encoding='utf-8')


def _class(tree, name):
    return next(node for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef) and node.name == name)


def _method(cls, name):
    return next(node for node in cls.body
                if isinstance(node, ast.FunctionDef) and node.name == name)


def test_trigonometry_import_widget_and_dispatch_exist():
    assert 'from trigonometry_right_triangle_fact import TrigonometryRightTriangleFactWidget' in MAIN
    cls = _class(ast.parse(MAIN), 'MathematicsLearningDockWidget')
    init = ast.get_source_segment(MAIN, _method(cls, '__init__'))
    dispatch = ast.get_source_segment(MAIN, _method(cls, 'open_fact'))
    theme = ast.get_source_segment(MAIN, _method(cls, 'set_dark_mode'))
    assert 'TrigonometryRightTriangleFactWidget()' in init
    assert 'trigonometry_right_triangle_scroll_area' in init
    assert "elif fact_key == 'trigonometry_right_triangle':" in dispatch
    assert 'self.content_stack.setCurrentWidget(self.trigonometry_right_triangle_scroll)' in dispatch
    assert 'self.trigonometry_right_triangle_widget.set_dark_mode(enabled)' in theme


def test_geometry_groups_collapsed_and_trigonometry_has_child_leaf():
    cls = _class(ast.parse(MAIN), 'MathematicsLearningDockWidget')
    populate = ast.get_source_segment(MAIN, _method(cls, '_populate_facts_tree'))
    assert 'flaechen.setExpanded(False)' in populate
    assert 'volume.setExpanded(False)' in populate
    assert "trigometrie = QTreeWidgetItem(['Trigometrie'])" in populate
    assert "right_triangle_item = QTreeWidgetItem(['Rechtwinkliges Dreieck'])" in populate
    assert "right_triangle_item.setData(0, Qt.UserRole, 'trigonometry_right_triangle')" in populate
    assert "trigometrie.addChild(right_triangle_item)" in populate
    assert "self._fact_items['trigonometry_right_triangle'] = right_triangle_item" in populate


def test_trigonometry_page_is_drawn_with_qpainter_and_not_image_copy():
    ast.parse(PAGE)
    assert 'QPainter' in PAGE
    assert 'drawText' in PAGE
    assert 'drawLine' in PAGE
    assert 'drawArc' in PAGE
    assert '.png' not in PAGE
    assert '.jpg' not in PAGE
    for text in ('SPICKZETTEL', 'Sinus, Cosinus & Tangens', 'Ankathete', 'Gegenkathete', 'Hypotenuse', 'sin(α)', 'cos(α)', 'tan(α)'):
        assert text in PAGE


def test_single_click_path_can_resolve_trigonometry_node_to_child():
    cls = _class(ast.parse(MAIN), 'MathematicsLearningDockWidget')
    helper = ast.get_source_segment(MAIN, _method(cls, '_find_first_fact_descendant'))
    click = ast.get_source_segment(MAIN, _method(cls, '_handle_fact_click'))
    assert 'for index in range(item.childCount()):' in helper
    assert 'self._find_first_fact_descendant(item)' in click
    assert 'self.open_fact(fact_key, title)' in click
