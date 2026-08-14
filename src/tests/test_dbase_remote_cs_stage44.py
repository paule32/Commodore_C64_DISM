from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")


class RemoteCharacterStreamStage44Tests(unittest.TestCase):
    def test_server_uses_same_zoom_tabs_and_fixed_pitch_chrome(self):
        server = BRIDGE.split("class ServerDialog final", 1)[1].split(
            "void remote_server_close_dialog", 1
        )[0]
        self.assertIn("m_zoomIn = make_zoom_button(true", server)
        self.assertIn("m_zoomOut = make_zoom_button(false", server)
        self.assertIn("m_tabBar = new QTabBar", server)
        self.assertIn('m_tabBar->addTab(QStringLiteral("Verbindung"))', server)
        self.assertIn('QStringLiteral("SRV-PC %1 - %2")', server)
        self.assertIn("changeServerFontSize(+1)", server)
        self.assertIn("changeServerFontSize(-1)", server)
        self.assertIn("QFont fixedFont(choose_console_font_family(), m_fontPointSize)", server)
        self.assertIn("m_statusBar->setFixedHeight", server)

    def test_grid_dimensions_come_from_client_with_80x25_defaults(self):
        self.assertIn('root.insert(QStringLiteral("gridColumns"), DBASE_TEXT_COLUMNS);', BRIDGE)
        self.assertIn('root.insert(QStringLiteral("gridRows"), DBASE_TEXT_ROWS);', BRIDGE)
        preview = BRIDGE.split("class RemotePreviewWidget final", 1)[1].split(
            "class ServerDialog final", 1
        )[0]
        self.assertIn("D64_REMOTE_DEFAULT_COLUMNS", preview)
        self.assertIn("D64_REMOTE_DEFAULT_ROWS", preview)
        self.assertIn('value(QStringLiteral("gridColumns"))', preview)
        self.assertIn('value(QStringLiteral("gridRows"))', preview)

    def test_dialogs_are_character_streamed_and_passwords_masked(self):
        self.assertIn("QJsonArray remote_dialog_char_lines", BRIDGE)
        self.assertIn('QStringLiteral("charLines")', BRIDGE)
        self.assertIn('QStringLiteral("charColumns")', BRIDGE)
        self.assertIn('QStringLiteral("charRows")', BRIDGE)
        self.assertIn("QLineEdit::Password", BRIDGE)
        self.assertIn("QString(edit->text().size(), QLatin1Char('*'))", BRIDGE)

    def test_mouse_events_are_bidirectional_and_visible(self):
        self.assertIn("class RemoteClientEventFilter final", BRIDGE)
        self.assertIn("remote_queue_frame(peer, 'M', payload);", BRIDGE)
        self.assertIn("m_preview->setPeerMouse", BRIDGE)
        self.assertIn("m_serverMouse = command;", BRIDGE)
        self.assertIn("remote_show_cursor(globalPoint);", BRIDGE)
        self.assertIn("QApplication::sendEvent(target, &event);", BRIDGE)

    def test_tcp_application_header_contains_versions_ips_and_ids(self):
        header = BRIDGE.split("QJsonObject remote_build_tcp_header", 1)[1].split(
            "void remote_send_tcp_header", 1
        )[0]
        for field in (
            "D64CS_TCP_HEADER", "protocolVersion", "applicationVersion",
            "serverSoftware", "clientIp", "serverIp", "connectionId",
            "sessionId", "gridColumns", "gridRows",
        ):
            self.assertIn(field, header)
        self.assertIn("QUuid::createUuid()", BRIDGE)

    def test_session_id_is_created_and_broadcast(self):
        session_create = BRIDGE.split("DBaseQtSessionCreate", 1)[1].split(
            "DBaseQtGetLoginSession", 1
        )[0]
        self.assertIn("session->sessionId", session_create)
        self.assertIn("QUuid::createUuid()", session_create)
        self.assertIn("remote_broadcast_session_identity();", session_create)
        self.assertIn("remote_broadcast_session_identity()", BRIDGE)

    def test_crosslink_guards_use_connection_and_session_ids(self):
        guard = BRIDGE.split("bool remote_command_matches_client", 1)[1].split(
            "void remote_dispatch_mouse_command", 1
        )[0]
        self.assertIn('targetConnectionId', guard)
        self.assertIn('sourceConnectionId', guard)
        self.assertIn('targetSessionId', guard)
        server = BRIDGE.split("void sendToSelected", 1)[1].split(
            "void disconnectSelected", 1
        )[0]
        self.assertIn('sourceConnectionId', server)
        self.assertIn('targetConnectionId', server)
        self.assertIn('targetSessionId', server)

    def test_client_statusbar_children_scale_with_zoom(self):
        font_block = BRIDGE.split("void apply_output_font()", 1)[1].split(
            "void unlock_window_for_grid_resize", 1
        )[0]
        self.assertIn("statusChildren", font_block)
        self.assertIn("child->setFont(chromeFont);", font_block)
        self.assertIn("g_remote_listener_label->setFont(chromeFont);", font_block)
        self.assertIn("QFontMetrics(chromeFont, g_status_bar).height()", font_block)

    def test_dialog_fixed_font_prefers_consolas_then_courier_new(self):
        helper = BRIDGE.split("QString choose_popup_border_font_family()", 1)[1].split(
            "// Legacy regression marker only", 1
        )[0]
        self.assertIn('QStringLiteral("Consolas")', helper)
        self.assertIn('QStringLiteral("Courier New")', helper)
        self.assertNotIn('QStringLiteral("Terminal")', helper)


if __name__ == "__main__":
    unittest.main()
