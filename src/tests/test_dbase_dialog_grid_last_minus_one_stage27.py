from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CPP = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")


class DBaseDialogGridStage27CompatibilityTests(unittest.TestCase):
    """Stage 27 was superseded by the less restrictive Stage 28 move range."""

    def test_grid_position_is_still_clamped(self):
        self.assertIn("m_gridColumn = qBound(0, column, maxGridColumn());", CPP)
        self.assertIn("m_gridRow = qBound(0, row, maxGridRow());", CPP)

    def test_dialog_is_still_raster_quantized(self):
        self.assertIn("m_startGridColumn + dxCells", CPP)
        self.assertIn("m_startGridRow + dyCells", CPP)
        self.assertIn("m_gridColumn * m_cellWidth", CPP)
        self.assertIn("m_gridRow * m_cellHeight", CPP)

    def test_stage28_supersedes_full_visibility_limit(self):
        self.assertNotIn(
            "DBASE_TEXT_COLUMNS - DBASE_LOGIN_DIALOG_COLUMNS - 1",
            CPP,
        )
        self.assertNotIn(
            "DBASE_TEXT_ROWS - DBASE_LOGIN_DIALOG_ROWS - 1",
            CPP,
        )
        self.assertIn("return qMax(0, usableColumns - 2);", CPP)
        self.assertIn("return qMax(0, usableRows - 1);", CPP)


if __name__ == "__main__":
    unittest.main()
