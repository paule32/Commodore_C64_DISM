from pathlib import Path
import unittest

from d64prolog import PrologKnowledgeBase

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage74KnowledgeQueryPersistenceTests(unittest.TestCase):
    def test_qsettings_persistence_is_per_database_and_utf8_json(self):
        self.assertIn(
            'self._query_state_settings = QSettings("paule32", "Qt5D64Explorer")',
            SOURCE,
        )
        key_block = SOURCE[
            SOURCE.index("def _query_state_key"):
            SOURCE.index("def _capture_active_query_lane_state")
        ]
        self.assertIn("hashlib.sha256", key_block)
        self.assertIn('prolog_knowledge/query_state_v1/', key_block)
        save_block = SOURCE[
            SOURCE.index("def _save_query_state"):
            SOURCE.index("def _read_query_state")
        ]
        self.assertIn("ensure_ascii=False", save_block)
        self.assertIn("self._query_state_settings.setValue", save_block)
        self.assertIn("self._query_state_settings.sync()", save_block)

    def test_every_lane_persists_predicate_levels_and_open_alternative(self):
        block = SOURCE[
            SOURCE.index("def _serialize_query_lane_state"):
            SOURCE.index("def _save_query_state")
        ]
        for marker in (
            '"predicate": predicate_state',
            '"levels": level_texts',
            '"active_level": int(lane.active_level)',
            '"query_text": str(lane.query_edit.text() or "")',
            '"open": alternative_open',
            '"parent_level": lane.alternative_parent_level',
            '"current_text": alternative_text',
        ):
            self.assertIn(marker, block)

    def test_save_contains_all_lanes_and_active_lane_index(self):
        block = SOURCE[
            SOURCE.index("def _save_query_state"):
            SOURCE.index("def _read_query_state")
        ]
        self.assertIn('"active_lane": int(active_index)', block)
        self.assertIn("for lane in self.query_lanes", block)
        self.assertIn("self._capture_active_query_lane_state()", block)

    def test_database_open_saves_old_workspace_then_restores_new_one(self):
        block = SOURCE[
            SOURCE.index("def open_selected_database"):
            SOURCE.index("def _populate_predicates")
        ]
        save_pos = block.index("self._save_query_state()")
        model_pos = block.index("model = PrologKnowledgeBase.from_file(path)")
        restore_pos = block.index("restored = self._restore_query_state(path)")
        self.assertLess(save_pos, model_pos)
        self.assertLess(model_pos, restore_pos)
        self.assertIn("self._query_state_save_suspended = True", block)
        self.assertIn("gespeicherte Abfrage(n)", block)

    def test_restore_recreates_multiscroll_lanes_and_rebuilds_buttons(self):
        recreate = SOURCE[
            SOURCE.index("def _recreate_query_lanes_for_restore"):
            SOURCE.index("def _find_saved_predicate")
        ]
        self.assertIn("self.query_lanes_layout.removeWidget(lane)", recreate)
        self.assertIn("self._add_query_lane(activate=False)", recreate)
        restore = SOURCE[
            SOURCE.index("def _restore_one_query_lane"):
            SOURCE.index("def _restore_query_state")
        ]
        self.assertIn("self.knowledge_base.parse_value", restore)
        self.assertIn("self.knowledge_base.accepts(predicate, candidate)", restore)
        self.assertIn("self._rebuild_level_buttons()", restore)
        self.assertIn("self._restart_decision()", restore)
        self.assertIn("self._choose_alternative(parent_level)", restore)
        self.assertIn("self.alternative_combo.setCurrentIndex(index)", restore)

    def test_closing_or_hiding_browser_saves_workspace(self):
        close_block = SOURCE[
            SOURCE.index("def _request_close"):
            SOURCE.index("def eventFilter", SOURCE.index("def _request_close"))
        ]
        self.assertIn("self._save_query_state()", close_block)
        dock_block = SOURCE[
            SOURCE.index("def _prolog_knowledge_dock_visibility_changed"):
            SOURCE.index("def _expand_prolog_knowledge_dock")
        ]
        self.assertIn("dialog._save_query_state()", dock_block)

    def test_prolog_term_text_roundtrips_for_saved_levels_including_umlaut(self):
        kb = PrologKnowledgeBase.from_source(
            'apfel(gesund).\napfel(essbar).\näpfel(gesund).\n',
            filename="stage74_state.pl",
        )
        predicate = next(p for p in kb.predicates if p.name == "apfel")
        value = kb.parse_value("gesund")
        text = kb.term_text(value)
        restored = kb.parse_value(text)
        self.assertEqual(kb.term_text(restored), "gesund")
        self.assertTrue(kb.accepts(predicate, (restored,)))
        umlaut_predicate = next(p for p in kb.predicates if p.name == "äpfel")
        self.assertTrue(kb.accepts(umlaut_predicate, (restored,)))


if __name__ == "__main__":
    unittest.main()
