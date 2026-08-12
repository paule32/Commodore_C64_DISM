from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CPP = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")


class DBaseDialogPartialOffscreenStage28Tests(unittest.TestCase):
    def test_vertical_anchor_can_reach_last_text_row(self):
        self.assertIn("const int usableRows = qMin(DBASE_TEXT_ROWS, viewportRows);", CPP)
        self.assertIn("return qMax(0, usableRows - 1);", CPP)
        self.assertIn("groesste Startzeile deshalb 24", CPP)

    def test_right_edge_keeps_two_character_cells_visible(self):
        self.assertIn("const int usableColumns = qMin(DBASE_TEXT_COLUMNS, viewportColumns);", CPP)
        self.assertIn("return qMax(0, usableColumns - 2);", CPP)
        self.assertIn("groesste Startspalte 78", CPP)

    def test_dialog_is_clipped_to_console_viewport(self):
        self.assertIn("#include <QRegion>", CPP)
        self.assertIn("void updateViewportClipMask()", CPP)
        self.assertIn("const QRect viewportGlobal(viewportOrigin, g_console->viewport()->size());", CPP)
        self.assertIn("const QRect visibleGlobal = dialogGlobal.intersected(viewportGlobal);", CPP)
        self.assertIn("setMask(QRegion(visibleLocal));", CPP)
        self.assertIn("updateViewportClipMask();", CPP)

    def test_move_origin_is_console_viewport_below_menu(self):
        self.assertIn("g_console->viewport()->mapToGlobal(QPoint(0, 0))", CPP)
        self.assertIn("origin.y() + m_gridRow * m_cellHeight", CPP)
        self.assertIn("origin.x() + m_gridColumn * m_cellWidth", CPP)

    def test_initial_dialog_remains_fully_visible_and_centered(self):
        self.assertIn("(DBASE_TEXT_COLUMNS - DBASE_LOGIN_DIALOG_COLUMNS) / 2", CPP)
        self.assertIn("(DBASE_TEXT_ROWS - DBASE_LOGIN_DIALOG_ROWS) / 2", CPP)
        self.assertIn("setStoredGridPosition(initialColumn, initialRow);", CPP)

    def test_grid_still_80_by_25(self):
        self.assertRegex(CPP, r"constexpr int DBASE_TEXT_COLUMNS\s*=\s*80;")
        self.assertRegex(CPP, r"constexpr int DBASE_TEXT_ROWS\s*=\s*25;")


if __name__ == "__main__":
    unittest.main()
