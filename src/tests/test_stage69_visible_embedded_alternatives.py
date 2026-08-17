from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage69VisibleEmbeddedAlternativesTests(unittest.TestCase):
    def test_level_button_explicitly_reports_expanded_size_hint(self):
        marker = SOURCE.index("class KnowledgeLevelButton(QWidget):")
        block = SOURCE[marker:marker + 18000]
        self.assertIn("def _expanded_alternative_height(self) -> int:", block)
        self.assertIn("def _button_row_size_hint(self) -> QSize:", block)
        self.assertIn("def sizeHint(self) -> QSize:", block)
        self.assertIn("def minimumSizeHint(self) -> QSize:", block)
        self.assertIn("row.height() + max(0, int(self.outer_layout.spacing())) + panel_h", block)

    def test_flow_layout_uses_live_widget_hint_and_minimum_size(self):
        marker = SOURCE.index("class KnowledgeFlowLayout(QLayout):")
        block = SOURCE[marker:marker + 5200]
        self.assertIn("hint = widget.sizeHint() if widget is not None else item.sizeHint()", block)
        self.assertIn("hint = hint.expandedTo(widget.minimumSizeHint())", block)
        self.assertIn("hint = hint.expandedTo(widget.minimumSize())", block)

    def test_combo_and_check_are_directly_below_button_row(self):
        marker = SOURCE.index("class KnowledgeLevelButton(QWidget):")
        block = SOURCE[marker:marker + 12500]
        row = block.index("outer_layout.addLayout(button_row)")
        host = block.index("outer_layout.addWidget(self.alternative_host)")
        combo = block.index("self.alternative_host_layout.addWidget(self.embedded_alternative_combo)")
        check = block.index("self.alternative_host_layout.addWidget(\n                self.embedded_alternative_check_button")
        self.assertLess(row, host)
        self.assertLess(combo, check)
        self.assertIn('self.embedded_alternative_check_button = QPushButton(\n                "Prüfen", self.alternative_host', block)

    def test_show_path_forces_nonzero_panel_height_before_flow_relayout(self):
        marker = SOURCE.index("def show_embedded_alternatives(")
        block = SOURCE[marker:marker + 4200]
        self.assertIn("self.alternative_host.show()", block)
        self.assertIn("combo.show()", block)
        self.assertIn("self.embedded_alternative_check_button.show()", block)
        self.assertIn("self._refresh_embedded_alternative_geometry()", block)
        self.assertIn("self.adjustSize()", block)
        geometry_marker = SOURCE.index("def _refresh_embedded_alternative_geometry")
        geometry = SOURCE[geometry_marker:geometry_marker + 3300]
        self.assertIn("self.alternative_host.setFixedHeight(panel_h)", geometry)
        self.assertIn("self.setMinimumSize(target)", geometry)

    def test_flow_host_height_is_recomputed_after_combo_open(self):
        marker = SOURCE.index("def _refresh_active_level_flow_height")
        block = SOURCE[marker:marker + 1800]
        self.assertIn("self.level_flow.heightForWidth(host_width)", block)
        self.assertIn("self.level_button_host.setMinimumHeight(flow_height)", block)
        populate = SOURCE[SOURCE.index("def _populate_alternative_combo("):SOURCE.index("def _alternative_combo_selected", SOURCE.index("def _populate_alternative_combo("))]
        self.assertIn("self._refresh_active_level_flow_height()", populate)
        self.assertIn("QTimer.singleShot(0, self._refresh_active_level_flow_height)", populate)

    def test_local_check_still_inserts_selected_alternative_as_next_button(self):
        marker = SOURCE.index("def _check_embedded_alternative")
        block = SOURCE[marker:marker + 1800]
        self.assertIn("self.query_edit.setText(value)", block)
        self.assertIn("self.add_query_level()", block)
        add = SOURCE[SOURCE.index("def add_query_level"):SOURCE.index("def _rebuild_level_buttons")]
        self.assertIn("self.level_values = base_prefix + [value]", add)
        self.assertIn("self._clear_alternative_controls()", add)
        self.assertIn("self._rebuild_level_buttons()", add)

    def test_combo_font_remains_consolas_courier_new_9pt(self):
        marker = SOURCE.index("self.embedded_alternative_combo = QComboBox")
        block = SOURCE[marker:marker + 2600]
        self.assertIn('embedded_font.setFamilies(["Consolas", "Courier New"])', block)
        self.assertIn("embedded_font.setPointSize(9)", block)
        self.assertIn("self.embedded_alternative_combo.view().setFont(embedded_font)", block)


if __name__ == "__main__":
    unittest.main()
