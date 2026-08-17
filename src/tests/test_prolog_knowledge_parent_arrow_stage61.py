from pathlib import Path
import unittest

from d64prolog import KnowledgePredicate, PrologKnowledgeBase


ROOT = Path(__file__).resolve().parents[1]
GUI = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class PrologKnowledgeParentArrowStage61Tests(unittest.TestCase):
    def test_level_arrow_is_visible_when_children_exist(self):
        self.assertIn(
            "self.arrow_button.setVisible(bool(self.alternatives))",
            GUI,
        )

    def test_root_button_receives_first_level_alternatives(self):
        self.assertIn(
            "root_alternatives = self._remaining_alternatives(",
            GUI,
        )
        self.assertIn("alternatives=root_alternatives", GUI)

    def test_child_button_receives_only_children_below_its_prefix(self):
        self.assertIn("prefix.append(value)", GUI)
        self.assertIn(
            "self.selected_predicate, tuple(prefix)",
            GUI,
        )

    def test_arrow_opens_parent_bound_combobox(self):
        self.assertIn("parent_prefix = ()", GUI)
        self.assertIn("self.level_values[: level_index + 1]", GUI)
        self.assertIn("self._alternative_parent_prefix = tuple(parent_prefix)", GUI)
        self.assertIn("self.alternative_combo.showPopup()", GUI)

    def test_combobox_is_hidden_until_parent_arrow_is_clicked(self):
        self.assertIn("self.alternative_label.setVisible(False)", GUI)
        self.assertIn("self.alternative_combo.setVisible(False)", GUI)
        self.assertIn("self.alternative_combo.setVisible(True)", GUI)

    def test_selected_child_is_inserted_under_the_clicked_parent(self):
        self.assertIn("base_prefix = list(self._alternative_parent_prefix)", GUI)
        self.assertIn("candidate = tuple(base_prefix) + (value,)", GUI)
        self.assertIn("self.level_values = base_prefix + [value]", GUI)

    def test_model_progresses_parent_to_child(self):
        kb = PrologKnowledgeBase.from_source(
            "obst(apfel, gesund, rot).\n"
            "obst(apfel, gesund, gruen).\n"
            "obst(apfel, essbar, ja).\n"
            "obst(birne, gesund, gruen).\n",
            filename="stage61.pl",
        )
        pred = KnowledgePredicate("obst", 3)
        self.assertEqual(kb.alternatives_for_level(pred, ()), ("apfel", "birne"))
        apfel = kb.parse_value("apfel")
        gesund = kb.parse_value("gesund")
        self.assertEqual(
            kb.alternatives_for_level(pred, (apfel,)),
            ("essbar", "gesund"),
        )
        self.assertEqual(
            kb.alternatives_for_level(pred, (apfel, gesund)),
            ("gruen", "rot"),
        )

    def test_delete_path_still_redraws_alternative_state(self):
        self.assertIn("self._clear_alternative_controls()\n            if level_index < 0:", GUI)
        self.assertIn("self._rebuild_level_buttons()\n            self._restart_decision()", GUI)


if __name__ == "__main__":
    unittest.main()
