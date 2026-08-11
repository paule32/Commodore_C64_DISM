from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CPP = ROOT / "d64qt5" / "d64qt5_bridge.cpp"


class DBaseConsoleChromeStage17Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cpp = CPP.read_text(encoding="utf-8")

    def test_three_pixel_frame_wraps_console_chrome(self):
        self.assertIn('QFrame *g_console_frame = nullptr;', self.cpp)
        self.assertIn('QFrame *g_debug_frame = nullptr;', self.cpp)
        self.assertIn('" border: 3px solid %1;"', self.cpp)
        self.assertIn('new QMenuBar(g_console_frame)', self.cpp)
        menu = self.cpp.index('console_layout->addWidget(g_menu_bar, 0)')
        editor = self.cpp.index('console_layout->addWidget(g_console, 1)')
        status = self.cpp.index('console_layout->addWidget(g_status_bar, 0)')
        self.assertLess(menu, editor)
        self.assertLess(editor, status)

    def test_border_is_not_on_plaintext_editor_anymore(self):
        self.assertIn('QFrame#dbaseConsoleFrame, QFrame#dbaseDebugFrame', self.cpp)
        self.assertIn('" border: 0px;"', self.cpp)
        self.assertNotIn('" border: 1px solid %2;"', self.cpp)

    def test_editor_has_zero_padding_margin_and_document_margin(self):
        self.assertIn('"  margin: 0px;"', self.cpp)
        self.assertIn('"  padding: 0px;"', self.cpp)
        self.assertIn('g_console->setContentsMargins(0, 0, 0, 0);', self.cpp)
        self.assertNotIn('setViewportMargins(', self.cpp)
        self.assertIn('g_console->document()->setDocumentMargin(0.0);', self.cpp)
        self.assertIn('g_debug->document()->setDocumentMargin(0.0);', self.cpp)

    def test_status_bar_is_fixed_last_row(self):
        self.assertIn('#include <QStatusBar>', self.cpp)
        self.assertIn('new QStatusBar(g_console_frame)', self.cpp)
        self.assertIn('QStringLiteral("dbaseStatusBar")', self.cpp)
        self.assertIn('g_status_bar->setSizeGripEnabled(false);', self.cpp)
        self.assertIn('g_status_bar->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Fixed);', self.cpp)
        self.assertIn('g_status_bar->setFocusPolicy(Qt::StrongFocus);', self.cpp)

    def test_status_bar_style_is_gray_black_and_monospace(self):
        self.assertIn('QStatusBar#dbaseStatusBar', self.cpp)
        self.assertIn('background-color: #909090', self.cpp)
        self.assertIn('color: #000000', self.cpp)
        self.assertIn('QStringLiteral("Consolas")', self.cpp)
        self.assertIn('QStringLiteral("Courier New")', self.cpp)
        self.assertIn('g_status_bar->setFont(chromeFont);', self.cpp)

    def test_status_bar_and_menu_are_outside_scrolling_document(self):
        self.assertIn('new QMenuBar(g_console_frame)', self.cpp)
        self.assertIn('new QStatusBar(g_console_frame)', self.cpp)
        self.assertIn('new QPlainTextEdit(g_console_frame)', self.cpp)
        self.assertIn('console_layout->addWidget(g_console, 1)', self.cpp)

    def test_enter_helper_preserves_trailing_blank_line(self):
        self.assertIn('void ensure_trailing_blank_line(QPlainTextEdit *editor)', self.cpp)
        self.assertIn("endsWith(QLatin1Char('\\n'))", self.cpp)
        self.assertIn('ensure_trailing_blank_line(g_debug);', self.cpp)

    def test_border_color_still_applies_without_recreating_editor(self):
        self.assertIn('g_console_border_color = color;', self.cpp)
        self.assertIn('apply_console_appearance();', self.cpp)
        self.assertNotIn('delete g_console', self.cpp)


if __name__ == "__main__":
    unittest.main()
