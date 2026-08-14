from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
WORK = (ROOT / "d64qt5" / "d64_workstation.cpp").read_text(encoding="utf-8")


class OwnerDialogVisibilityAltF4Stage41Tests(unittest.TestCase):
    def test_owner_close_hides_owned_top_level_windows_before_main(self):
        block = BRIDGE.split("class DBaseMainWindow final", 1)[1].split(
            "QString choose_menu_font_family", 1
        )[0]
        self.assertIn("hide_owner_application_windows();", block)
        self.assertIn("hide();", block)
        self.assertLess(
            block.index("hide_owner_application_windows();"),
            block.rindex("hide();"),
        )
        self.assertIn("event->ignore();", block)

    def test_owner_hide_marks_only_visible_top_levels_for_restore(self):
        block = BRIDGE.rsplit("void hide_owner_application_windows()", 1)[1].split(
            "void restore_owner_application_windows()", 1
        )[0]
        self.assertIn("QApplication::activeWindow()", block)
        self.assertIn("QApplication::topLevelWidgets()", block)
        self.assertIn("!widget->isVisible()", block)
        self.assertIn('widget->setProperty("dbaseHiddenWithMainWindow", true);', block)
        self.assertIn("widget->hide();", block)

    def test_db_restore_restores_only_windows_hidden_with_main(self):
        restore = BRIDGE.rsplit("void restore_owner_application_windows()", 1)[1].split(
            "void close_runtime_application_windows()", 1
        )[0]
        self.assertIn('widget->property("dbaseHiddenWithMainWindow").toBool()', restore)
        self.assertIn('widget->setProperty("dbaseHiddenWithMainWindow", false);', restore)
        self.assertIn("widget->show();", restore)
        self.assertIn("g_owner_hidden_active_window", restore)
        self.assertIn("active->raise();", restore)
        self.assertIn("active->activateWindow();", restore)

        callback = BRIDGE.split("void workstation_db_requested()", 1)[1].split(
            "void show_runtime_warning", 1
        )[0]
        self.assertIn("restore_owner_application_windows();", callback)
        self.assertLess(
            callback.index("g_window->show();"),
            callback.index("restore_owner_application_windows();"),
        )

    def test_alt_f4_is_redirected_to_root_owner_application_window(self):
        block = WORK.split("LRESULT CALLBACK workstation_keyboard_proc", 1)[1].split(
            "HMODULE module_from_hook_address", 1
        )[0]
        self.assertIn("if (alt && vk == VK_F4)", block)
        self.assertIn("GetForegroundWindow()", block)
        self.assertIn("GetAncestor(focusedWindow, GA_ROOTOWNER)", block)
        self.assertIn("PostMessageW(mainApplicationWindow, WM_CLOSE, 0, 0);", block)
        self.assertIn("mainApplicationWindow == g_exit_window", block)
        alt_block = block.split("if (alt && vk == VK_F4)", 1)[1]
        self.assertIn("return 1;", alt_block)

    def test_alt_f4_no_longer_falls_through_to_focused_login_dialog(self):
        block = WORK.split("LRESULT CALLBACK workstation_keyboard_proc", 1)[1].split(
            "HMODULE module_from_hook_address", 1
        )[0]
        alt_pos = block.index("if (alt && vk == VK_F4)")
        pass_through_pos = block.rindex("return CallNextHookEx")
        self.assertLess(alt_pos, pass_through_pos)
        alt_block = block[alt_pos:pass_through_pos]
        self.assertIn("return 1;", alt_block)


if __name__ == "__main__":
    unittest.main()
