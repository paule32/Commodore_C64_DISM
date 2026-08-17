from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class PrologKnowledgeMultiScrollStage65Tests(unittest.TestCase):
    def test_main_scroll_contains_dynamic_query_lanes(self):
        self.assertIn('class KnowledgeQueryLane(QWidget):', SOURCE)
        self.assertIn('self.query_main_scroll = QScrollArea(right_panel)', SOURCE)
        self.assertIn('self.query_main_container = QWidget(self.query_main_scroll)', SOURCE)
        self.assertIn('self.query_lanes_layout = QVBoxLayout(self.query_main_container)', SOURCE)
        self.assertIn('self.query_lanes_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)', SOURCE)

    def test_lane_has_left_add_delete_and_right_inner_scroll(self):
        add = SOURCE.index('self.add_lane_button = QPushButton("Hinzufügen"')
        delete = SOURCE.index('self.delete_lane_button = QPushButton("Löschen"', add)
        scroll = SOURCE.index('self.level_scroll = QScrollArea(self)', delete)
        self.assertLess(add, delete)
        self.assertLess(delete, scroll)
        self.assertIn('row_layout.addWidget(self.command_host, 0, Qt.AlignTop)', SOURCE)
        self.assertIn('row_layout.addWidget(self.level_scroll, 1)', SOURCE)

    def test_inner_scroll_height_is_dynamic(self):
        self.assertIn('MIN_SCROLL_HEIGHT = 170', SOURCE)
        self.assertIn('MAX_SCROLL_HEIGHT = 430', SOURCE)
        self.assertIn('def update_dynamic_height(self) -> None:', SOURCE)
        self.assertIn('hint = self.level_container.sizeHint().height()', SOURCE)
        self.assertIn('self.level_scroll.setFixedHeight(target)', SOURCE)
        self.assertIn('QTimer.singleShot(0, lane.update_dynamic_height)', SOURCE)

    def test_add_inserts_new_independent_lane_after_clicked_lane(self):
        self.assertIn('def _add_query_lane(', SOURCE)
        self.assertIn('position = self.query_lanes.index(after) + 1', SOURCE)
        self.assertIn('self.query_lanes.insert(position, lane)', SOURCE)
        self.assertIn('self.query_lanes_layout.insertWidget(position, lane)', SOURCE)
        self.assertIn('self._activate_query_lane(lane)', SOURCE)

    def test_delete_removes_one_lane_but_keeps_a_minimum_lane(self):
        self.assertIn('def _delete_query_lane(self, lane: KnowledgeQueryLane) -> None:', SOURCE)
        self.assertIn('if len(self.query_lanes) == 1:', SOURCE)
        self.assertIn('self._reset_active_query_lane()', SOURCE)
        self.assertIn('self.query_lanes.pop(index)', SOURCE)
        self.assertIn('lane.deleteLater()', SOURCE)

    def test_each_lane_owns_query_state_and_widgets(self):
        for marker in (
            'self.selected_predicate = None',
            'self.level_values = []',
            'self.level_buttons = []',
            'self.active_level = -1',
            'self.alternative_parent_prefix = ()',
            'self.query_edit = QLineEdit(self.level_container)',
            'self.alternative_combo = QComboBox(self.level_button_host)',
            'self.alternative_check_button = QPushButton("Prüfen", self.level_button_host)',
            'self.alternative_status_label = QLabel("", self.level_container)',
        ):
            self.assertIn(marker, SOURCE)

    def test_switching_lane_saves_and_restores_existing_solution(self):
        self.assertIn('def _store_active_query_lane(self) -> None:', SOURCE)
        self.assertIn('lane.level_values = list(self.level_values)', SOURCE)
        self.assertIn('def _load_query_lane(self, lane: KnowledgeQueryLane) -> None:', SOURCE)
        self.assertIn('self.level_values = list(lane.level_values)', SOURCE)
        self.assertIn('self.selected_predicate = lane.selected_predicate', SOURCE)
        self.assertIn('self._store_active_query_lane()', SOURCE)

    def test_fact_click_targets_active_lane(self):
        self.assertIn('self.fact_tree.itemClicked.connect(self._predicate_selected_for_active_lane)', SOURCE)
        self.assertIn('def _predicate_selected_for_active_lane(', SOURCE)
        self.assertIn('self._predicate_selected(item, column)', SOURCE)
        self.assertIn('self._store_active_query_lane()', SOURCE)

    def test_database_switch_resets_each_lane_without_collapsing_layout(self):
        self.assertIn('lanes = list(self.query_lanes)', SOURCE)
        self.assertIn('for lane in lanes:', SOURCE)
        self.assertIn('self._activate_query_lane(lane, sync_tree=False)', SOURCE)
        self.assertIn('self._reset_active_query_lane(', SOURCE)
        self.assertNotIn('self.query_lanes.clear()', SOURCE)

    def test_stage64_alternative_and_label_logic_remains_per_lane(self):
        self.assertIn('self.alternative_check_button = QPushButton("Prüfen", self.level_button_host)', SOURCE)
        self.assertIn('text = "weitere Alternativen vorhanden"', SOURCE)
        self.assertIn('text = "keine weiteren Alternativen"', SOURCE)
        self.assertIn('self._remaining_alternatives(alternatives)', SOURCE)


if __name__ == '__main__':
    unittest.main()
