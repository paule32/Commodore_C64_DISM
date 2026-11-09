"""Native PyQt5-GUI-Regressionen fuer Stage 553.

Windows (oder Linux mit Qt-Offscreen):
    set QT_QPA_PLATFORM=offscreen
    python -m unittest -v test_stage553_qt

Ohne PyQt5 werden die GUI-Tests uebersprungen, nicht als bestanden markiert.
"""
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication, QDockWidget, QMainWindow, QSplitter, QToolBar, QScrollArea
    from software_installer import SoftwareInstallerWorkbench
except ImportError:
    QApplication = None


@unittest.skipUnless(QApplication is not None, "PyQt5 ist nicht installiert")
class SoftwareInstallerWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.widget = SoftwareInstallerWorkbench()
        self.widget.resize(1100, 700)
        self.widget.show()
        self.app.processEvents()
        self.widget.apply_initial_widths()

    def tearDown(self):
        self.widget.close()
        self.app.processEvents()

    def test_single_splitter_toolbar_and_tabs(self):
        self.assertNotIsInstance(self.widget, QMainWindow)
        self.assertEqual(len(self.widget.findChildren(QDockWidget)), 0)
        self.assertIsInstance(self.widget.splitter, QSplitter)
        self.assertEqual(self.widget.splitter.orientation(), Qt.Horizontal)
        self.assertIs(self.widget.layout().itemAt(0).widget(), self.widget.filter_bar)
        self.assertIs(self.widget.layout().itemAt(1).widget(), self.widget.splitter)
        self.assertIsInstance(self.widget.filter_bar, QToolBar)
        self.assertFalse(self.widget.filter_bar.isMovable())
        self.assertFalse(self.widget.filter_bar.isFloatable())
        self.assertIs(self.widget.splitter.widget(0), self.widget.files_scroll)
        self.assertIs(self.widget.splitter.widget(1), self.widget.tabs)
        self.assertIsInstance(self.widget.files_scroll, QScrollArea)
        self.assertEqual(self.widget.tabs.count(), 2)
        self.assertEqual(self.widget.tabs.tabText(0), "Archiv")
        self.assertEqual(self.widget.tabs.tabText(1), "Extern")

    def test_initial_split_ratio_and_manual_resize_persists(self):
        self.widget.apply_initial_widths()
        self.app.processEvents()
        before = self.widget.splitter.sizes()
        self.assertAlmostEqual(before[0] / sum(before), 0.25, delta=0.06)
        self.widget.splitter.setSizes([350, 750])
        self.app.processEvents()
        manual = self.widget.splitter.sizes()
        self.widget.apply_initial_widths()
        self.assertEqual(self.widget.splitter.sizes(), manual)

    def test_panel_toggle_arrows(self):
        panel = self.widget.panels["Einstellungen"]
        self.assertTrue(panel.content.isVisible())
        panel.toggle()
        self.assertFalse(panel.content.isVisible())
        self.assertEqual(panel.toggle_button.arrowType(), Qt.DownArrow)
        panel.toggle()
        self.assertTrue(panel.content.isVisible())
        self.assertEqual(panel.toggle_button.arrowType(), Qt.UpArrow)

    def test_add_delete_and_filter(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "readme.txt"
            file.write_text("hello", encoding="utf-8")
            self.widget.project.add_paths("archive", [str(file)])
            self.widget.refresh_tables()
            table = self.widget.tables["archive"]
            self.assertEqual(table.rowCount(), 1)
            self.assertEqual(table.item(0, 0).text(), "readme.txt")
            self.widget.filter_combo.setCurrentIndex(4)  # fehlend
            self.assertTrue(table.isRowHidden(0))
            self.widget.filter_combo.setCurrentIndex(3)  # vorhanden
            self.assertFalse(table.isRowHidden(0))
            table.selectRow(0)
            self.widget.delete_selected_rows("archive")
            self.assertEqual(table.rowCount(), 0)

    def test_dark_light_and_json_roundtrip(self):
        self.widget.set_dark_mode(True)
        self.assertIn("#202329", self.widget.styleSheet())
        self.widget.set_dark_mode(False)
        self.assertIn("#f5f5f5", self.widget.styleSheet())
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "my.installer.json"
            self.widget.project.sections["OnStartup"] = "abc"
            self.widget.project.save(str(file))
            self.assertEqual(self.widget.project.load(str(file)).sections["OnStartup"], "abc")


if __name__ == "__main__":
    unittest.main()
