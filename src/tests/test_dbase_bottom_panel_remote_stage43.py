from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORK = (ROOT / "d64qt5" / "d64_workstation.cpp").read_text(encoding="utf-8")
HDR = (ROOT / "d64qt5" / "d64_workstation.h").read_text(encoding="utf-8")
BRIDGE = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
PRO = (ROOT / "d64qt5" / "d64qt5_bridge.pro").read_text(encoding="utf-8")


class BottomPanelRemoteStage43Tests(unittest.TestCase):
    def test_bottom_panel_spans_screen_and_matches_icon_height(self):
        self.assertIn("constexpr int WORKSTATION_ICON_SIZE = 52;", WORK)
        self.assertIn("constexpr int WORKSTATION_BOTTOM_PANEL_HEIGHT = WORKSTATION_ICON_SIZE;", WORK)
        block = WORK.split("bool create_bottom_panel_window()", 1)[1].split("void destroy_bottom_panel_window", 1)[0]
        self.assertIn("GetSystemMetrics(SM_CXSCREEN)", block)
        self.assertIn("height - WORKSTATION_BOTTOM_PANEL_HEIGHT", block)
        self.assertIn("WS_EX_TOPMOST", block)

    def test_left_panel_stops_above_bottom_panel(self):
        block = WORK.split("bool create_exit_window()", 1)[1].split("void destroy_exit_window", 1)[0]
        self.assertIn("screenHeight - WORKSTATION_BOTTOM_PANEL_HEIGHT", block)

    def test_minimized_main_window_uses_four_pixel_panel_gaps(self):
        self.assertIn("constexpr int WORKSTATION_PANEL_GAP = 4;", WORK)
        block = WORK.split("void D64WorkstationPositionMinimizedWindow", 1)[1].split("bool D64WorkstationLaunchProgram", 1)[0]
        self.assertIn("WPF_SETMINPOSITION", block)
        self.assertIn("WORKSTATION_PANEL_WIDTH + WORKSTATION_PANEL_GAP", block)
        self.assertIn("WORKSTATION_BOTTOM_PANEL_HEIGHT", block)
        self.assertIn("SM_CYMINIMIZED", block)
        main = BRIDGE.split("class DBaseMainWindow final", 1)[1].split("QString choose_menu_font_family", 1)[0]
        self.assertIn("WM_MOVING", main)
        self.assertIn("D64WorkstationConstrainMovingRect", main)
        self.assertIn("D64WorkstationPositionMinimizedWindow", main)
        activate = WORK.split("bool D64WorkstationActivate(HWND mainWindow)", 1)[1].split("bool D64WorkstationInstallKeyboardGuard", 1)[0]
        self.assertIn("D64WorkstationConstrainMovingRect(&constrainedRect);", activate)

    def test_server_and_srv_pc_icons_are_in_bottom_panel(self):
        self.assertIn('L"SERVER"', WORK)
        self.assertIn('L"SRV-PC %d"', WORK)
        self.assertIn("D64WorkstationSetServerClientCount", HDR)
        self.assertIn("g_server_client_callback(item);", WORK)

    def test_clients_listen_over_ipv4_and_winsock_is_linked(self):
        self.assertIn("socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)", BRIDGE)
        self.assertIn("listen(listener, SOMAXCONN)", BRIDGE)
        self.assertIn("inet_pton(AF_INET", BRIDGE)
        self.assertIn('QStringLiteral("127.0.0.1")', BRIDGE)
        self.assertIn("-lws2_32", PRO)

    def test_remote_stream_is_character_state_not_pixels(self):
        self.assertIn("QStringList remote_grid_lines()", BRIDGE)
        self.assertIn("DBASE_TEXT_COLUMNS", BRIDGE)
        self.assertIn("DBASE_TEXT_ROWS", BRIDGE)
        self.assertIn('root.insert(QStringLiteral("grid"), grid);', BRIDGE)
        self.assertIn('root.insert(QStringLiteral("menuTree"), remote_menu_tree());', BRIDGE)
        self.assertIn('root.insert(QStringLiteral("windows"), windows);', BRIDGE)
        remote = BRIDGE.split("Stage 43: zeichenorientierte IPv4", 1)[1].split("#endif // _WIN32", 1)[0]
        self.assertNotIn("BitBlt", remote)
        self.assertNotIn("PrintWindow", remote)
        self.assertNotIn("QScreen::grabWindow", remote)

    def test_dialog_movement_is_part_of_periodic_snapshot(self):
        self.assertIn("QApplication::topLevelWidgets()", BRIDGE)
        self.assertIn('info.insert(QStringLiteral("charColumn")', BRIDGE)
        self.assertIn('info.insert(QStringLiteral("charRow")', BRIDGE)
        self.assertIn("g_remote_client_timer->setInterval(50);", BRIDGE)

    def test_server_close_disconnects_but_client_listener_remains_separate(self):
        server = BRIDGE.split("class ServerDialog final", 1)[1].split("void workstation_server_requested", 1)[0]
        self.assertIn("disconnectAll();", server)
        self.assertIn("D64WorkstationSetServerClientCount(0);", server)
        client = BRIDGE.split("void remote_client_poll()", 1)[1].split("class RemotePreviewWidget", 1)[0]
        self.assertIn("if (!g_remote_client_peers.isEmpty())", client)
        self.assertIn("g_remote_listener", client)

    def test_remote_mouse_is_scoped_to_qt_widgets_and_visible_on_client(self):
        self.assertIn("QApplication::widgetAt(globalPoint)", BRIDGE)
        self.assertIn("QApplication::sendEvent(target, &event);", BRIDGE)
        self.assertIn("class RemoteCursorMarker final", BRIDGE)
        self.assertIn("remote_show_cursor(globalPoint);", BRIDGE)
        remote = BRIDGE.split("void remote_dispatch_mouse_command", 1)[1].split("void remote_process_client_command", 1)[0]
        self.assertNotIn("SendInput", remote)
        self.assertNotIn("mouse_event", remote)

    def test_server_connections_drive_srv_pc_panel_count(self):
        self.assertIn("D64WorkstationSetServerClientCount(connected.size());", BRIDGE)
        self.assertIn("void workstation_server_client_requested(int clientIndex)", BRIDGE)
        self.assertIn("g_server_dialog->selectClient(clientIndex);", BRIDGE)

    def test_server_window_is_not_treated_as_alt_f4_main_application(self):
        self.assertIn('L"D64Workstation.ToolWindow"', WORK)
        alt = WORK.split("if (alt && vk == VK_F4)", 1)[1].split("return CallNextHookEx", 1)[0]
        self.assertIn("GetPropW(mainApplicationWindow, WORKSTATION_TOOL_WINDOW_PROPERTY)", alt)
        self.assertIn('L"D64Workstation.ToolWindow"', BRIDGE)


if __name__ == "__main__":
    unittest.main()
