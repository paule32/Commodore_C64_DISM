from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage89SettingsPreserveProjectLogTests(unittest.TestCase):
    def _workspace_block(self) -> str:
        start = SOURCE.index("def _enter_settings_workspace")
        end = SOURCE.index("def _restore_settings_workspace", start)
        return SOURCE[start:end]

    def _show_block(self) -> str:
        start = SOURCE.index("def show_settings_dock")
        end = SOURCE.index("def _create_menu", start)
        return SOURCE[start:end]

    def test_source_parses(self):
        ast.parse(SOURCE)

    def test_settings_workspace_does_not_hide_project_or_log(self):
        block = self._workspace_block()
        self.assertIn('right = managed_docks.get("right")', block)
        self.assertIn('bottom = managed_docks.get("bottom")', block)
        self.assertIn('right.show()', block)
        self.assertIn('bottom.show()', block)
        self.assertIn('for name in ("localize", "knowledge", "table", "form_props", "form_designer")', block)
        self.assertNotIn('for name, dock in managed_docks.items():\n                if name == "left"', block)

    def test_show_settings_explicitly_reveals_project_and_log(self):
        block = self._show_block()
        self.assertIn('right = getattr(self, "right_dock", None)', block)
        self.assertIn('bottom = getattr(self, "bottom_dock", None)', block)
        self.assertIn('right.show()', block)
        self.assertIn('bottom.show()', block)


if __name__ == "__main__":
    unittest.main()
