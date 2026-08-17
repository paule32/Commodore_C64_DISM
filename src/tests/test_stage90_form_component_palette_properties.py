from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage90FormComponentPalettePropertyTests(unittest.TestCase):
    def _designer_block(self) -> str:
        start = SOURCE.index("DBASE_FORM_COMPONENT_SPECS")
        end = SOURCE.index("# Stage 85: dBase-Tabellendesigner", start)
        return SOURCE[start:end]

    def test_source_parses(self):
        ast.parse(SOURCE)

    def test_standard_palette_contains_requested_control_types(self):
        block = self._designer_block()
        for name in (
            "Button", "CheckBox", "RadioButton", "ComboBox", "Label", "Image",
            "Panel", "TableGrid", "VScrollBar", "HScrollBar", "StatusBar",
            "ToolBar", "Menu",
        ):
            self.assertIn(f'"{name}"', block)
        self.assertIn("_populate_standard_palette", block)
        self.assertIn("itemClicked.connect(self._component_palette_clicked)", block)

    def test_palette_click_sets_one_shot_scene_placement_flag(self):
        block = self._designer_block()
        self.assertIn("self._pending_component_type", block)
        self.assertIn("def set_pending_component", block)
        self.assertIn("self.create_control(component_type, event.scenePos())", block)
        self.assertIn('self.set_pending_component("")', block)
        self.assertIn("Qt.CrossCursor", block)

    def test_controls_are_real_widgets_embedded_with_graphics_proxy(self):
        block = self._designer_block()
        self.assertIn("QGraphicsProxyWidget", SOURCE)
        self.assertIn("self.proxy = QGraphicsProxyWidget(self)", block)
        self.assertIn("self.proxy.setWidget(self.control_widget)", block)
        self.assertIn("self.control_widget.winId()", block)
        for qt_control in (
            "QPushButton", "QCheckBox", "QRadioButton", "QComboBox", "QLabel",
            "QTableWidget", "QScrollBar", "QStatusBar", "QToolBar", "QMenuBar",
        ):
            self.assertIn(qt_control, block)

    def test_property_tree_has_position_group_and_requested_properties(self):
        block = self._designer_block()
        self.assertIn('QTreeWidget(properties_page)', block)
        self.assertIn('setHeaderLabels(("Key", "Value"))', block)
        self.assertIn('QTreeWidgetItem(self.property_tree, ["Position", ""])', block)
        self.assertIn("setFirstColumnSpanned(0, QModelIndex(), True)", block)
        self.assertIn("itemDoubleClicked.connect(self._property_item_double_clicked)", block)
        for name in (
            "Top", "Left", "Width", "Height", "HWND", "Name",
            "Hintergrundfarbe", "Schriftfarbe", "Schriftart", "Font", "Fett", "Kursiv",
        ):
            self.assertIn(f'"{name}"', block)

    def test_position_root_and_dark_header_use_requested_colors(self):
        block = self._designer_block()
        self.assertIn("QColor(0, 0, 128)", block)
        self.assertIn("QColor(255, 255, 0)", block)
        self.assertIn("background:#2a2a2a;color:#ffffff", block)
        self.assertIn("background:#000000;color:#ffff00", block)

    def test_component_properties_apply_to_control(self):
        block = self._designer_block()
        self.assertIn("def set_component_name", block)
        self.assertIn("def set_background_color", block)
        self.assertIn("def set_foreground_color", block)
        self.assertIn("def set_font_family", block)
        self.assertIn("def set_font_point_size", block)
        self.assertIn("def set_font_bold", block)
        self.assertIn("def set_font_italic", block)
        self.assertIn("font.setBold", block)
        self.assertIn("font.setItalic", block)

    def test_form_property_theme_updates_live(self):
        self.assertIn("elif isinstance(widget, DBaseFormPropertyPanel):", SOURCE)
        self.assertIn("widget.set_dark_mode(enabled)", SOURCE)


if __name__ == "__main__":
    unittest.main()
