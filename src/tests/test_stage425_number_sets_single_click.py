# -*- coding: utf-8 -*-
"""Stage 425: Zahlen-Mengen, single-click math navigation and collapsed matrix types."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parent
MAIN = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
PAGE = (ROOT / 'number_sets_fact.py').read_text(encoding='utf-8')


def _class(tree, name):
    return next(node for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef) and node.name == name)


def _method(cls, name):
    return next(node for node in cls.body
                if isinstance(node, ast.FunctionDef) and node.name == name)


def test_number_sets_imported_instantiated_and_dispatched():
    assert 'from number_sets_fact import NumberSetsFactWidget' in MAIN
    cls = _class(ast.parse(MAIN), 'MathematicsLearningDockWidget')
    init = ast.get_source_segment(MAIN, _method(cls, '__init__'))
    dispatch = ast.get_source_segment(MAIN, _method(cls, 'open_fact'))
    theme = ast.get_source_segment(MAIN, _method(cls, 'set_dark_mode'))
    assert 'NumberSetsFactWidget()' in init
    assert 'number_sets_scroll_area' in init
    assert "if fact_key == 'number_sets':" in dispatch
    assert 'self.content_stack.setCurrentWidget(self.number_sets_scroll)' in dispatch
    assert 'self.number_sets_widget.set_dark_mode(enabled)' in theme


def test_number_sets_is_first_leaf_under_grundwissen_and_matrix_types_collapsed():
    cls = _class(ast.parse(MAIN), 'MathematicsLearningDockWidget')
    populate = ast.get_source_segment(MAIN, _method(cls, '_populate_facts_tree'))
    assert "number_sets = QTreeWidgetItem(['Zahlen-Mengen'])" in populate
    assert "number_sets.setData(0, Qt.UserRole, 'number_sets')" in populate
    assert "grundwissen.addChild(number_sets)" in populate
    assert populate.index("grundwissen.addChild(number_sets)") < populate.index("grundwissen.addChild(rules)")
    assert 'matrix_types_group.setExpanded(False)' in populate


def test_single_click_navigation_enabled_for_facts_and_games():
    cls = _class(ast.parse(MAIN), 'MathematicsLearningDockWidget')
    init = ast.get_source_segment(MAIN, _method(cls, '__init__'))
    fact_click = ast.get_source_segment(MAIN, _method(cls, '_handle_fact_click'))
    game_click = ast.get_source_segment(MAIN, _method(cls, '_handle_game_click'))
    assert 'self.facts_tree.itemClicked.connect(self._handle_fact_click)' in init
    assert 'self.games_tree.itemClicked.connect(self._handle_game_click)' in init
    assert 'self.open_fact(fact_key, title)' in fact_click
    assert 'self.open_game(game_key, title)' in game_click
    assert 'self._find_first_fact_descendant(item)' in fact_click
    assert 'self._find_first_game_descendant(item)' in game_click


def test_number_sets_page_is_qpainter_rendered_and_not_external_image():
    ast.parse(PAGE)
    assert 'QPainter' in PAGE
    assert 'QPainterPath' in PAGE
    assert 'addRoundedRect' in PAGE
    assert 'fillPath' in PAGE
    assert 'drawText' in PAGE
    assert '.png' not in PAGE
    assert '.jpg' not in PAGE
    for text in ('komplexe Zahlen', 'algebraische Zahlen', 'natürliche', 'ganze', 'rationale', 'reelle Zahlen', 'imaginärer Teil', 'reeller Teil'):
        assert text in PAGE
