from pathlib import Path
import unittest

from d64prolog import PrologKnowledgeBase

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage72PredicateLaneStateComboTests(unittest.TestCase):
    def test_fact_selection_is_stored_before_focus_can_reenter_lane(self):
        block = SOURCE[
            SOURCE.index("def _predicate_selected_for_active_lane"):
            SOURCE.index("def _update_fact_filter_icon")
        ]
        select_pos = block.index("self._predicate_selected(item, column)")
        store_pos = block.index("self._store_active_query_lane()")
        focus_pos = block.index("self.query_edit.setFocus(Qt.OtherFocusReason)")
        self.assertLess(select_pos, store_pos)
        self.assertLess(store_pos, focus_pos)

    def test_predicate_selected_no_longer_moves_focus_before_lane_store(self):
        block = SOURCE[
            SOURCE.index("def _predicate_selected(self, item"):
            SOURCE.index("def _clear_alternative_controls")
        ]
        runtime = "\n".join(
            line for line in block.splitlines()
            if not line.lstrip().startswith("#")
        )
        self.assertNotIn("self.query_edit.setFocus(Qt.OtherFocusReason)", runtime)
        self.assertIn("self.selected_predicate = KnowledgePredicate(name, arity)", runtime)
        self.assertIn("self._rebuild_level_buttons()", runtime)
        self.assertIn("self._restart_decision()", runtime)

    def test_focus_on_already_active_lane_does_not_reload_stale_state(self):
        block = SOURCE[
            SOURCE.index("def _activate_query_lane("):
            SOURCE.index("def _run_query_lane_action")
        ]
        same_lane = block[
            block.index("if current is lane:"):
            block.index("if current is not None:")
        ]
        self.assertIn("return", same_lane)
        self.assertNotIn("self._load_query_lane(lane)", same_lane)
        self.assertIn("self._load_query_lane(lane)", block)

    def test_arrow_path_still_opens_stage71_viewport_overlay(self):
        choose = SOURCE[
            SOURCE.index("def _choose_alternative"):
            SOURCE.index("def _set_status", SOURCE.index("def _choose_alternative"))
        ]
        self.assertIn("self.knowledge_base.alternatives_for_level", choose)
        self.assertIn("self._populate_alternative_combo(", choose)
        populate = SOURCE[
            SOURCE.index("def _populate_alternative_combo"):
            SOURCE.index("def _show_alternative_overlay")
        ]
        self.assertIn("self._show_alternative_overlay(parent_button)", populate)
        show = SOURCE[
            SOURCE.index("def _show_alternative_overlay"):
            SOURCE.index("def _refresh_alternative_overlay_position")
        ]
        self.assertIn("self.alternative_combo.show()", show)
        self.assertIn("self.alternative_check_button.show()", show)

    def test_prolog_model_supplies_expected_apfel_alternatives(self):
        kb = PrologKnowledgeBase.from_source(
            """
            apfel(gesund).
            apfel(essbar).
            apfel(obst).
            """,
            filename="stage72_apfel.pl",
        )
        predicate = next(p for p in kb.predicates if p.name == "apfel" and p.arity == 1)
        self.assertEqual(kb.alternatives_for_level(predicate, ()), ("essbar", "gesund", "obst"))


if __name__ == "__main__":
    unittest.main()
