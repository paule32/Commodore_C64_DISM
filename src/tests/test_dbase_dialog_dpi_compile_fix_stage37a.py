from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")


class DialogDpiCompileFixStage37ATests(unittest.TestCase):
    def test_grid_baseline_is_declared_before_ascii_popup_menu(self):
        decl = "int grid_text_baseline(const QFontMetrics &fm, int cellHeight, int row);"
        self.assertIn(decl, BRIDGE)
        self.assertLess(BRIDGE.index(decl), BRIDGE.index("class AsciiPopupMenu final : public QMenu"))

    def test_ascii_popup_defines_cell_height_and_top_baseline(self):
        block = BRIDGE.split("class AsciiPopupMenu final : public QMenu", 1)[1]
        block = block.split("void connect_quit_action", 1)[0]
        self.assertIn("const int ch = qMax(1, m_cellHeight);", block)
        self.assertIn("const int topBaseline = grid_text_baseline(fm, ch, 0);", block)
        self.assertIn("grid_text_baseline(fm, ch, y / ch)", block)
        self.assertNotIn("const int ascent = fm.ascent();", block)

    def test_login_uses_grid_baseline_consistently(self):
        block = BRIDGE.split("class LoginDialog final : public QDialog", 1)[1]
        block = block.split("class WarningDialog final : public QDialog", 1)[0]
        self.assertIn("const int topBaseline = grid_text_baseline(fm, ch, 0);", block)
        self.assertIn("painter.drawText(0, topBaseline, TL);", block)
        self.assertIn("grid_text_baseline(fm, ch, y / ch)", block)
        self.assertNotIn("painter.drawText(0, ascent, TL);", block)
        self.assertNotIn("const int baseline = y + ascent;", block)


if __name__ == "__main__":
    unittest.main()
