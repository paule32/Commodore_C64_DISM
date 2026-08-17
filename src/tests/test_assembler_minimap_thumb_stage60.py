from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class AssemblerMiniMapThumbStage60Tests(unittest.TestCase):
    def test_assembler_thumb_minimum_is_120_pixels(self):
        self.assertIn("ASSEMBLER_MIN_VIEWPORT_HEIGHT = 120", SOURCE)
        self.assertIn("self.min_viewport_height", SOURCE)
        self.assertIn(
            "viewport_height = max(\n                self.min_viewport_height,",
            SOURCE,
        )

    def test_generated_assembler_minimap_uses_120_pixel_minimum(self):
        marker = "self.generated_assembly_editor_container = SourceEditorWithMiniMap("
        start = SOURCE.index(marker)
        block = SOURCE[start:start + 420]
        self.assertIn("SourceMiniMap.ASSEMBLER_MIN_VIEWPORT_HEIGHT", block)

    def test_raw_asm_minimap_switches_to_120_pixels(self):
        start = SOURCE.index("def update_syntax_highlighting")
        block = SOURCE[start:start + 7000]
        self.assertIn("self.raw_minimap.set_min_viewport_height(", block)
        self.assertIn("if is_assembler", block)
        self.assertIn("SourceMiniMap.ASSEMBLER_MIN_VIEWPORT_HEIGHT", block)
        self.assertIn("SourceMiniMap.MIN_VIEWPORT_HEIGHT", block)

    def test_drag_mapping_logic_remains_unchanged(self):
        start = SOURCE.index("def _set_scroll_from_thumb_top")
        end = SOURCE.index("def paintEvent", start)
        block = SOURCE[start:end]
        self.assertIn("QStyle.sliderValueFromPosition(", block)
        self.assertIn("self.height() - viewport_rect.height()", block)

    def test_mouse_drag_uses_viewport_rectangle(self):
        start = SOURCE.index("def mousePressEvent", SOURCE.index("class SourceMiniMap"))
        end = SOURCE.index("def wheelEvent", start)
        block = SOURCE[start:end]
        self.assertIn("viewport_rect = self._viewport_rectangle()", block)
        self.assertIn("self._set_scroll_from_thumb_top(", block)
        self.assertIn("self._drag_offset_y", block)


if __name__ == "__main__":
    unittest.main()
