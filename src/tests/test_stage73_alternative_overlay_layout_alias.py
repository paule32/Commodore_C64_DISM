from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage73AlternativeOverlayLayoutAliasTests(unittest.TestCase):
    def test_active_lane_load_aliases_overlay_layout(self):
        block = SOURCE[
            SOURCE.index("def _load_query_lane(self, lane"):
            SOURCE.index("def _sync_fact_tree_to_active_lane")
        ]
        self.assertIn(
            "self.alternative_overlay_layout = lane.alternative_overlay_layout",
            block,
        )
        overlay_pos = block.index("self.alternative_overlay = lane.alternative_overlay")
        layout_pos = block.index(
            "self.alternative_overlay_layout = lane.alternative_overlay_layout"
        )
        combo_pos = block.index("self.alternative_combo = lane.alternative_combo")
        self.assertLess(overlay_pos, layout_pos)
        self.assertLess(layout_pos, combo_pos)

    def test_overlay_position_has_runtime_layout_fallback(self):
        block = SOURCE[
            SOURCE.index("def _refresh_alternative_overlay_position"):
            SOURCE.index("def _alternative_combo_selected")
        ]
        self.assertIn(
            'overlay_layout = getattr(self, "alternative_overlay_layout", None)',
            block,
        )
        self.assertIn("overlay_layout = self.alternative_overlay.layout()", block)
        self.assertIn("overlay_layout.spacing()", block)
        self.assertIn("overlay_layout.contentsMargins()", block)

    def test_arrow_still_reaches_visible_combo_and_check_button(self):
        show = SOURCE[
            SOURCE.index("def _show_alternative_overlay"):
            SOURCE.index("def _refresh_alternative_overlay_position")
        ]
        self.assertIn("self.alternative_overlay.show()", show)
        self.assertIn("self.alternative_combo.show()", show)
        self.assertIn("self.alternative_check_button.show()", show)
        self.assertIn("self.alternative_combo.showPopup", show)


if __name__ == "__main__":
    unittest.main()
