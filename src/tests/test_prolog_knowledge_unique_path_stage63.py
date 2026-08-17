from pathlib import Path
import unittest

from d64prolog import KnowledgePredicate, PrologKnowledgeBase

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class PrologKnowledgeUniquePathStage63Tests(unittest.TestCase):
    def test_visible_path_values_are_removed_from_combobox(self):
        self.assertIn("def _used_decision_texts(self):", SOURCE)
        self.assertIn("def _remaining_alternatives(self, alternatives):", SOURCE)
        self.assertIn("if str(value).strip().casefold() not in used", SOURCE)

    def test_root_fact_name_is_also_considered_used(self):
        self.assertIn("used.add(str(self.selected_predicate.name).strip().casefold())", SOURCE)

    def test_all_visible_argument_buttons_are_considered_used(self):
        self.assertIn("for value in self.level_values:", SOURCE)
        self.assertIn("used.add(rendered.casefold())", SOURCE)

    def test_combobox_population_uses_only_remaining_alternatives(self):
        self.assertIn("values = self._remaining_alternatives(alternatives)", SOURCE)
        self.assertNotIn("item.setEnabled(False)", SOURCE)

    def test_manual_duplicate_is_rejected_across_entire_path(self):
        self.assertIn("used_keys = self._used_decision_texts()", SOURCE)
        self.assertIn("if rendered_key in used_keys:", SOURCE)
        self.assertIn("im aktuellen Entscheidungsweg bereits enthalten", SOURCE)

    def test_status_label_uses_remaining_alternatives(self):
        self.assertIn("remaining_alternatives = self._remaining_alternatives(alternatives)", SOURCE)
        self.assertIn("self._set_alternative_status(bool(remaining_alternatives))", SOURCE)

    def test_arrow_data_is_filtered_after_path_rebuild(self):
        self.assertIn("root_alternatives = self._remaining_alternatives(", SOURCE)
        self.assertIn("alternatives = self._remaining_alternatives(\n                    self.knowledge_base.alternatives_for_level(", SOURCE)

    def test_model_example_can_offer_same_word_at_later_level_but_gui_filters_it(self):
        # The resolver correctly reports all logical answers. Stage 63 keeps the
        # PROLOG model complete and performs the no-repeat presentation rule in
        # the GUI layer, so the knowledge base itself is not mutilated.
        kb = PrologKnowledgeBase.from_source(
            "apfel(gesund, essbar, gesund).\n"
            "apfel(essbar, gesund, rot).\n",
            filename="stage63.pl",
        )
        pred = KnowledgePredicate("apfel", 3)
        gesund = kb.parse_value("gesund")
        essbar = kb.parse_value("essbar")
        self.assertEqual(kb.alternatives_for_level(pred, ()), ("essbar", "gesund"))
        self.assertEqual(kb.alternatives_for_level(pred, (gesund,)), ("essbar",))
        # Raw PROLOG knowledge still has 'gesund' as the third value; the GUI
        # will suppress it because it is already a visible button.
        self.assertEqual(kb.alternatives_for_level(pred, (gesund, essbar)), ("gesund",))


if __name__ == "__main__":
    unittest.main()
