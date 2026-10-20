# -*- coding: utf-8 -*-
"""Stage 423: verify bottom 'Verschieben 3-D' layout tweak."""
from __future__ import annotations

import ast
from pathlib import Path

PAGE = (Path(__file__).parent / 'rotation_matrix_fact.py').read_text(encoding='utf-8')

def test_bottom_z_section_shifted_left_and_wider_tiles():
    ast.parse(PAGE)
    assert "('Verschiebung um die z-Achse', 'P_z =', (" in PAGE
    assert "), 1133, 'z', 95, 125)" in PAGE
    assert "for heading, name, rows, y, axis, matrix_x, col_width in sections:" in PAGE
    assert "self._matrix(painter, name, rows, y+50, x=matrix_x," in PAGE
    assert "col_width=col_width" in PAGE
