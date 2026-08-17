from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')


class PrologKnowledgeDockComboStage66Tests(unittest.TestCase):
    def test_browser_has_embedded_mode_for_dock_payload(self):
        self.assertIn('embedded: bool = False', SOURCE)
        self.assertIn('self.setWindowFlags(Qt.Widget)', SOURCE)
        self.assertIn('dock_close_requested = pyqtSignal()', SOURCE)

    def test_main_window_creates_knowledge_dock_in_left_area(self):
        self.assertIn('dock = QDockWidget("PROLOG – Wissen-Datenbanken", self)', SOURCE)
        self.assertIn('dock.setObjectName("prolog_knowledge_dock")', SOURCE)
        self.assertIn('self.addDockWidget(Qt.LeftDockWidgetArea, dock)', SOURCE)
        self.assertIn('embedded=True', SOURCE)

    def test_filesystem_dock_is_swapped_and_restored(self):
        self.assertIn('self.left_dock.hide()', SOURCE)
        self.assertIn('self.left_dock.show()', SOURCE)
        self.assertIn('_knowledge_replaced_filesystem_dock', SOURCE)
        self.assertIn('def _prolog_knowledge_dock_visibility_changed', SOURCE)

    def test_reparented_alternative_controls_are_shown_again(self):
        marker = SOURCE.index('def attach_alternative_controls(')
        block = SOURCE[marker: marker + 2600]
        self.assertIn('combo.setParent(self.alternative_host)', block)
        self.assertIn('label.show()', block)
        self.assertIn('combo.show()', block)
        self.assertIn('check_button.show()', block)
        self.assertGreater(block.index('combo.show()'), block.index('combo.setParent(self.alternative_host)'))

    def test_combo_font_is_consolas_with_courier_new_fallback_at_9pt(self):
        self.assertIn('alternative_font.setFamilies(["Consolas", "Courier New"])', SOURCE)
        self.assertIn('alternative_font.setPointSize(9)', SOURCE)
        self.assertIn('self.alternative_combo.setFont(alternative_font)', SOURCE)
        self.assertIn('self.alternative_combo.view().setFont(alternative_font)', SOURCE)

    def test_searchable_combo_completer_popup_uses_same_font(self):
        self.assertIn('completer.popup().setFont(self.alternative_combo.font())', SOURCE)

    def test_combo_remains_attached_below_clicked_parent(self):
        self.assertIn('parent_button.attach_alternative_controls(', SOURCE)
        self.assertIn('self.alternative_host_layout.addWidget(combo)', SOURCE)
        self.assertIn('self.alternative_host_layout.addWidget(check_button)', SOURCE)

    def test_lane_height_is_refreshed_after_combo_is_shown(self):
        marker = SOURCE.index('def _populate_alternative_combo(')
        block = SOURCE[marker: marker + 5000]
        self.assertIn('lane.update_dynamic_height()', block)
        self.assertIn('QTimer.singleShot(0, lane.update_dynamic_height)', block)


if __name__ == '__main__':
    unittest.main()
