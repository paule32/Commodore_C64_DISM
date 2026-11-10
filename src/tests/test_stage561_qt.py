"""Stage 561: native PyQt5-Interaktion direkt an der Zellengrenze."""
from __future__ import annotations

import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PyQt5.QtCore import Qt, QPoint
    from PyQt5.QtTest import QTest
    from PyQt5.QtWidgets import QApplication
    from software_installer_dialogs import InstallerSessionVariablesDialog
    from software_installer_model import InstallerProject
except ImportError:
    QApplication = None


@unittest.skipUnless(QApplication is not None, 'PyQt5 ist nicht installiert')
class Stage561QtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.dialog = InstallerSessionVariablesDialog(InstallerProject(), dark_mode=True)
        self.dialog.show()
        self.app.processEvents()

    def tearDown(self):
        self.dialog.close()
        self.app.processEvents()

    def test_header_is_hidden_on_every_panel(self):
        for panel in self.dialog.panels.values():
            self.assertTrue(panel.table.horizontalHeader().isHidden())

    def test_drag_on_cell_border_updates_every_table(self):
        table = self.dialog.panels['product'].table
        self.dialog.scroll.ensureWidgetVisible(table)
        self.app.processEvents()
        boundary = table.columnViewportPosition(1)
        self.assertGreater(boundary, 0)
        viewport = table.viewport()
        QTest.mouseMove(viewport, QPoint(boundary, 12))
        QTest.mousePress(viewport, Qt.LeftButton, pos=QPoint(boundary, 12))
        QTest.mouseMove(viewport, QPoint(boundary + 30, 12))
        QTest.mouseRelease(viewport, Qt.LeftButton, pos=QPoint(boundary + 30, 12))
        self.app.processEvents()
        self.assertEqual([panel.table.columnWidth(0) for panel in self.dialog.panels.values()],
                         [225] * 3)

    def test_custom_empty_panel_is_accessible(self):
        table = self.dialog.panels['custom'].table
        self.assertGreaterEqual(table.height(), 28)
        self.assertEqual(table.rowCount(), 0)


if __name__ == '__main__':
    unittest.main()
