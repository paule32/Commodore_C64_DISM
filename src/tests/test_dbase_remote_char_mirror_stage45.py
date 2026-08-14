from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")


class RemoteCharMirrorStage45Tests(unittest.TestCase):
    def test_protocol_is_char_cell_only_and_bumped(self):
        self.assertIn("constexpr int D64_REMOTE_PROTOCOL_VERSION = 3;", BRIDGE)
        header = BRIDGE.split("QJsonObject remote_build_tcp_header", 1)[1].split(
            "void remote_send_tcp_header", 1
        )[0]
        self.assertIn('QStringLiteral("streamMode"), QStringLiteral("chars")', header)
        self.assertIn('QStringLiteral("coordinateMode"), QStringLiteral("cells")', header)
        snapshot = BRIDGE.split("QJsonObject remote_build_snapshot()", 1)[1].split(
            "class RemoteCursorMarker final", 1
        )[0]
        self.assertIn('QStringLiteral("streamMode"), QStringLiteral("chars")', snapshot)
        for forbidden in ("mainWidth", "mainHeight", "gridRect", 'QStringLiteral("rect")'):
            self.assertNotIn(forbidden, snapshot)

    def test_full_client_menu_tree_is_transmitted_and_mirrored(self):
        self.assertIn("QJsonArray remote_menu_tree()", BRIDGE)
        self.assertIn("QJsonObject remote_menu_action_snapshot", BRIDGE)
        self.assertIn('QStringLiteral("children")', BRIDGE)
        self.assertIn('root.insert(QStringLiteral("menuTree"), remote_menu_tree());', BRIDGE)
        server = BRIDGE.split("class ServerDialog final", 1)[1].split(
            "void remote_server_close_dialog", 1
        )[0]
        self.assertIn("void syncMirroredMenu", server)
        self.assertIn("void populateMirroredMenu", server)
        self.assertIn("AsciiPopupMenu", server)
        self.assertIn('command.insert(QStringLiteral("type"), QStringLiteral("menu"));', server)
        self.assertIn("remote_dispatch_menu_command", BRIDGE)

    def test_client_status_fields_replace_server_status_when_selected(self):
        self.assertIn("QJsonArray remote_status_fields()", BRIDGE)
        self.assertIn('root.insert(QStringLiteral("statusFields"), remote_status_fields());', BRIDGE)
        server = BRIDGE.split("class ServerDialog final", 1)[1].split(
            "void remote_server_close_dialog", 1
        )[0]
        self.assertIn("void syncMirroredStatus", server)
        self.assertIn("m_status->hide();", server)
        self.assertIn("m_mirroredStatusLabels", server)
        self.assertIn("Verbindungsdaten liegen nur noch im", server)

    def test_dialog_frames_are_actual_stream_chars(self):
        helper = BRIDGE.split("void remote_draw_char_frame", 1)[1].split(
            "QJsonArray remote_dialog_char_lines", 1
        )[0]
        for codepoint in ("0x2554", "0x2557", "0x255A", "0x255D", "0x2550", "0x2551"):
            self.assertIn(codepoint, helper)
        preview = BRIDGE.split("class RemotePreviewWidget final", 1)[1].split(
            "class ServerDialog final", 1
        )[0]
        self.assertIn('window.value(QStringLiteral("charLines"))', preview)
        self.assertNotIn("painter.drawRect(wr", preview)
        self.assertNotIn("titleRect", preview)

    def test_dialog_and_popup_positions_are_character_cells(self):
        snapshot = BRIDGE.split("QJsonObject remote_build_snapshot()", 1)[1].split(
            "class RemoteCursorMarker final", 1
        )[0]
        self.assertIn('QStringLiteral("charColumn")', snapshot)
        self.assertIn('QStringLiteral("charRow")', snapshot)
        self.assertIn('QStringLiteral("charColumns")', snapshot)
        self.assertIn('QStringLiteral("charRows")', snapshot)
        self.assertIn("remote_popup_char_lines", snapshot)

    def test_mouse_transport_uses_cells_not_pixels(self):
        local = BRIDGE.split("void remote_queue_local_mouse", 1)[1].split(
            "class RemoteClientEventFilter", 1
        )[0]
        dispatch = BRIDGE.split("void remote_dispatch_mouse_command", 1)[1].split(
            "void remote_process_client_command", 1
        )[0]
        for field in ("column", "row", "subX", "subY"):
            self.assertIn(f'QStringLiteral("{field}")', local)
            self.assertIn(f'QStringLiteral("{field}")', dispatch)
        self.assertNotIn('QStringLiteral("x")', local)
        self.assertNotIn('QStringLiteral("y")', local)
        self.assertNotIn('QStringLiteral("x")', dispatch)
        self.assertNotIn('QStringLiteral("y")', dispatch)


if __name__ == "__main__":
    unittest.main()
