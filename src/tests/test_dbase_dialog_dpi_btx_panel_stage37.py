from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
WORK = (ROOT / "d64qt5" / "d64_workstation.cpp").read_text(encoding="utf-8")
HDR = (ROOT / "d64qt5" / "d64_workstation.h").read_text(encoding="utf-8")


class DialogDpiAndBtxPanelStage37Tests(unittest.TestCase):
    def test_dialogs_share_real_console_dpi_font(self):
        self.assertIn("QFont current_console_grid_font()", BRIDGE)
        self.assertIn("QFontMetrics console_font_metrics", BRIDGE)
        self.assertIn("static_cast<const QPaintDevice *>(g_console->viewport())", BRIDGE)
        self.assertGreaterEqual(BRIDGE.count("m_borderFont = uiFont;"), 2)
        self.assertIn("const QFont uiFont = current_console_grid_font();", BRIDGE)

    def test_pixel_fine_tuning_is_removed(self):
        self.assertNotIn("g_font_pixel_adjust", BRIDGE)
        self.assertNotIn("fine_tune_console_font_for_grid", BRIDGE)
        self.assertNotIn("font.setPixelSize", BRIDGE)
        self.assertNotIn("const int adjustments[2] = { -1, +1 };", BRIDGE)

    def test_dialog_borders_are_drawn_on_character_cell_baselines(self):
        self.assertIn("int grid_text_baseline", BRIDGE)
        self.assertIn("grid_text_baseline(fm, ch, 0)", BRIDGE)
        self.assertIn("title.size() * cw", BRIDGE)
        self.assertNotIn("m_cellHeight + 2", BRIDGE)

    def test_btx_surface_is_exactly_80_by_25_cells(self):
        self.assertIn("constexpr int DBASE_BTX_COLUMNS = 80;", BRIDGE)
        self.assertIn("constexpr int DBASE_BTX_ROWS = 25;", BRIDGE)
        self.assertIn("DBASE_BTX_COLUMNS * m_cellWidth", BRIDGE)
        self.assertIn("DBASE_BTX_ROWS * m_cellHeight", BRIDGE)
        self.assertIn('setObjectName(QStringLiteral("dbaseBtxScreen"))', BRIDGE)

    def test_btx_dialog_follows_zoom_grid(self):
        self.assertIn("class BtxDialog final : public QDialog", BRIDGE)
        self.assertIn("if (g_btx_dialog)", BRIDGE)
        self.assertIn("g_btx_dialog->updateForGrid(true);", BRIDGE)
        self.assertIn("current_console_cell_size()", BRIDGE)

    def test_workstation_has_full_height_left_panel_with_btx_icon(self):
        self.assertIn("constexpr int WORKSTATION_PANEL_WIDTH = 76;", WORK)
        self.assertIn("GetSystemMetrics(SM_CYSCREEN)", WORK)
        self.assertIn("WORKSTATION_PANEL_WIDTH", WORK)
        self.assertIn('L"BTX"', WORK)
        self.assertIn("PanelHotItem::Btx", WORK)
        self.assertIn("WM_LBUTTONUP", WORK)

    def test_btx_panel_click_is_queued_into_qt(self):
        self.assertIn("using D64WorkstationBtxCallback = D64WorkstationCallback;", HDR)
        self.assertIn("D64WorkstationSetBtxCallback", HDR)
        self.assertIn("g_btx_callback();", WORK)
        self.assertIn("D64WorkstationSetBtxCallback(&workstation_btx_requested);", BRIDGE)
        self.assertIn("QTimer::singleShot(0", BRIDGE)
        self.assertIn("launch_btx_executable();", BRIDGE)

    def test_exit_is_deferred_to_confirmation_callback(self):
        block = WORK.split("case WM_LBUTTONUP:", 1)[1].split("case WM_LBUTTONDBLCLK:", 1)[0]
        self.assertIn("PanelHotItem::Exit", block)
        self.assertIn("g_exit_callback();", block)
        self.assertNotIn("ExitProcess", WORK)
        self.assertNotIn("TerminateProcess", WORK)


if __name__ == "__main__":
    unittest.main()
