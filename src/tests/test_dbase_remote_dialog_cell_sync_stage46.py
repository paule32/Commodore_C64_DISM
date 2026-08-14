from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")


class RemoteDialogCellSyncStage46Tests(unittest.TestCase):
    def test_protocol_is_version_four_and_stays_char_cell_only(self):
        self.assertIn("constexpr int D64_REMOTE_PROTOCOL_VERSION = 4;", BRIDGE)
        header = BRIDGE.split("QJsonObject remote_build_tcp_header", 1)[1].split(
            "void remote_send_tcp_header", 1
        )[0]
        self.assertIn('QStringLiteral("streamMode"), QStringLiteral("chars")', header)
        self.assertIn('QStringLiteral("coordinateMode"), QStringLiteral("cells")', header)

    def test_dialog_controls_are_transmitted_as_semantic_cells(self):
        helper = BRIDGE.split("QJsonArray remote_dialog_controls", 1)[1].split(
            "QJsonArray remote_popup_char_lines", 1
        )[0]
        for field in ("role", "text", "column", "row", "columns", "rows", "focused"):
            self.assertIn(f'QStringLiteral("{field}")', helper)
        self.assertIn('QStringLiteral("input")', helper)
        self.assertIn('QStringLiteral("button")', helper)
        self.assertIn("QLineEdit::Password", helper)
        snapshot = BRIDGE.split("QJsonObject remote_build_snapshot()", 1)[1].split(
            "class RemoteCursorMarker final", 1
        )[0]
        self.assertIn('QStringLiteral("controls")', snapshot)
        self.assertIn('QStringLiteral("dialogStyle")', snapshot)

    def test_server_uses_client_dialog_colors_and_controls(self):
        preview = BRIDGE.split("class RemotePreviewWidget final", 1)[1].split(
            "class ServerDialog final", 1
        )[0]
        self.assertIn("QColor(144, 144, 144)", preview)
        self.assertIn("QColor(0, 128, 0)", preview)
        self.assertIn("QColor(255, 255, 255)", preview)
        self.assertIn("QColor(255, 255, 0)", preview)
        self.assertIn('role == QStringLiteral("input")', preview)
        self.assertIn('role == QStringLiteral("button")', preview)
        self.assertIn('window.value(QStringLiteral("charLines"))', preview)

    def test_server_outer_frame_follows_client_border_color(self):
        snapshot = BRIDGE.split("QJsonObject remote_build_snapshot()", 1)[1].split(
            "class RemoteCursorMarker final", 1
        )[0]
        self.assertIn('QStringLiteral("consoleBorderColor")', snapshot)
        server = BRIDGE.split("void applyServerStyleAndFont()", 1)[1].split(
            "void changeServerFontSize", 1
        )[0]
        self.assertIn('snapshot.value(QStringLiteral("consoleBorderColor"))', server)
        self.assertIn("border:3px solid %1", server)

    def test_mouse_moves_are_coalesced_but_press_release_are_ordered(self):
        helper = BRIDGE.split("void remote_queue_mouse_payload", 1)[1].split(
            "void remote_flush_pending_mouse", 1
        )[0]
        self.assertIn("coalesceMove", helper)
        self.assertIn("state->pendingMousePayload = payload;", helper)
        local = BRIDGE.split("void remote_queue_local_mouse", 1)[1].split(
            "class RemoteClientEventFilter", 1
        )[0]
        self.assertIn('action == QStringLiteral("move")', local)
        self.assertIn("remote_queue_mouse_payload(peer, 'M', payload, coalesceMove)", local)
        server = BRIDGE.split("void sendToSelected", 1)[1].split(
            "void disconnectSelected", 1
        )[0]
        self.assertIn("remote_queue_mouse_payload(m_selected, 'C', payload, mouseMove)", server)

    def test_fast_remote_drag_uses_stable_widget_capture(self):
        dispatch = BRIDGE.split("void remote_dispatch_mouse_command", 1)[1].split(
            "void remote_process_client_command", 1
        )[0]
        self.assertIn("g_remote_mouse_capture_widget = target;", dispatch)
        self.assertIn("g_remote_mouse_capture_widget.data()", dispatch)
        self.assertIn("g_remote_mouse_capture_widget.clear();", dispatch)

    def test_mouse_positions_have_monotonic_sequences_and_cell_coordinates(self):
        local = BRIDGE.split("void remote_queue_local_mouse", 1)[1].split(
            "class RemoteClientEventFilter", 1
        )[0]
        for field in ("sequence", "column", "row", "subX", "subY"):
            self.assertIn(f'QStringLiteral("{field}")', local)
        self.assertIn('QStringLiteral("sequence")', BRIDGE)
        self.assertIn("lastPeerMouseSequence", BRIDGE)

    def test_remote_network_ticks_are_16_ms(self):
        self.assertIn("g_remote_client_timer->setInterval(16);", BRIDGE)
        self.assertIn("m_timer->setInterval(16);", BRIDGE)

    def test_preview_predicts_dialog_drag_in_cells_on_both_sides(self):
        preview = BRIDGE.split("class RemotePreviewWidget final", 1)[1].split(
            "class ServerDialog final", 1
        )[0]
        self.assertIn("struct DragPrediction", preview)
        self.assertIn("beginDragPrediction", preview)
        self.assertIn("updateDragPrediction(m_peerDrag, mouse)", preview)
        self.assertIn("updateDragPrediction(m_serverDrag, command)", preview)
        self.assertIn('QStringLiteral("charColumn")', preview)
        self.assertIn('QStringLiteral("charRow")', preview)
        self.assertIn("qMax(0, columns - 2)", preview)
        self.assertIn("qMax(0, rows - 1)", preview)


if __name__ == "__main__":
    unittest.main()
