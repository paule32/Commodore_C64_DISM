from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CPP = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")


class DBaseConsoleGridStage19Tests(unittest.TestCase):
    def test_standard_grid_is_80_by_25(self):
        self.assertIn("constexpr int DBASE_TEXT_COLUMNS = 80;", CPP)
        self.assertIn("constexpr int DBASE_TEXT_ROWS = 25;", CPP)
        self.assertIn("DBASE_TEXT_COLUMNS * cellWidth", CPP)
        self.assertIn("DBASE_TEXT_ROWS * lineHeight", CPP)

    def test_grid_uses_real_font_metrics(self):
        self.assertIn("QFontMetrics fm(font);", CPP)
        self.assertIn("fm.horizontalAdvance(QLatin1Char('M'))", CPP)
        self.assertIn("fm.lineSpacing()", CPP)
        self.assertIn("console_grid_pixel_size", CPP)

    def test_zoom_is_exactly_one_point(self):
        self.assertIn("change_font_size(+1);", CPP)
        self.assertIn("change_font_size(-1);", CPP)
        self.assertIn("g_font_point_size = next;", CPP)
        self.assertIn("enforce_console_80x25_grid();", CPP)

    def test_pixel_fine_tuning_is_separate_from_point_size(self):
        self.assertIn("int g_font_pixel_adjust = 0;", CPP)
        self.assertIn("const int adjustments[2] = { -1, +1 };", CPP)
        self.assertIn("QFontInfo(font).pixelSize()", CPP)
        self.assertIn("font.setPixelSize", CPP)
        self.assertIn("g_font_pixel_adjust = bestAdjust;", CPP)

    def test_window_is_resized_from_viewport_difference(self):
        self.assertIn("g_console->viewport()->size()", CPP)
        self.assertIn("target.width() - actual.width()", CPP)
        self.assertIn("target.height() - actual.height()", CPP)
        self.assertIn("g_window->resize(", CPP)
        self.assertNotIn("g_window->resize(900, 600);", CPP)

    def test_initial_show_enforces_grid(self):
        show = CPP.index('extern "C" D64QT5_API void DBaseQtShowWindow(void)')
        after = CPP[show:show + 500]
        self.assertIn("g_window->show();", after)
        self.assertIn("enforce_console_80x25_grid();", after)

    def test_existing_chrome_is_preserved(self):
        self.assertIn("g_zoom_in = make_zoom_button(true, g_header);", CPP)
        self.assertIn("g_zoom_out = make_zoom_button(false, g_header);", CPP)
        self.assertIn('addTab(QStringLiteral("Konsole"))', CPP)
        self.assertIn('addTab(QStringLiteral("DEBUG"))', CPP)
        self.assertIn('" border: 3px solid %1;"', CPP)
        self.assertIn('" border-width: 2px 0px 0px 0px;"', CPP)

    def test_ascii_submenus_are_preserved(self):
        self.assertIn("class AsciiPopupMenu final : public QMenu", CPP)
        self.assertIn("QMenu::paintEvent(event);", CPP)
        self.assertIn("QChar(0x2554)", CPP)
        self.assertIn("QChar(0x2550)", CPP)


if __name__ == "__main__":
    unittest.main()
