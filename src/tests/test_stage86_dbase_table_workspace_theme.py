from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage86DBaseTableWorkspaceThemeTests(unittest.TestCase):
    def _grid_block(self) -> str:
        start = SOURCE.index("class DBaseTableFieldGrid")
        end = SOURCE.index("class DBaseTablePage", start)
        return SOURCE[start:end]

    def _workspace_block(self) -> str:
        start = SOURCE.index("def _ensure_dbase_table_designer")
        end = SOURCE.index("def _create_menu", start)
        return SOURCE[start:end]

    def test_table_designer_is_split_right_of_filesystem_dock(self):
        block = self._workspace_block()
        self.assertIn("self.addDockWidget(Qt.LeftDockWidgetArea, dock)", block)
        self.assertIn("self.splitDockWidget(self.left_dock, dock, Qt.Horizontal)", block)
        self.assertNotIn("self.addDockWidget(Qt.RightDockWidgetArea, dock)", block)
        self.assertIn("[left, self.dbase_table_designer_dock]", block)
        self.assertIn("[320, 100000]", block)

    def test_table_workspace_hides_central_area_but_keeps_filesystem(self):
        block = self._workspace_block()
        self.assertIn("central.hide()", block)
        self.assertIn("left.show()", block)
        self.assertIn("_restore_dbase_table_workspace", block)
        self.assertIn("dock.visibilityChanged.connect", block)

    def test_grid_selects_single_cell_and_uses_navy_focus_color(self):
        block = self._grid_block()
        self.assertIn("QAbstractItemView.SelectItems", block)
        self.assertNotIn("QAbstractItemView.SelectRows", block)
        self.assertIn("background-color:#000080; color:#ffffff", block)

    def test_dark_grid_headers_corner_and_editors_use_requested_colors(self):
        block = self._grid_block()
        self.assertIn("QHeaderView::section", block)
        self.assertIn("background-color:#2a2a2a; color:#ffffff", block)
        self.assertIn("QTableCornerButton::section", block)
        self.assertIn("background-color:#000000", block)
        self.assertIn("QLineEdit", block)
        self.assertIn("QComboBox", block)
        self.assertIn("QSpinBox", block)
        self.assertIn("color:#ffff00", block)

    def test_both_spinboxes_are_exactly_84_pixels_wide(self):
        block = self._grid_block()
        self.assertEqual(block.count("spin.setFixedWidth(84)"), 2)

    def test_dock_title_icons_follow_dark_and_light_mode(self):
        start = SOURCE.index("class DockTitleBar")
        end = SOURCE.index("class OpenFileFilterProxyModel", start)
        block = SOURCE[start:end]
        self.assertIn('icon_color = "#ffffff" if self._dark_mode else "#000000"', block)
        self.assertIn("def set_dark_mode(self, enabled: bool)", block)
        self.assertIn('self.float_button.setIcon(self._symbol_icon("float"))', block)
        self.assertIn('self.close_button.setIcon(self._symbol_icon("close"))', block)
        self.assertIn("elif isinstance(widget, DockTitleBar)", SOURCE)


if __name__ == "__main__":
    unittest.main()
