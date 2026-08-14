from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")


class TerminalRpcStage47Tests(unittest.TestCase):
    def test_protocol_version_five_and_terminal_header(self):
        self.assertIn("constexpr int D64_REMOTE_PROTOCOL_VERSION = 5;", BRIDGE)
        self.assertIn("constexpr int D64_TERMINAL_RPC_VERSION = 1;", BRIDGE)
        header = BRIDGE.split("QJsonObject remote_build_tcp_header", 1)[1].split(
            "void remote_send_tcp_header", 1
        )[0]
        self.assertIn('QStringLiteral("terminalProtocol"), QStringLiteral("D64TERM/1")', header)
        self.assertIn('QStringLiteral("terminalRpcVersion"), D64_TERMINAL_RPC_VERSION', header)
        accept = BRIDGE.split("bool remote_accept_tcp_header", 1)[1].split(
            "QSize remote_console_cell_size", 1
        )[0]
        self.assertIn('QStringLiteral("D64TERM/1")', accept)
        self.assertIn("D64_TERMINAL_RPC_VERSION", accept)

    def test_terminal_type_numbers_are_stable(self):
        required = {
            "TerminalTApplication": 2000,
            "TerminalTBackground": 2001,
            "TerminalTMainMenu": 2002,
            "TerminalTStatusBar": 2003,
            "TerminalTFrame": 2010,
            "TerminalTView": 2011,
            "TerminalTButton": 2040,
            "TerminalTLineEdit": 2045,
            "TerminalTCheckBox": 2046,
            "TerminalTComboBox": 2047,
            "TerminalTLabel": 2048,
            "TerminalTMenuItem": 2050,
        }
        enum = BRIDGE.split("enum TerminalTypeCode", 1)[1].split("};", 1)[0]
        for name, value in required.items():
            self.assertIn(f"{name}", enum)
            self.assertIn(str(value), enum)

    def test_compact_dsl_uses_cells_and_hex_rgb(self):
        record = BRIDGE.split("QString terminal_record_line", 1)[1].split(
            "TerminalComponentRecord terminal_make_record", 1
        )[0]
        self.assertIn('QStringLiteral("T%1_%2_%3_%4_%5_%6_%7_%8_%9_%10")', record)
        self.assertIn("terminal_color_hex(record.foreground)", record)
        self.assertIn("terminal_color_hex(record.background)", record)
        self.assertNotIn("pixel", record.lower())
        self.assertNotIn("QRect", record)

    def test_application_template_has_turbo_vision_build_order(self):
        build = BRIDGE.split("QByteArray terminal_build_application_template()", 1)[1].split(
            "void terminal_broadcast_property", 1
        )[0]
        positions = [
            build.index("TerminalTApplication"),
            build.index("TerminalTBackground"),
            build.index("TerminalTMainMenu"),
            build.index("TerminalTStatusBar"),
            build.index("TerminalTFrame"),
            build.index("TerminalTView"),
        ]
        self.assertEqual(positions, sorted(positions))

    def test_background_template_uses_screen_clear_char_and_colors(self):
        build = BRIDGE.split("QByteArray terminal_build_application_template()", 1)[1].split(
            "void terminal_broadcast_property", 1
        )[0]
        self.assertIn("g_console_clear_char_code", build)
        self.assertIn("g_console_clear_char_foreground", build)
        self.assertIn("g_console_clear_char_background", build)
        self.assertIn('QStringLiteral("CHAR=%1")', build)
        self.assertIn("DBASE_TEXT_COLUMNS", build)
        self.assertIn("DBASE_TEXT_ROWS", build)

    def test_clear_and_color_changes_dirty_terminal_template(self):
        set_color = BRIDGE.split('extern "C" D64QT5_API int DBaseQtSetOutputColor', 1)[1].split(
            'extern "C" D64QT5_API void DBaseQtClearScreen', 1
        )[0]
        self.assertIn("g_terminal_template_dirty = true;", set_color)
        normal = BRIDGE.split('extern "C" D64QT5_API int DBaseQtSetColorNormal', 1)[1].split(
            'extern "C" D64QT5_API int DBaseQtSetOutputColor', 1
        )[0]
        self.assertIn("g_terminal_template_dirty = true;", normal)
        clear_char = BRIDGE.split('extern "C" D64QT5_API int DBaseQtClearScreenChar', 1)[1].split(
            'extern "C" D64QT5_API int DBaseQtClearScreenColor', 1
        )[0]
        self.assertIn("g_terminal_template_dirty = true;", clear_char)
        append = BRIDGE.split("void append_text", 1)[1].split("int debug_tab_index", 1)[0]
        self.assertIn("g_console_clear_mode = ConsoleClearMode::None;", append)
        self.assertIn("g_terminal_template_dirty = true;", append)

    def test_template_contains_frame_view_and_semantic_controls(self):
        build = BRIDGE.split("QByteArray terminal_build_application_template()", 1)[1].split(
            "void terminal_broadcast_property", 1
        )[0]
        self.assertIn("terminal_component_id(widget)", build)
        self.assertIn("terminal_type_for_widget(child)", build)
        self.assertIn("TerminalTLineEdit", BRIDGE)
        self.assertIn("TerminalTButton", BRIDGE)
        self.assertIn("TerminalTCheckBox", BRIDGE)
        self.assertIn("TerminalTComboBox", BRIDGE)
        self.assertIn("TerminalTLabel", BRIDGE)

    def test_line_edit_2045_sends_runtime_text_as_property_rpc(self):
        ids = BRIDGE.split("quint32 terminal_component_id(QObject *object)\n{", 1)[1].split(
            "QObject *terminal_object_by_id", 1
        )[0]
        self.assertIn("QLineEdit::textChanged", ids)
        self.assertIn('QStringLiteral("TEXT")', ids)
        self.assertIn("QLineEdit::Password", ids)
        rpc = BRIDGE.split("void terminal_broadcast_property(QObject *object, const QString &name, const QString &value)\n{", 1)[1].split(
            "bool terminal_parse_record_line", 1
        )[0]
        self.assertIn('QStringLiteral("P_%1_%2_%3_%4_%5")', rpc)
        self.assertIn("remote_queue_frame(peer, 'R', payload)", rpc)

    def test_template_is_queued_before_snapshot_and_before_property(self):
        poll = BRIDGE.split("void remote_client_poll()", 1)[1].split(
            "void remote_client_shutdown", 1
        )[0]
        self.assertLess(poll.index("remote_queue_frame(peer, 'T'"), poll.index("remote_queue_frame(peer, 'S'"))
        rpc = BRIDGE.split("void terminal_broadcast_property(QObject *object, const QString &name, const QString &value)\n{", 1)[1].split(
            "bool terminal_parse_record_line", 1
        )[0]
        self.assertLess(rpc.index("remote_queue_frame(peer, 'T'"), rpc.index("remote_queue_frame(peer, 'R'"))

    def test_server_consumes_template_and_rpc_before_json_snapshot(self):
        poll = BRIDGE.split("void poll()", 1)[1].split("void connectClient()", 1)[0]
        tpos = poll.index("if (type == 'T')")
        rpos = poll.index("if (type == 'R')")
        jsonpos = poll.index("QJsonParseError error")
        self.assertLess(tpos, jsonpos)
        self.assertLess(rpos, jsonpos)
        self.assertIn("m_preview->setTerminalProgram(payload)", poll)
        self.assertIn("m_preview->applyTerminalRpc(payload)", poll)

    def test_server_can_edit_line_edit_by_component_id(self):
        preview = BRIDGE.split("class RemotePreviewWidget final", 1)[1].split(
            "class ServerDialog final", 1
        )[0]
        self.assertIn('QStringLiteral("terminalKey")', preview)
        self.assertIn('QStringLiteral("componentId")', preview)
        dispatch = BRIDGE.split("void remote_dispatch_terminal_key", 1)[1].split(
            "void remote_process_client_command", 1
        )[0]
        self.assertIn("terminal_object_by_id", dispatch)
        self.assertIn("qobject_cast<QLineEdit *>", dispatch)
        self.assertIn("QApplication::sendEvent", dispatch)

    def test_frame_moving_state_is_visible_remote(self):
        self.assertEqual(BRIDGE.count('setProperty("dbaseRemoteMoving", true)'), 3)
        self.assertEqual(BRIDGE.count('setProperty("dbaseRemoteMoving", false)'), 3)
        snapshot = BRIDGE.split("QJsonObject remote_build_snapshot()", 1)[1].split(
            "class RemoteCursorMarker final", 1
        )[0]
        self.assertIn('property("dbaseRemoteMoving")', snapshot)

    def test_checkbox_and_combo_runtime_state_are_semantic(self):
        ids = BRIDGE.split("quint32 terminal_component_id(QObject *object)\n{", 1)[1].split(
            "QObject *terminal_object_by_id", 1
        )[0]
        self.assertIn("QComboBox::currentTextChanged", ids)
        self.assertIn("QCheckBox::toggled", ids)
        self.assertIn('QStringLiteral("CHECKED")', ids)
        controls = BRIDGE.split("QJsonArray remote_dialog_controls", 1)[1].split(
            "QJsonArray remote_popup_char_lines", 1
        )[0]
        self.assertIn('QStringLiteral("checkbox")', controls)
        self.assertIn('QStringLiteral("checked")', controls)

    def test_terminal_protocol_never_uses_global_sendinput(self):
        self.assertNotIn("SendInput(", BRIDGE)
        self.assertNotIn("mouse_event(", BRIDGE)


if __name__ == "__main__":
    unittest.main()
