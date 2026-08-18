from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage91FormPanelParentChildTests(unittest.TestCase):
    def _designer_block(self) -> str:
        start = SOURCE.index("DBASE_FORM_COMPONENT_SPECS")
        end = SOURCE.index("# Stage 85: dBase-Tabellendesigner", start)
        return SOURCE[start:end]

    def test_source_parses(self):
        ast.parse(SOURCE)

    def test_palette_captures_selected_panel_as_pending_parent(self):
        block = self._designer_block()
        self.assertIn("self._pending_parent_panel = None", block)
        self.assertIn("def _selected_panel(self):", block)
        self.assertIn('item.component_type == "Panel"', block)
        self.assertIn("self._pending_parent_panel = self._selected_panel()", block)
        self.assertIn("def pending_parent_panel(self):", block)

    def test_parent_is_used_only_when_click_lands_inside_selected_panel(self):
        block = self._designer_block()
        self.assertIn("def _placement_parent(self, scene_pos: QPointF):", block)
        self.assertIn("panel.mapFromScene(QPointF(scene_pos))", block)
        self.assertIn("panel.boundingRect().contains(local)", block)
        self.assertIn("parent_panel = self._placement_parent(event.scenePos())", block)
        self.assertIn("parent_panel=parent_panel", block)

    def test_created_child_uses_graphics_parent_and_local_coordinates(self):
        block = self._designer_block()
        self.assertIn("parent=parent_panel", block)
        self.assertIn("position = parent_panel.mapFromScene(QPointF(scene_pos))", block)
        self.assertIn("item.setZValue(10.0)", block)
        self.assertIn("item.setPos(float(position.x()), float(position.y()))", block)

    def test_nested_panels_are_supported(self):
        block = self._designer_block()
        self.assertIn("def panel_parent(self):", block)
        self.assertIn("def panel_depth(self) -> int:", block)
        self.assertIn("selected.sort(key=lambda item: item.panel_depth(), reverse=True)", block)
        self.assertIn('parent.component_type == "Panel"', block)

    def test_child_move_is_constrained_to_parent_panel(self):
        block = self._designer_block()
        self.assertIn("parent_panel = self.panel_parent()", block)
        self.assertIn("bounds = parent_panel.boundingRect() if parent_panel is not None else self.scene().sceneRect()", block)

    def test_child_resize_uses_scene_bounds_of_parent_and_maps_result_back(self):
        block = self._designer_block()
        self.assertIn("parent_panel.sceneBoundingRect()", block)
        self.assertIn("position = parent_panel.mapFromScene(QPointF(rect.left(), rect.top()))", block)


if __name__ == "__main__":
    unittest.main()
