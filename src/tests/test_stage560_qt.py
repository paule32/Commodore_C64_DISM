"""Stage 560: echte Qt-Synchronisation der drei Session-Tabellen (offscreen)."""
from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PyQt5.QtWidgets import QApplication, QHeaderView
    from software_installer_dialogs import InstallerSessionVariablesDialog
    from software_installer_model import InstallerProject
except ImportError:
    QApplication = None


@unittest.skipUnless(QApplication is not None, "PyQt5 ist nicht installiert")
class Stage560QtTests(unittest.TestCase):
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

    def test_three_headers_are_hidden_but_columns_can_resize(self):
        for panel in self.dialog.panels.values():
            header = panel.table.horizontalHeader()
            self.assertTrue(header.isHidden())
            self.assertEqual(header.sectionResizeMode(0), QHeaderView.Interactive)
            self.assertEqual(header.sectionResizeMode(1), QHeaderView.Stretch)
            self.assertEqual(panel.table.columnWidth(0), 195)

    def test_resize_first_column_updates_other_tables(self):
        self.dialog.panels["product"].table.setColumnWidth(0, 220)
        self.app.processEvents()
        self.assertEqual([panel.table.columnWidth(0)
                          for panel in self.dialog.panels.values()], [220] * 3)

    def test_resize_with_collapsed_panel(self):
        self.dialog.panels["product"].toggle()
        self.dialog.panels["directories"].table.setColumnWidth(0, 240)
        self.app.processEvents()
        self.assertEqual([panel.table.columnWidth(0)
                          for panel in self.dialog.panels.values()], [240] * 3)


if __name__ == "__main__":
    unittest.main()
