from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage70AlternativeOverlayVisibilityTests(unittest.TestCase):
    def test_lane_owns_permanent_overlay_under_flow_host(self):
        marker = SOURCE.index("class KnowledgeQueryLane(QWidget):")
        block = SOURCE[marker:marker + 15000]
        self.assertIn("self.alternative_overlay = QFrame(self.level_button_host)", block)
        self.assertIn('"prolog_knowledge_alternative_overlay"', block)
        self.assertIn("self.alternative_overlay_layout = QVBoxLayout(self.alternative_overlay)", block)
        self.assertIn("self.alternative_combo = QComboBox(self.alternative_overlay)", block)
        self.assertIn('self.alternative_check_button = QPushButton("Prüfen", self.alternative_overlay)', block)

    def test_overlay_has_combo_then_check_button(self):
        marker = SOURCE.index("self.alternative_overlay = QFrame(self.level_button_host)")
        block = SOURCE[marker:marker + 6500]
        combo = block.index("self.alternative_overlay_layout.addWidget(self.alternative_combo)")
        check = block.index("self.alternative_overlay_layout.addWidget(self.alternative_check_button)")
        self.assertLess(combo, check)

    def test_arrow_path_shows_overlay_instead_of_reparenting(self):
        marker = SOURCE.index("def _populate_alternative_combo(")
        block = SOURCE[marker:marker + 8000]
        self.assertIn("self._show_alternative_overlay(parent_button)", block)
        self.assertIn("combo.setCurrentIndex(0)", block)
        self.assertIn("combo.setVisible(True)", block)
        self.assertIn("self.alternative_check_button.setVisible(True)", block)
        runtime = "\n".join(
            line for line in block.splitlines()
            if "compatibility marker" not in line.lower() and not line.lstrip().startswith("#")
        )
        self.assertNotIn("setParent(", runtime)

    def test_overlay_position_is_directly_below_parent_button_row(self):
        marker = SOURCE.index("def _refresh_alternative_overlay_position")
        block = SOURCE[marker:marker + 5200]
        self.assertIn("button_rect = parent_button.geometry()", block)
        self.assertIn("row_h = max(32, int(parent_button._button_row_size_hint().height()))", block)
        self.assertIn("y = int(button_rect.y()) + row_h + 4", block)
        self.assertIn("self.alternative_overlay.setGeometry(x, y, panel_w, panel_h)", block)
        self.assertIn("self.alternative_overlay.raise_()", block)
        self.assertIn("self.alternative_overlay.show()", block)

    def test_host_reserves_space_for_overlay_to_prevent_clipping(self):
        marker = SOURCE.index("def _refresh_alternative_overlay_position")
        block = SOURCE[marker:marker + 5200]
        self.assertIn("required_h = y + panel_h + 8", block)
        self.assertIn("host.setMinimumHeight(max(base_h, required_h))", block)
        refresh = SOURCE[SOURCE.index("def _refresh_active_level_flow_height"):SOURCE.index("def _alternative_combo_selected")]
        self.assertIn("overlay_bottom = int(self.alternative_overlay.geometry().bottom()) + 8", refresh)
        self.assertIn("flow_height = max(flow_height, overlay_bottom)", refresh)

    def test_check_button_still_uses_existing_prolog_validation(self):
        wire = SOURCE[SOURCE.index("def _wire_query_lane"):SOURCE.index("def _store_active_query_lane")]
        self.assertIn("lane.alternative_check_button.clicked.connect", wire)
        self.assertIn("self._check_selected_alternative", wire)
        check = SOURCE[SOURCE.index("def _check_selected_alternative"):SOURCE.index("def _restart_decision")]
        self.assertIn("value = str(self.alternative_combo.currentText()).strip()", check)
        self.assertIn("self.query_edit.setText(value)", check)
        self.assertIn("self.add_query_level()", check)

    def test_success_path_clears_overlay_then_rebuilds_button_path(self):
        add = SOURCE[SOURCE.index("def add_query_level"):SOURCE.index("def _rebuild_level_buttons")]
        self.assertIn("self._clear_alternative_controls()", add)
        self.assertIn("self._rebuild_level_buttons()", add)
        clear = SOURCE[SOURCE.index("def _clear_alternative_controls"):SOURCE.index("def _set_alternative_status")]
        self.assertIn("self.alternative_overlay.hide()", clear)
        self.assertIn("self.alternative_combo.setVisible(False)", clear)
        self.assertIn("self.alternative_check_button.setVisible(False)", clear)

    def test_combo_font_is_still_consolas_courier_new_9pt(self):
        marker = SOURCE.index("self.alternative_combo = QComboBox(self.alternative_overlay)")
        block = SOURCE[marker:marker + 3200]
        self.assertIn('alternative_font.setFamilies(["Consolas", "Courier New"])', block)
        self.assertIn("alternative_font.setPointSize(9)", block)
        self.assertIn("self.alternative_combo.view().setFont(alternative_font)", block)


if __name__ == "__main__":
    unittest.main()
