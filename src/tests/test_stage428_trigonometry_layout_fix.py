# -*- coding: utf-8 -*-
"""Stage 428: trigonometry sheet geometry and footer cleanup."""
from __future__ import annotations

import ast
from pathlib import Path

PAGE = (Path(__file__).parent / 'trigonometry_right_triangle_fact.py').read_text(encoding='utf-8')


def test_footer_text_block_removed():
    ast.parse(PAGE)
    assert 'Trigonometrie' not in PAGE
    assert 'Lernblatt' not in PAGE
    assert 'rechtwinkliges Dreieck' not in PAGE


def test_alpha_angle_top_marker_and_right_side_label_adjusted():
    assert "painter.drawArc(178, 354, 124, 124, -6 * 16, 72 * 16)" in PAGE
    assert "self._write(painter, 240, 407, 'α'" in PAGE
    assert "painter.drawArc(382, 232, 90, 90, 300 * 16, 84 * 16)" in PAGE
    assert "painter.drawEllipse(QPointF(454, 275), 4.5, 4.5)" in PAGE
    assert "painter.translate(525, 298)" in PAGE
    assert "painter.rotate(52)" in PAGE
