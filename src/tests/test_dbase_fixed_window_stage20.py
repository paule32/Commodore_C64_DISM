from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CPP = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")


class DBaseFixedWindowStage20Tests(unittest.TestCase):
    def test_main_window_is_locked_after_grid_measurement(self):
        self.assertIn("void lock_window_to_current_grid_size()", CPP)
        self.assertIn("g_window->setFixedSize(g_window->size());", CPP)

    def test_internal_grid_resize_can_temporarily_unlock_window(self):
        self.assertIn("void unlock_window_for_grid_resize()", CPP)
        self.assertIn("g_window->setMinimumSize(420, 260);", CPP)
        self.assertIn(
            "g_window->setMaximumSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX);",
            CPP,
        )

    def test_grid_enforcement_unlocks_then_relocks(self):
        start = CPP.index("void enforce_console_80x25_grid()")
        end = CPP.index("void change_font_size", start)
        body = CPP[start:end]
        self.assertIn("unlock_window_for_grid_resize();", body)
        self.assertIn("resize_window_to_console_grid();", body)
        self.assertIn("lock_window_to_current_grid_size();", body)
        self.assertLess(
            body.index("unlock_window_for_grid_resize();"),
            body.index("lock_window_to_current_grid_size();"),
        )

    def test_zoom_still_changes_exactly_one_point(self):
        self.assertIn("change_font_size(+1);", CPP)
        self.assertIn("change_font_size(-1);", CPP)
        self.assertIn("g_font_point_size = next;", CPP)
        self.assertIn("enforce_console_80x25_grid();", CPP)

    def test_stage19_grid_and_chrome_are_preserved(self):
        self.assertIn("constexpr int DBASE_TEXT_COLUMNS = 80;", CPP)
        self.assertIn("constexpr int DBASE_TEXT_ROWS = 25;", CPP)
        self.assertIn("class AsciiPopupMenu final : public QMenu", CPP)
        self.assertIn('addTab(QStringLiteral("Konsole"))', CPP)
        self.assertIn('addTab(QStringLiteral("DEBUG"))', CPP)
        self.assertIn('" border: 3px solid %1;"', CPP)
        self.assertIn('" border-width: 2px 0px 0px 0px;"', CPP)


if __name__ == "__main__":
    unittest.main()
