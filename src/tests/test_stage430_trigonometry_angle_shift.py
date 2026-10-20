# -*- coding: utf-8 -*-
"""Stage 430: further left alpha and right-angle marker shift/rotation."""
from __future__ import annotations

import ast
from pathlib import Path

PAGE = (Path(__file__).parent / 'trigonometry_right_triangle_fact.py').read_text(encoding='utf-8')


def test_alpha_moved_further_left():
    ast.parse(PAGE)
    assert "painter.drawArc(128, 352, 124, 124, -4 * 16, 72 * 16)" in PAGE
    assert "self._write(painter, 190, 405, 'α'" in PAGE


def test_right_angle_dot_and_arc_shifted_left_and_arc_rotated():
    assert "painter.drawArc(373, 228, 88, 88, 28 * 16, 88 * 16)" in PAGE
    assert "painter.drawEllipse(QPointF(448, 271), 4.5, 4.5)" in PAGE
