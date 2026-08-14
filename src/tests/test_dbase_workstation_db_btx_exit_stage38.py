from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
WORK = (ROOT / "d64qt5" / "d64_workstation.cpp").read_text(encoding="utf-8")
HDR = (ROOT / "d64qt5" / "d64_workstation.h").read_text(encoding="utf-8")


class WorkstationDbBtxExitStage38Tests(unittest.TestCase):
    def test_panel_has_database_icon_and_db_text(self):
        self.assertIn("PanelHotItem::Db", WORK)
        self.assertIn("WORKSTATION_DB_TOP", WORK)
        self.assertIn("draw_database_symbol", WORK)
        self.assertIn('L"DB"', WORK)
        self.assertIn("Ellipse(dc", WORK)
        self.assertIn("Rectangle(dc", WORK)

    def test_normal_main_window_close_only_hides(self):
        block = BRIDGE.split("class DBaseMainWindow final", 1)[1].split("QString choose_menu_font_family", 1)[0]
        self.assertIn("hide();", block)
        self.assertIn("event->ignore();", block)
        self.assertIn("g_exit_authorized", block)
        normal = block.split("if (g_exit_authorized", 1)[1]
        self.assertIn("request_runtime_shutdown();", normal)

    def test_db_icon_restores_hidden_main_window(self):
        self.assertIn("D64WorkstationSetDbCallback", HDR)
        self.assertIn("g_db_callback();", WORK)
        self.assertIn("D64WorkstationSetDbCallback(&workstation_db_requested);", BRIDGE)
        block = BRIDGE.split("void workstation_db_requested()", 1)[1].split("void show_runtime_warning", 1)[0]
        self.assertIn("g_window->show();", block)
        self.assertIn("g_window->raise();", block)
        self.assertIn("g_window->activateWindow();", block)

    def test_exit_requires_yes_no_confirmation(self):
        self.assertIn('QStringLiteral("JA")', BRIDGE)
        self.assertIn('QStringLiteral("NEIN")', BRIDGE)
        self.assertIn("confirm_runtime_exit()", BRIDGE)
        self.assertIn("g_exit_authorized = true;", BRIDGE)
        self.assertIn("D64WorkstationSetExitCallback(&workstation_exit_requested);", BRIDGE)
        self.assertNotIn("ExitProcess", WORK)
        self.assertNotIn("TerminateProcess", WORK)

    def test_btx_icon_launches_real_btx_exe(self):
        self.assertIn('QStringLiteral("BTX.exe")', BRIDGE)
        self.assertIn("D64WorkstationLaunchProgram", BRIDGE)
        self.assertIn("CreateProcessW(", WORK)
        self.assertIn("startup.lpDesktop", WORK)
        self.assertIn('std::wstring desktopSpec = L"WinSta0\\\\";', WORK)
        callback = BRIDGE.rsplit("void workstation_btx_requested()", 1)[1].split("void workstation_db_requested()", 1)[0]
        self.assertIn("launch_btx_executable();", callback)
        self.assertNotIn("show_btx_dialog();", callback)

    def test_btx_process_is_started_on_private_desktop(self):
        block = WORK.split("bool D64WorkstationLaunchProgram(", 1)[1].split("const wchar_t *D64WorkstationDesktopName", 1)[0]
        self.assertIn("desktopSpec += g_desktop_name;", block)
        self.assertIn("startup.lpDesktop", block)
        self.assertIn("CREATE_UNICODE_ENVIRONMENT", block)

    def test_external_workstation_children_get_graceful_close(self):
        self.assertIn("g_workstation_child_pids", WORK)
        self.assertIn("EnumDesktopWindows", WORK)
        self.assertIn("PostMessageW(hwnd, WM_CLOSE, 0, 0)", WORK)
        begin = WORK.split("void D64WorkstationBeginLeave()", 1)[1].split("void D64WorkstationFinalizeLeave()", 1)[0]
        self.assertIn("request_workstation_children_close();", begin)


if __name__ == "__main__":
    unittest.main()
