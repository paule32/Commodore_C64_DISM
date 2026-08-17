from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage88TableWorkspacePreservesProjectLogTests(unittest.TestCase):
    def _workspace_block(self) -> str:
        start = SOURCE.index("def _enter_dbase_table_workspace")
        end = SOURCE.index("def _restore_dbase_table_workspace", start)
        return SOURCE[start:end]

    def test_project_information_and_log_docks_are_not_hidden(self):
        block = self._workspace_block()
        self.assertIn('"right": getattr(self, "right_dock", None)', block)
        self.assertIn('"bottom": getattr(self, "bottom_dock", None)', block)
        self.assertIn('for name in ("localize", "knowledge")', block)
        self.assertNotIn('for name in ("right", "bottom", "localize", "knowledge")', block)
        self.assertIn("Projekt/Informationen", block)
        self.assertIn("Log-Dock", block)


if __name__ == "__main__":
    unittest.main()
