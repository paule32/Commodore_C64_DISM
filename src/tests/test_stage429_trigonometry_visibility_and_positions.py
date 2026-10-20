# -*- coding: utf-8 -*-
"""Stage 429: further left alpha, shifted Gegenkathete, adjusted triangle and visible tan section."""
from __future__ import annotations

import ast
from pathlib import Path

PAGE = (Path(__file__).parent / 'trigonometry_right_triangle_fact.py').read_text(encoding='utf-8')


def test_alpha_shifted_left_and_right_label_shifted_left():
    ast.parse(PAGE)
    assert "painter.drawArc(148, 352, 124, 124, -4 * 16, 72 * 16)" in PAGE
    assert "self._write(painter, 210, 405, 'α'" in PAGE
    assert "painter.translate(520, 292)" in PAGE
    assert "painter.rotate(60)" in PAGE


def test_triangle_geometry_changed():
    assert "a = QPointF(96, 432)" in PAGE
    assert "b = QPointF(430, 236)" in PAGE
    assert "c = QPointF(548, 439)" in PAGE
    assert "painter.drawArc(388, 228, 88, 88, 298 * 16, 88 * 16)" in PAGE


def test_tan_section_fully_visible_on_paper():
    assert "BASE_HEIGHT = 980" in PAGE
    assert "painter.fillRect(QRectF(34, 166, 672, 760), QColor(self._colors['paper']))" in PAGE
    assert "self._formula_block(painter, 568)" in PAGE
    # tan denominator and fraction must fit on paper with the new geometry
    paper_bottom = 166 + 760
    tan_top = 568 + 132 + 150
    tan_bottom_estimate = tan_top + 42 + 36
    assert tan_bottom_estimate < paper_bottom
