from __future__ import annotations

import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
GUI_SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")
PASCAL_SOURCE = (ROOT / "c64pascal" / "compiler.py").read_text(encoding="utf-8")


class GutterMarkerSourceTests(unittest.TestCase):
    def test_two_marker_columns_and_colors_exist(self) -> None:
        self.assertIn('GUTTER_MARKER_COLUMN_WIDTH = 13', GUI_SOURCE)
        self.assertIn('"breakpoint"', GUI_SOURCE)
        self.assertIn('"bookmark"', GUI_SOURCE)
        self.assertIn('QColor("#ff8f8f")', GUI_SOURCE)
        self.assertIn('QColor("#8fd0ff")', GUI_SOURCE)

    def test_left_sets_and_right_removes_marker(self) -> None:
        start = GUI_SOURCE.index("def handle_line_number_area_mouse_press")
        end = GUI_SOURCE.index("def line_number_area_width", start)
        block = GUI_SOURCE[start:end]
        self.assertIn("event.button() == Qt.LeftButton", block)
        self.assertIn("self._set_gutter_marker", block)
        self.assertIn("event.button() == Qt.RightButton", block)
        self.assertIn("self._remove_gutter_marker", block)

    def test_favorites_menu_contains_file_and_line_and_jump(self) -> None:
        self.assertIn('self.favorites_menu = self.menuBar().addMenu("&Favoriten")', GUI_SOURCE)
        self.assertIn('f"Zeile {line_number} — {filename}"', GUI_SOURCE)
        self.assertIn("def _jump_to_favorite", GUI_SOURCE)
        self.assertIn("editor.centerCursor()", GUI_SOURCE)
        self.assertIn("bookmarks_changed.connect", GUI_SOURCE)

    def test_pascal_console_build_receives_breakpoint_lines(self) -> None:
        self.assertIn('compiler_kwargs["breakpoint_lines"]', GUI_SOURCE)
        self.assertIn('document.raw_editor.breakpoint_lines()', GUI_SOURCE)
        self.assertIn('== "Console"', GUI_SOURCE)


class PascalBreakpointInstrumentationTests(unittest.TestCase):
    def test_compile_function_accepts_breakpoint_lines(self) -> None:
        tree = ast.parse(PASCAL_SOURCE)
        functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        }
        compile_fn = functions["compile_pascal_to_assembly"]
        names = [arg.arg for arg in compile_fn.args.kwonlyargs]
        self.assertIn("breakpoint_lines", names)

    def test_ast_instrumentation_uses_readln_not_source_rewrite(self) -> None:
        self.assertIn("def _inject_console_breakpoints", PASCAL_SOURCE)
        start = PASCAL_SOURCE.index("def _inject_console_breakpoints")
        end = PASCAL_SOURCE.index("def compile_pascal_to_assembly", start)
        block = PASCAL_SOURCE[start:end]
        self.assertIn('DesignatorExpression(position, "readln", ())', block)
        self.assertIn("CompoundStatement", block)
        self.assertIn("program.methods", block)


if __name__ == "__main__":
    unittest.main()
