from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CPP = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")


class DBaseDialogGridPreserveStage26Tests(unittest.TestCase):
    def test_dialog_move_area_is_console_viewport_based(self):
        self.assertIn("g_console->viewport()->width()", CPP)
        self.assertIn("g_console->viewport()->height()", CPP)
        self.assertIn("g_console->viewport()->mapToGlobal(QPoint(0, 0))", CPP)
        self.assertIn("maxGridRow()", CPP)
        self.assertIn("maxGridColumn()", CPP)
        self.assertIn("m_gridColumn", CPP)
        self.assertIn("m_gridRow", CPP)

    def test_dialog_repositions_when_main_window_moves_or_resizes(self):
        self.assertIn("installEventFilter(this);", CPP)
        self.assertIn("bool eventFilter(QObject *watched, QEvent *event) override", CPP)
        self.assertIn("event->type() == QEvent::Move", CPP)
        self.assertIn("event->type() == QEvent::Resize", CPP)
        self.assertIn("QTimer::singleShot(0, this", CPP)
        self.assertIn("repositionToStoredGrid();", CPP)
        self.assertIn("g_console->viewport()->mapToGlobal(QPoint(0, 0))", CPP)

    def test_move_is_quantized_to_character_cells(self):
        self.assertIn("m_startGridColumn + dxCells", CPP)
        self.assertIn("m_startGridRow + dyCells", CPP)
        self.assertIn("m_gridColumn * m_cellWidth", CPP)
        self.assertIn("m_gridRow * m_cellHeight", CPP)

    def test_clear_screen_character_pattern_is_remembered_across_zoom(self):
        self.assertIn("ConsoleClearMode::CharacterPattern", CPP)
        self.assertIn("g_console_clear_char_code", CPP)
        self.assertIn("g_console_clear_char_foreground", CPP)
        self.assertIn("g_console_clear_char_background", CPP)
        self.assertIn("restore_console_clear_pattern_after_grid_change();", CPP)
        self.assertIn("render_console_character_pattern(", CPP)

    def test_normal_output_stops_pattern_restore_to_avoid_overwriting_text(self):
        self.assertIn("editor == g_console && g_console_clear_mode == ConsoleClearMode::CharacterPattern", CPP)
        self.assertIn("g_console_clear_mode = ConsoleClearMode::None;", CPP)


if __name__ == "__main__":
    unittest.main()
