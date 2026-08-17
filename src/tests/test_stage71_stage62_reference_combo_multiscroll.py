from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage71Stage62ReferenceComboMultiScrollTests(unittest.TestCase):
    def test_stage70_multi_scroll_structure_remains(self):
        block = SOURCE[SOURCE.index("class KnowledgeQueryLane(QWidget):"):SOURCE.index("class PrologKnowledgeDialog(QDialog):")]
        self.assertIn("self.add_lane_button = QPushButton(\"Hinzufügen\"", block)
        self.assertIn("self.delete_lane_button = QPushButton(\"Löschen\"", block)
        self.assertIn("self.level_scroll = QScrollArea(self)", block)
        dialog = SOURCE[SOURCE.index("class PrologKnowledgeDialog(QDialog):"):SOURCE.index("class ExplorerWindow(QMainWindow):")]
        self.assertIn("self.query_main_scroll = QScrollArea(right_panel)", dialog)
        self.assertIn("self.query_lanes = []", dialog)

    def test_selector_is_viewport_child_not_clipped_by_flow_host(self):
        block = SOURCE[SOURCE.index("class KnowledgeQueryLane(QWidget):"):SOURCE.index("class PrologKnowledgeDialog(QDialog):")]
        runtime = "\n".join(line for line in block.splitlines() if not line.lstrip().startswith("#"))
        self.assertIn("self.alternative_overlay = QFrame(self.level_scroll.viewport())", runtime)
        self.assertNotIn("self.alternative_overlay = QFrame(self.level_button_host)", runtime)

    def test_combo_is_positioned_immediately_below_clicked_parent(self):
        block = SOURCE[SOURCE.index("def _refresh_alternative_overlay_position"):SOURCE.index("def _refresh_active_level_flow_height")]
        self.assertIn("viewport = self.level_scroll.viewport()", block)
        self.assertIn("anchor = parent_button.mapTo(viewport, QPoint(0, row_h + 4))", block)
        self.assertIn("x = max(4, int(anchor.x()))", block)
        self.assertIn("y = max(4, int(anchor.y()))", block)
        self.assertIn("self.alternative_overlay.setGeometry(x, y, panel_w, panel_h)", block)
        self.assertIn("self.alternative_overlay.raise_()", block)

    def test_combo_then_local_pruefen_plus_button(self):
        block = SOURCE[SOURCE.index("self.alternative_combo = QComboBox(self.alternative_overlay)"):SOURCE.index("self.alternative_status_label = QLabel")]
        self.assertIn('self.alternative_check_button = QPushButton("Prüfen +", self.alternative_overlay)', block)
        combo_add = block.index("self.alternative_overlay_layout.addWidget(self.alternative_combo)")
        check_add = block.index("self.alternative_overlay_layout.addWidget(self.alternative_check_button)")
        self.assertLess(combo_add, check_add)

    def test_arrow_click_immediately_opens_stage62_style_dropdown(self):
        block = SOURCE[SOURCE.index("def _show_alternative_overlay"):SOURCE.index("def _refresh_alternative_overlay_position")]
        self.assertIn("self.alternative_overlay.show()", block)
        self.assertIn("self.alternative_combo.show()", block)
        self.assertIn("self.alternative_check_button.show()", block)
        self.assertIn("QTimer.singleShot(0, self.alternative_combo.showPopup)", block)

    def test_local_check_uses_existing_prolog_insert_path(self):
        wire = SOURCE[SOURCE.index("def _wire_query_lane"):SOURCE.index("def _store_active_query_lane")]
        self.assertIn("lane.alternative_check_button.clicked.connect", wire)
        self.assertIn("self._check_selected_alternative", wire)
        check = SOURCE[SOURCE.index("def _check_selected_alternative"):SOURCE.index("def _restart_decision")]
        self.assertIn("value = str(self.alternative_combo.currentText()).strip()", check)
        self.assertIn("self.query_edit.setText(value)", check)
        self.assertIn("self.add_query_level()", check)

    def test_success_hides_selector_before_button_path_rebuild(self):
        add = SOURCE[SOURCE.index("def add_query_level"):SOURCE.index("def _rebuild_level_buttons")]
        self.assertIn("self._clear_alternative_controls()", add)
        self.assertIn("self._rebuild_level_buttons()", add)
        clear = SOURCE[SOURCE.index("def _clear_alternative_controls"):SOURCE.index("def _set_alternative_status")]
        self.assertIn("self.alternative_overlay.hide()", clear)
        self.assertIn("self.alternative_combo.setVisible(False)", clear)
        self.assertIn("self.alternative_check_button.setVisible(False)", clear)

    def test_combo_keeps_consolas_courier_new_9pt(self):
        block = SOURCE[SOURCE.index("self.alternative_combo = QComboBox(self.alternative_overlay)"):SOURCE.index("self.alternative_check_button = QPushButton", SOURCE.index("self.alternative_combo = QComboBox(self.alternative_overlay)"))]
        self.assertIn('alternative_font.setFamilies(["Consolas", "Courier New"])', block)
        self.assertIn("alternative_font.setPointSize(9)", block)
        self.assertIn("self.alternative_combo.view().setFont(alternative_font)", block)


if __name__ == "__main__":
    unittest.main()
