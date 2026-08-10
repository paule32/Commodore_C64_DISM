from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CPP = ROOT / "d64qt5" / "d64qt5_bridge.cpp"


class DBaseQt5StyleStage6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cpp = CPP.read_text(encoding="utf-8")

    def test_black_gui_and_gray_text(self):
        self.assertIn('background-color: #000000', self.cpp)
        self.assertIn('color: #a9a9a9', self.cpp)
        self.assertIn('QPlainTextEdit {', self.cpp)
        self.assertIn('QLineEdit {', self.cpp)

    def test_font_fallback_order(self):
        con = self.cpp.index('QStringLiteral("Consolas")')
        courier_new = self.cpp.index('QStringLiteral("Courier New")')
        courier = self.cpp.index('QStringLiteral("Courier")', courier_new + 1)
        self.assertLess(con, courier_new)
        self.assertLess(courier_new, courier)
        self.assertIn('QFontDatabase::FixedFont', self.cpp)
        self.assertIn('font.setStyleHint(QFont::Monospace)', self.cpp)
        self.assertIn('font.setFixedPitch(true)', self.cpp)

    def test_font_is_synchronized_for_console_debug_and_input(self):
        self.assertIn('g_console->setFont(font)', self.cpp)
        self.assertIn('g_debug->setFont(font)', self.cpp)
        self.assertIn('g_debug_input->setFont(font)', self.cpp)

    def test_zoom_limits_are_9_and_75(self):
        self.assertIn('DBASE_FONT_MIN_PT = 9', self.cpp)
        self.assertIn('DBASE_FONT_MAX_PT = 75', self.cpp)
        self.assertIn('change_font_size(+1)', self.cpp)
        self.assertIn('change_font_size(-1)', self.cpp)

    def test_zoom_buttons_live_in_top_left_tab_bar_corner(self):
        self.assertIn('new QToolButton(g_zoom_widget)', self.cpp)
        self.assertIn('create_zoom_icon(true)', self.cpp)
        self.assertIn('create_zoom_icon(false)', self.cpp)
        self.assertIn('setCornerWidget(g_zoom_widget, Qt::TopLeftCorner)', self.cpp)

    def test_zoom_icons_are_self_drawn_magnifiers(self):
        self.assertIn('painter.drawEllipse', self.cpp)
        self.assertIn('QPointF(13.0, 13.0)', self.cpp)
        self.assertIn('if (plus)', self.cpp)


if __name__ == "__main__":
    unittest.main()
