from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class PrologKnowledgeLevelFilterStage62Tests(unittest.TestCase):
    def test_combobox_is_embedded_below_selected_level_button(self):
        self.assertIn('self.alternative_host = QWidget(self)', SOURCE)
        self.assertIn('def attach_alternative_controls(', SOURCE)
        self.assertIn('check_button: QPushButton', SOURCE)
        self.assertIn('parent_button.attach_alternative_controls(', SOURCE)
        self.assertIn('self.alternative_host_layout.addWidget(combo)', SOURCE)

    def test_existing_alternative_is_not_insertable_twice(self):
        # Stage 63 supersedes the Stage-62 disabled-row presentation: already
        # visible values are now removed from the alternatives ComboBox.
        self.assertIn('def _remaining_alternatives(self, alternatives):', SOURCE)
        self.assertIn('if str(value).strip().casefold() not in used', SOURCE)

    def test_duplicate_insert_is_rejected_in_current_path(self):
        self.assertIn('used_keys = self._used_decision_texts()', SOURCE)
        self.assertIn('if rendered_key in used_keys:', SOURCE)
        self.assertIn("ist im aktuellen Entscheidungsweg bereits enthalten.", SOURCE)
        self.assertIn('target_level = len(base_prefix)', SOURCE)

    def test_fact_name_filter_controls_exist(self):
        self.assertIn('self.fact_filter_edit = QLineEdit(left_panel)', SOURCE)
        self.assertIn('self.fact_filter_edit.setPlaceholderText("Faktenname filtern …")', SOURCE)
        self.assertIn('self.fact_filter_edit.textChanged.connect(self._fact_name_filter_changed)', SOURCE)
        self.assertIn('needle not in name.casefold()', SOURCE)

    def test_arity_filter_contains_all_and_1_to_100(self):
        self.assertIn('self.fact_arity_combo.addItem("Alle", None)', SOURCE)
        self.assertIn('for arity_value in range(1, 101):', SOURCE)
        self.assertIn('self.fact_arity_combo.addItem(str(arity_value), arity_value)', SOURCE)
        self.assertIn('if wanted_arity is not None and arity != wanted_arity:', SOURCE)

    def test_filter_button_uses_a_funnel_icon(self):
        self.assertIn('def _update_fact_filter_icon(self)', SOURCE)
        self.assertIn('path.lineTo(10.5, 9.2)', SOURCE)
        self.assertIn('self.fact_filter_button.setIcon(QIcon(pixmap))', SOURCE)

    def test_dark_tree_header_is_dark_with_white_title(self):
        self.assertIn('QTreeWidget#prolog_knowledge_fact_tree QHeaderView::section{', SOURCE)
        self.assertIn('background:#161b22;color:#ffffff', SOURCE)

    def test_green_red_alternative_status_logic_is_preserved(self):
        self.assertIn('text = "weitere Alternativen vorhanden"', SOURCE)
        self.assertIn('text = "keine weiteren Alternativen"', SOURCE)
        self.assertIn('self._set_alternative_status(bool(remaining_alternatives))', SOURCE)


if __name__ == "__main__":
    unittest.main()
