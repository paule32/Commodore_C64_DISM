# -*- coding: utf-8 -*-
"""Stage 570: opt-in PyQt5-GUI-Smoketests (Windows/Linux offscreen)."""
import importlib.util
import os
import unittest

HAS_QT = importlib.util.find_spec('PyQt5') is not None


@unittest.skipUnless(HAS_QT, 'PyQt5 ist in dieser Umgebung nicht installiert')
class MatrixPanelQtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        from PyQt5.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])
        from matrix_multiplication_panel import MatrixMultiplicationPanel
        cls.panel_type = MatrixMultiplicationPanel

    def setUp(self):
        self.panel = self.panel_type()

    def tearDown(self):
        self.panel.close()
        self.panel.deleteLater()

    def test_toolbar_and_four_dimensions(self):
        self.assertEqual(self.panel._dimensions(), (2, 3, 3, 2))
        self.assertEqual(self.panel.create_button.text(), 'Erstellen')
        self.assertEqual(self.panel.calculate_button.text(), 'Berechnen')

    def test_create_and_calculate(self):
        a = [[1, 2, 3], [4, 5, 6]]
        b = [[7, 8], [9, 10], [11, 12]]
        for i, row in enumerate(a):
            for j, value in enumerate(row):
                self.panel.entries_a[i][j].setText(str(value))
        for i, row in enumerate(b):
            for j, value in enumerate(row):
                self.panel.entries_b[i][j].setText(str(value))
        self.panel.calculate()
        self.assertEqual(self.panel.last_result, [[58, 64], [139, 154]])
        self.assertTrue(self.panel.steps_box.isVisible() or not self.panel.isVisible())

    def test_blank_fields_written_as_zero(self):
        self.panel.calculate()
        self.assertEqual(self.panel.entries_a[0][0].text(), '0')
        self.assertEqual(self.panel.entries_b[0][0].text(), '0')
        self.assertEqual(self.panel.last_result[0][0], 0)

    def test_style_toggle(self):
        self.panel.set_dark_mode(False)
        self.assertFalse(self.panel._dark_mode)
        self.panel.set_dark_mode(True)
        self.assertTrue(self.panel._dark_mode)


if __name__ == '__main__':
    unittest.main()
