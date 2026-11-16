# -*- coding: utf-8 -*-
"""Stage 570: Mathematische Korrektheit und Anschluss an vorhandenes Mathematik-Dock."""
import pathlib
import unittest
from decimal import Decimal
from matrix_multiplication_logic import (
    parse_matrix_value, format_matrix_value, multiply_matrices, matrix_calculation_steps,
)


ROOT = pathlib.Path(__file__).resolve().parent
SOURCE = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
PANEL = (ROOT / 'matrix_multiplication_panel.py').read_text(encoding='utf-8')


class MultiplicationMathTests(unittest.TestCase):
    def test_2_by_3_times_3_by_2(self):
        a = [[1, 2, 3], [4, 5, 6]]
        b = [[7, 8], [9, 10], [11, 12]]
        self.assertEqual(multiply_matrices(a, b), [[58, 64], [139, 154]])

    def test_row_column_inner_product(self):
        self.assertEqual(multiply_matrices([['2', '3']], [['4'], ['5']]), [[23]])

    def test_blanks_are_zero(self):
        self.assertEqual(multiply_matrices([['', '3']], [[''], ['2']]), [[6]])

    def test_comma_decimals_and_negatives(self):
        self.assertEqual(multiply_matrices([['1,5', '-2']], [['2'], ['0,5']]),
                         [[Decimal('2')]])

    def test_non_square_multiplication(self):
        self.assertEqual(multiply_matrices([[1, 2, 3]], [[1], [2], [3]]), [[14]])

    def test_2_x_2_times_2_x_1(self):
        self.assertEqual(multiply_matrices([[1, 2], [3, 4]], [[5], [6]]), [[17], [39]])

    def test_dimension_mismatch(self):
        with self.assertRaisesRegex(ValueError, 'n1=3, m2=2'):
            multiply_matrices([[1, 2, 3]], [[1], [2]])

    def test_non_rectangular_matrix(self):
        with self.assertRaisesRegex(ValueError, 'rechteckig'):
            multiply_matrices([[1], [2, 3]], [[1]])

    def test_empty_matrix(self):
        with self.assertRaises(ValueError):
            multiply_matrices([], [[1]])

    def test_invalid_number(self):
        with self.assertRaisesRegex(ValueError, 'Ungültiger'):
            parse_matrix_value('1.2.3')

    def test_nan_or_infinity_are_rejected(self):
        for value in ('NaN', 'Infinity', '-Infinity'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_matrix_value(value)

    def test_format_exact_decimal(self):
        self.assertEqual(format_matrix_value(Decimal('3.2500')), '3.25')
        self.assertEqual(format_matrix_value(Decimal('-0')), '0')

    def test_steps_each_matrix_row(self):
        rows = matrix_calculation_steps([[1, 2, 3], [4, 5, 6]],
                                       [[7, 8], [9, 10], [11, 12]])
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(rows[0]), 2)
        self.assertIn('(1 × 7) + (2 × 9) + (3 × 11) = 58', rows[0][0])
        self.assertIn('(4 × 8) + (5 × 10) + (6 × 12) = 154', rows[1][1])


class SourceIntegrationTests(unittest.TestCase):
    def test_original_painter_widget_preserved(self):
        self.assertIn('self.multiplication_matrix_widget = MultiplicationMatrixFactWidget()', SOURCE)
        self.assertIn('matrix_page_layout.addWidget(self.multiplication_matrix_widget)', SOURCE)
        self.assertIn('matrix_page_layout.addWidget(self.matrix_multiplication_panel)', SOURCE)

    def test_open_fact_switches_matrix_focus(self):
        self.assertIn("self.matrix_multiplication_focus_changed.emit(fact_key == 'matrix_multiplication')", SOURCE)
        self.assertIn('widget.matrix_multiplication_focus_changed.connect(self._set_math_multiplication_focus)', SOURCE)

    def test_restore_logic_on_minimize(self):
        self.assertIn('self._math_multiplication_restore_pending', SOURCE)
        self.assertIn('self._ensure_math_multiplication_workspace_after_restore', SOURCE)
        self.assertIn('self.isMinimized()', SOURCE)

    def test_toolbar_and_two_buttons(self):
        for s in ('QToolBar(', "'m1'", "'n1'", "'m2'", "'n2'", "'Erstellen'", "'Berechnen'"):
            self.assertIn(s, PANEL)

    def test_zeros_are_written_to_empty_edit_fields(self):
        self.assertIn("cell.setText(text)", PANEL)
        self.assertIn("text = '0'", PANEL)

    def test_matrix_result_label_row(self):
        self.assertIn('QLabel(format_matrix_value(value), result_frame)', PANEL)
        self.assertIn('result_grid.addWidget(value_label, i + 1, j)', PANEL)

    def test_new_sources_compile(self):
        compile(PANEL, 'matrix_multiplication_panel.py', 'exec')
        compile((ROOT / 'matrix_multiplication_logic.py').read_text(encoding='utf-8'),
                'matrix_multiplication_logic.py', 'exec')

    def test_main_source_has_only_existing_315_syntax_obstacle(self):
        compat = '\n'.join(line[5:] if line.startswith('lazy ') else line
                           for line in SOURCE.splitlines())
        compile(compat, 'd64_dism.py', 'exec')


if __name__ == '__main__':
    unittest.main()
