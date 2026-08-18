from __future__ import annotations

import ast
import base64
import io
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage92FormBrushPatternTests(unittest.TestCase):
    def _designer_block(self) -> str:
        start = SOURCE.index("DBASE_FORM_COMPONENT_SPECS")
        end = SOURCE.index("# Stage 85: dBase-Tabellendesigner", start)
        return SOURCE[start:end]

    def test_source_parses(self):
        ast.parse(SOURCE)

    def test_resize_preview_is_light_gray(self):
        block = self._designer_block()
        self.assertIn("Resize-Vorschau bewusst hellgrau", block)
        self.assertIn("QColor(205, 205, 205)", block)

    def test_brush_root_contains_background_foreground_and_style(self):
        block = self._designer_block()
        self.assertIn('QTreeWidgetItem(self.property_tree, ["Brush", ""])', block)
        self.assertIn('"Background", parent_item=self.brush_root', block)
        self.assertIn('"Foreground", parent_item=self.brush_root', block)
        self.assertIn('"Style", self.brush_style_combo, parent_item=self.brush_root', block)
        self.assertIn('self.brush_style_combo.setIconSize(QSize(72, 36))', block)

    def test_twelve_reference_patterns_are_embedded_without_external_dependency(self):
        tree = ast.parse(SOURCE)
        run_gui = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "run_gui"
        )
        assignment = next(
            node for node in run_gui.body
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "DBASE_FORM_BRUSH_PATTERNS" for t in node.targets)
        )
        values = ast.literal_eval(assignment.value)
        self.assertEqual(len(values), 12)
        for name, encoded in values:
            self.assertTrue(name)
            image = Image.open(io.BytesIO(base64.b64decode(encoded)))
            self.assertEqual(image.size, (48, 48))
            self.assertEqual(image.mode, "L")
            extrema = image.getextrema()
            self.assertEqual(extrema, (0, 255))

    def test_patterns_are_recolored_from_background_and_foreground(self):
        block = self._designer_block()
        self.assertIn("Schwarz = Foreground, Weiss = Background", block)
        self.assertIn("fg if mask_color.value() < 128 else bg", block)
        self.assertIn("_dbase_form_pattern_icon(style_index, bg, fg)", block)
        self.assertIn("painter.fillRect(self.boundingRect(), QBrush(tile))", block)
        self.assertIn("def set_brush_style", block)

    def test_button_background_and_text_color_are_forced_visible(self):
        block = self._designer_block()
        self.assertIn('if self.component_type == "Button":', block)
        self.assertIn("background-color: {bg.name()}", block)
        self.assertIn("color: {fg.name()}", block)
        self.assertIn("background-color: transparent", block)

    def test_pattern_reference_sheet_is_packaged(self):
        path = ROOT / "FORM_BRUSH_PATTERNS_STAGE92.png"
        self.assertTrue(path.is_file())
        with Image.open(path) as image:
            self.assertGreater(image.width, 100)
            self.assertGreater(image.height, 100)


if __name__ == "__main__":
    unittest.main()
