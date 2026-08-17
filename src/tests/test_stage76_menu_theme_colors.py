from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage76MenuThemeColorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        start = SOURCE.index("def _green_beige_menu_stylesheet")
        end = SOURCE.index("def _apply_green_beige_chrome_style", start)
        cls.menu = SOURCE[start:end]
        tstart = SOURCE.index("def paintEvent", SOURCE.index("class GreenBeigeTitleBar"))
        tend = SOURCE.index("class ExplorerWindow(QMainWindow)", tstart)
        cls.title = SOURCE[tstart:tend]

    def test_dark_mode_is_navy_with_yellow_text(self):
        self.assertIn('surface = "#0B1F33"', self.menu)
        self.assertIn('text = "#FFD84D"', self.menu)
        self.assertIn('if self.dark_mode_enabled:', self.menu)

    def test_light_mode_returns_to_beige_with_black_text(self):
        self.assertIn('surface = "#F5F0E6"', self.menu)
        self.assertIn('text = "#000000"', self.menu)

    def test_menu_entries_use_arial_9pt(self):
        self.assertGreaterEqual(self.menu.count('font-family: "Arial";'), 2)
        self.assertGreaterEqual(self.menu.count('font-size: 9pt;'), 2)

    def test_selected_items_remain_green_and_stage77_uses_white_text(self):
        self.assertIn('QMenuBar#green_beige_menu_bar::item:selected', self.menu)
        self.assertIn('QMenu#green_beige_popup_menu::item:selected', self.menu)
        self.assertGreaterEqual(self.menu.count('background: #2E7D32;'), 3)
        self.assertGreaterEqual(self.menu.count('color: #FFFFFF;'), 2)

    def test_disabled_items_keep_theme_surface_and_gray_text(self):
        self.assertIn('QMenuBar#green_beige_menu_bar::item:disabled', self.menu)
        self.assertIn('QMenu#green_beige_popup_menu::item:disabled', self.menu)
        self.assertGreaterEqual(self.menu.count('background: {surface};'), 4)
        self.assertGreaterEqual(self.menu.count('color: {disabled};'), 2)
        self.assertIn('disabled = "#8B949E"', self.menu)
        self.assertIn('disabled = "#8A8A8A"', self.menu)

    def test_title_text_is_black(self):
        self.assertIn('painter.setPen(QColor("#000000"))', self.title)
        self.assertNotIn('painter.setPen(QColor("#FFFFFF"))', self.title)

    def test_top_chrome_surface_tracks_dark_light_mode(self):
        start = SOURCE.index("def _apply_green_beige_chrome_style")
        end = SOURCE.index("def _sync_green_beige_menu_objects", start)
        block = SOURCE[start:end]
        self.assertIn('"#0B1F33" if self.dark_mode_enabled else "#F5F0E6"', block)

    def test_global_theme_switch_reapplies_menu_chrome(self):
        start = SOURCE.index("def _apply_application_theme")
        end = SOURCE.index("def toggle_editor_theme", start)
        block = SOURCE[start:end]
        self.assertIn('self._apply_green_beige_chrome_style()', block)


if __name__ == "__main__":
    unittest.main()
