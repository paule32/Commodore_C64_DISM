from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CPP = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")


class DBaseAsciiSubmenuStage18Tests(unittest.TestCase):
    def test_popup_menu_subclass_is_productive(self):
        self.assertIn("class AsciiPopupMenu final : public QMenu", CPP)
        self.assertIn("QMenu::paintEvent(event);", CPP)
        self.assertIn("QChar(0x2554)", CPP)  # C9 -> ╔
        self.assertIn("QChar(0x2557)", CPP)  # BB -> ╗
        self.assertIn("QChar(0x255A)", CPP)  # C8 -> ╚
        self.assertIn("QChar(0x255D)", CPP)  # BC -> ╝
        self.assertIn("QChar(0x2550)", CPP)  # CD -> ═
        self.assertIn("QChar(0x2551)", CPP)  # BA -> ║

    def test_main_menu_bar_remains_normal_qmenubar(self):
        self.assertIn("g_menu_bar = new QMenuBar(g_console_frame);", CPP)
        self.assertNotIn("class AsciiMenuBar", CPP)
        self.assertIn('"QMenuBar {"', CPP)

    def test_every_dbase_popup_uses_ascii_popup_menu(self):
        self.assertIn("AsciiPopupMenu *menu = new AsciiPopupMenu(node->text, menuParent);", CPP)
        self.assertIn("AsciiPopupMenu *popup = new AsciiPopupMenu(QString(), g_menu_bar);", CPP)
        self.assertNotIn("new QMenu(g_menu_bar)", CPP)

    def test_terminal_font_with_courier_new_fallback(self):
        self.assertIn('QStringLiteral("Terminal")', CPP)
        self.assertIn('QStringLiteral("Courier New")', CPP)
        self.assertIn("choose_popup_border_font_family()", CPP)

    def test_two_zoom_buttons_and_tab_bar_are_preserved(self):
        self.assertIn("g_zoom_in = make_zoom_button(true, g_header);", CPP)
        self.assertIn("g_zoom_out = make_zoom_button(false, g_header);", CPP)
        self.assertIn('addTab(QStringLiteral("Konsole"))', CPP)
        self.assertIn('addTab(QStringLiteral("DEBUG"))', CPP)
        self.assertIn("remove_debug_tab();", CPP)
        self.assertIn("install_debug_tab(true);", CPP)

    def test_outer_frame_stays_three_pixels(self):
        self.assertIn('" border: 3px solid %1;"', CPP)

    def test_status_separator_is_two_pixels(self):
        self.assertIn('" border-width: 2px 0px 0px 0px;"', CPP)
        self.assertIn('" border-color: %1;"', CPP)

    def test_zero_editor_padding_is_preserved(self):
        self.assertIn("g_console->setContentsMargins(0, 0, 0, 0);", CPP)
        self.assertIn("g_console->document()->setDocumentMargin(0.0);", CPP)
        self.assertIn('"  margin: 0px;"', CPP)
        self.assertIn('"  padding: 0px;"', CPP)
        self.assertNotIn("setViewportMargins(", CPP)


if __name__ == "__main__":
    unittest.main()
