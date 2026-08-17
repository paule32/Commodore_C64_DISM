from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class PrologKnowledgeAlternativeCheckStage64Tests(unittest.TestCase):
    def test_local_check_button_exists(self):
        self.assertIn('self.alternative_check_button = QPushButton("Prüfen", right_panel)', SOURCE)
        self.assertIn('"prolog_knowledge_alternative_check_button"', SOURCE)

    def test_local_button_is_embedded_below_combo(self):
        combo_pos = SOURCE.index('self.alternative_host_layout.addWidget(combo)')
        check_pos = SOURCE.index('self.alternative_host_layout.addWidget(check_button)', combo_pos)
        self.assertLess(combo_pos, check_pos)

    def test_shared_controls_move_as_one_group(self):
        self.assertIn('label.setParent(self.alternative_host)', SOURCE)
        self.assertIn('combo.setParent(self.alternative_host)', SOURCE)
        self.assertIn('check_button.setParent(self.alternative_host)', SOURCE)

    def test_check_button_uses_normal_prolog_validation_path(self):
        self.assertIn('def _check_selected_alternative(self) -> None:', SOURCE)
        self.assertIn('value = str(self.alternative_combo.currentText()).strip()', SOURCE)
        self.assertIn('self.query_edit.setText(value)', SOURCE)
        self.assertIn('self.add_query_level()', SOURCE)

    def test_success_removes_combo_and_check_button_before_rebuild(self):
        marker = 'self.level_values = base_prefix + [value]'
        start = SOURCE.index(marker)
        clear_pos = SOURCE.index('self._clear_alternative_controls()', start)
        rebuild_pos = SOURCE.index('self._rebuild_level_buttons()', start)
        self.assertLess(clear_pos, rebuild_pos)

    def test_failed_validation_keeps_controls_for_retry(self):
        method_start = SOURCE.index('def add_query_level(self) -> None:')
        success_start = SOURCE.index('self.level_values = base_prefix + [value]', method_start)
        before_success = SOURCE[method_start:success_start]
        self.assertNotIn('self._clear_alternative_controls()', before_success)

    def test_clear_hides_and_reparents_local_button(self):
        self.assertIn('self.alternative_check_button.setEnabled(False)', SOURCE)
        self.assertIn('self.alternative_check_button.setVisible(False)', SOURCE)
        self.assertIn('self.alternative_check_button.setParent(self.level_button_host)', SOURCE)

    def test_green_red_label_logic_remains(self):
        self.assertIn('text = "weitere Alternativen vorhanden"', SOURCE)
        self.assertIn('text = "keine weiteren Alternativen"', SOURCE)


if __name__ == "__main__":
    unittest.main()
