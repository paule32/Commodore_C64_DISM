# -*- coding: utf-8 -*-
"""Stage 421: tests that do not require Qt on the test machine."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parent
MAIN = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
PAGE = (ROOT / 'rotation_matrix_fact.py').read_text(encoding='utf-8')


def _class(tree, name):
    return next(node for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef) and node.name == name)


def _method(cls, name):
    return next(node for node in cls.body
                if isinstance(node, ast.FunctionDef) and node.name == name)


def test_reference_stage_matrix_types_stay_complete():
    """The existing card keys remain untouched when moving tree leaves."""
    klass = _class(ast.parse(MAIN), 'BasicMathRulesFactWidget')
    entries = next(ast.literal_eval(node.value)
                   for node in klass.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'MATRIX_TYPES'
                           for target in node.targets))
    assert len(entries) == 38
    assert len({row[0] for row in entries}) == 38
    assert all(key.startswith('matrix_') for key, *_ in entries)


def test_matrix_tree_nested_under_exact_nodes():
    cls = _class(ast.parse(MAIN), 'MathematicsLearningDockWidget')
    populate = ast.get_source_segment(MAIN, _method(cls, '_populate_facts_tree'))
    assert "QTreeWidgetItem(['Arten von . . .'])" in populate
    assert "QTreeWidgetItem(['Rechnen mit . . .'])" in populate
    assert 'matrix_types_group.addChild(matrix_item)' in populate
    assert 'matrix_calculation_group.addChild(rotation_item)' in populate
    assert "rotation_item.setData(0, Qt.UserRole, 'matrix_rotation')" in populate
    assert "self._fact_items['matrix_rotation'] = rotation_item" in populate
    assert 'matrices.addChild(matrix_types_group)' in populate
    assert 'matrices.addChild(matrix_calculation_group)' in populate


def test_rotation_page_and_dispatch():
    cls = _class(ast.parse(MAIN), 'MathematicsLearningDockWidget')
    init = ast.get_source_segment(MAIN, _method(cls, '__init__'))
    dispatch = ast.get_source_segment(MAIN, _method(cls, 'open_fact'))
    theme = ast.get_source_segment(MAIN, _method(cls, 'set_dark_mode'))
    assert 'RotationMatrixFactWidget()' in init
    assert 'rotation_matrix_scroll_area' in init
    assert "elif fact_key == 'matrix_rotation':" in dispatch
    assert 'self.content_stack.setCurrentWidget(self.rotation_matrix_scroll)' in dispatch
    assert dispatch.index("elif fact_key == 'matrix_rotation':") < dispatch.index("fact_key.startswith('matrix_')")
    assert 'self.rotation_matrix_widget.set_dark_mode(enabled)' in theme


def test_rotation_math_and_reference_captions():
    tree = ast.parse(PAGE)
    klass = _class(tree, 'RotationMatrixFactWidget')
    method = _method(klass, 'paintEvent')
    constants = [node.value for node in ast.walk(method) if isinstance(node, ast.Constant)
                 and isinstance(node.value, str)]
    for title in ('Rotational Matrix', 'Elementare Verschiebungen',
                  'Verschiebung um die x-Achse', 'Verschiebung um die y-Achse',
                  'Verschiebung um die z-Achse'):
        assert title in constants
    assert PAGE.count("'−sin(θ)'") >= 4
    assert PAGE.count("'cos(θ)'") >= 8
    assert all(name in PAGE for name in ('R_x(φ)', 'R_y(θ)', 'R_z(ψ)',
                                       'P_x =', 'P_y =', 'P_z ='))
    assert 'painter.drawPath(path)' in PAGE
    assert 'QLinearGradient' in PAGE
    assert 'watermark' not in PAGE.lower()


def test_qt_module_syntax_and_no_external_assets():
    ast.parse(PAGE)
    assert 'requests' not in PAGE
    assert '.png' not in PAGE
    assert '.jpg' not in PAGE
