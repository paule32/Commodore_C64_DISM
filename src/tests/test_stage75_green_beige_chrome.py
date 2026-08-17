from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "d64_dism.py").read_text(encoding="utf-8")


class Stage75GreenBeigeChromeTests(unittest.TestCase):
    def test_reference_palette_constants_are_present(self):
        self.assertIn('GREEN_BEIGE_GREEN = "#2E7D32"', SOURCE)
        self.assertIn('GREEN_BEIGE_BEIGE = "#F5F0E6"', SOURCE)
        self.assertIn('GREEN_BEIGE_GOLD = "#D0A65F"', SOURCE)
        self.assertIn('QLinearGradient', SOURCE)

    def test_custom_titlebar_contains_minimize_maximize_close_controls(self):
        block = SOURCE[
            SOURCE.index("class GreenBeigeTitleBar"):
            SOURCE.index("class ExplorerWindow(QMainWindow)")
        ]
        self.assertIn('green_beige_minimize_button', block)
        self.assertIn('green_beige_maximize_button', block)
        self.assertIn('green_beige_close_button', block)
        self.assertIn('self.close_button.clicked.connect(window.close)', block)
        self.assertIn('self.maximize_button.clicked.connect(self.toggle_maximized)', block)

    def test_titlebar_paints_green_to_gold_gradient_and_black_title(self):
        block = SOURCE[
            SOURCE.index("def paintEvent", SOURCE.index("class GreenBeigeTitleBar")):
            SOURCE.index("class ExplorerWindow(QMainWindow)")
        ]
        self.assertIn('gradient.setColorAt(0.00, QColor("#2E7D32"))', block)
        self.assertIn('gradient.setColorAt(0.78, QColor("#D0A65F"))', block)
        self.assertIn('painter.setPen(QColor("#000000"))', block)
        self.assertIn('QPainterPath()', block)

    def test_windows_frame_is_frameless_but_resize_hit_test_is_preserved(self):
        self.assertIn('Qt.FramelessWindowHint', SOURCE)
        native = SOURCE[
            SOURCE.index("def nativeEvent", SOURCE.index("class ExplorerWindow")):
            SOURCE.index("def _focus_project_panel_on_startup")
        ]
        self.assertIn('WM_NCHITTEST', native)
        self.assertIn('HTTOPLEFT', native)
        self.assertIn('HTBOTTOMRIGHT', native)
        self.assertIn('FRAMELESS_RESIZE_BORDER', native)

    def test_custom_menu_row_replaces_qmainwindow_default_menu_calls(self):
        create = SOURCE[
            SOURCE.index("def _create_green_beige_window_chrome"):
            SOURCE.index("def _focus_project_panel_on_startup")
        ]
        self.assertIn('self.main_menu_bar = QMenuBar(self.main_top_chrome)', create)
        self.assertIn('self.setMenuWidget(self.main_top_chrome)', create)
        menu = SOURCE[
            SOURCE.index("def _create_menu(self)"):
            SOURCE.index("def _favorite_editor_name")
        ]
        self.assertIn('self.main_menu_bar.addMenu("&Datei")', menu)
        self.assertIn('self.main_menu_bar.addMenu("&Ansicht")', menu)
        self.assertIn('self.main_menu_bar.addMenu("&Hilfe")', menu)
        self.assertNotIn('self.menuBar().addMenu(', menu)

    def test_menu_bar_and_popup_menus_follow_reference_colors(self):
        block = SOURCE[
            SOURCE.index("def _green_beige_menu_stylesheet"):
            SOURCE.index("def _apply_green_beige_chrome_style")
        ]
        self.assertIn('surface = "#F5F0E6"', block)
        self.assertIn('background: #2E7D32;', block)
        self.assertIn('color: #FFFFFF;', block)
        self.assertIn('QMenu#green_beige_popup_menu::item:selected', block)
        self.assertIn('border-radius: 10px;', block)

    def test_dark_light_switch_reapplies_brand_chrome(self):
        block = SOURCE[
            SOURCE.index("def _apply_application_theme"):
            SOURCE.index("def toggle_editor_theme")
        ]
        self.assertIn('self._apply_green_beige_chrome_style()', block)

    def test_close_button_still_enters_existing_window_close_logic(self):
        # Titlebar calls window.close(); existing closeEvent must remain intact.
        self.assertIn('self.close_button.clicked.connect(window.close)', SOURCE)
        close = SOURCE[
            SOURCE.index("def closeEvent", SOURCE.index("class ExplorerWindow")):
        ]
        self.assertIn('self._confirm_project_replacement("Anwendung schließen")', close)
        self.assertIn('self._confirm_close_document(document)', close)


if __name__ == "__main__":
    unittest.main()
