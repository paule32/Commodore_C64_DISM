# -*- coding: utf-8 -*-
"""Stage 422: tree structure, dark-mode facts and matrix multiplication page."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parent
MAIN = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
ROTATION = (ROOT / 'rotation_matrix_fact.py').read_text(encoding='utf-8')
MULTIPLICATION = (ROOT / 'multiplication_matrix_fact.py').read_text(encoding='utf-8')


def _class(tree, name):
    return next(node for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef) and node.name == name)


def _method(cls, name):
    return next(node for node in cls.body
                if isinstance(node, ast.FunctionDef) and node.name == name)


def test_matrix_calculation_tree_contains_multiplication_and_renamed_rotation():
    cls = _class(ast.parse(MAIN), 'MathematicsLearningDockWidget')
    populate = ast.get_source_segment(MAIN, _method(cls, '_populate_facts_tree'))
    assert "QTreeWidgetItem(['Multiplikation'])" in populate
    assert "QTreeWidgetItem(['Verschieben 3-D'])" in populate
    assert "multiplication_item.setData(0, Qt.UserRole, 'matrix_multiplication')" in populate
    assert "self._fact_items['matrix_multiplication'] = multiplication_item" in populate
    assert "rotation_item.setData(0, Qt.UserRole, 'matrix_rotation')" in populate
    assert populate.index("QTreeWidgetItem(['Multiplikation'])") < populate.index("QTreeWidgetItem(['Verschieben 3-D'])")


def test_math_tree_icons_are_applied():
    cls = _class(ast.parse(MAIN), 'MathematicsLearningDockWidget')
    populate = ast.get_source_segment(MAIN, _method(cls, '_populate_facts_tree'))
    assert 'standardIcon(QStyle.SP_DirClosedIcon)' in populate
    assert 'standardIcon(QStyle.SP_FileIcon)' in populate
    assert 'def _apply_learning_tree_icons(item):' in populate
    assert '_apply_learning_tree_icons(self.facts_tree.topLevelItem(index))' in populate


def test_multiplication_page_is_instantiated_and_dispatched_in_dark_mode():
    cls = _class(ast.parse(MAIN), 'MathematicsLearningDockWidget')
    init = ast.get_source_segment(MAIN, _method(cls, '__init__'))
    dispatch = ast.get_source_segment(MAIN, _method(cls, 'open_fact'))
    theme = ast.get_source_segment(MAIN, _method(cls, 'set_dark_mode'))
    assert 'MultiplicationMatrixFactWidget()' in init
    assert 'multiplication_matrix_scroll_area' in init
    assert "elif fact_key == 'matrix_multiplication':" in dispatch
    assert 'self.content_stack.setCurrentWidget(self.multiplication_matrix_scroll)' in dispatch
    assert 'self.multiplication_matrix_widget.set_dark_mode(enabled)' in theme
    assert 'self._dark_mode = True' in init


def test_multiplication_page_texts_and_no_external_assets():
    tree = ast.parse(MULTIPLICATION)
    klass = _class(tree, 'MultiplicationMatrixFactWidget')
    method = _method(klass, 'paintEvent')
    constants = [node.value for node in ast.walk(method) if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    assert 'Matrix Multiplikation: Schritt für Schritt' in constants
    for token in ('21', '24', '7', '54', '0'):
        assert token in MULTIPLICATION
    assert 'QPainter' in MULTIPLICATION
    assert '.png' not in MULTIPLICATION
    assert '.jpg' not in MULTIPLICATION
    ast.parse(MULTIPLICATION)


def test_rotation_page_stays_available():
    assert 'RotationMatrixFactWidget' in MAIN
    assert "QTreeWidgetItem(['Verschieben 3-D'])" in MAIN
    ast.parse(ROTATION)
