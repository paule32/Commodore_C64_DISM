from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage77MenuSelectionResizeBorderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        start = SOURCE.index("def _green_beige_menu_stylesheet")
        end = SOURCE.index("def _apply_green_beige_chrome_style", start)
        cls.menu = SOURCE[start:end]
        cls.window = SOURCE[SOURCE.index("class ExplorerWindow(QMainWindow)"):]

    def test_selected_menu_text_is_white_on_green(self):
        self.assertIn("QMenuBar#green_beige_menu_bar::item:selected", self.menu)
        self.assertIn("QMenu#green_beige_popup_menu::item:selected", self.menu)
        self.assertGreaterEqual(self.menu.count("background: #2E7D32;"), 3)
        self.assertGreaterEqual(self.menu.count("color: #FFFFFF;"), 2)

    def test_visible_resize_border_is_exactly_two_pixels_and_beige(self):
        self.assertIn('FRAMELESS_VISIBLE_BORDER = 2', self.window)
        self.assertIn('FRAMELESS_BORDER_COLOR = "#F5F0E6"', self.window)

    def test_resize_hit_zone_remains_larger_than_visible_border(self):
        visible = int(re.search(r"FRAMELESS_VISIBLE_BORDER\s*=\s*(\d+)", self.window).group(1))
        hit = int(re.search(r"FRAMELESS_RESIZE_BORDER\s*=\s*(\d+)", self.window).group(1))
        self.assertEqual(visible, 2)
        self.assertGreaterEqual(hit, visible)
        self.assertEqual(hit, 7)

    def test_window_reserves_two_pixel_contents_margin_on_windows(self):
        init = self.window[self.window.index("def __init__"):self.window.index("def _create_green_beige_window_chrome")]
        self.assertIn('if sys.platform == "win32":', init)
        self.assertIn('border = int(self.FRAMELESS_VISIBLE_BORDER)', init)
        self.assertIn('self.setContentsMargins(border, border, border, border)', init)

    def test_explorer_paints_visible_border_with_configured_color(self):
        start = self.window.index("def paintEvent(self, event) -> None:", self.window.index("def _sync_green_beige_menu_objects"))
        end = self.window.index("def nativeEvent", start)
        block = self.window[start:end]
        self.assertIn("QPainter(self)", block)
        self.assertIn("QPen(QColor(self.FRAMELESS_BORDER_COLOR), border)", block)
        # Stage 78 rounds only the two top corners; the visible 2 px border
        # and native resize behavior from Stage 77 remain unchanged.
        self.assertIn("QPainterPath()", block)
        self.assertIn("frame_path.quadTo(left, top, left + radius, top)", block)
        self.assertIn("frame_path.quadTo(right, top, right, top + radius)", block)
        self.assertIn("Qt.RoundJoin", block)

    def test_native_resize_edges_and_corners_are_unchanged(self):
        start = self.window.index("def nativeEvent")
        end = self.window.index("def _focus_project_panel_on_startup", start)
        block = self.window[start:end]
        for token in ("HTTOPLEFT", "HTTOPRIGHT", "HTBOTTOMLEFT", "HTBOTTOMRIGHT", "HTLEFT", "HTRIGHT", "HTTOP", "HTBOTTOM"):
            self.assertIn(token, block)
        self.assertIn("FRAMELESS_RESIZE_BORDER", block)


if __name__ == "__main__":
    unittest.main()
