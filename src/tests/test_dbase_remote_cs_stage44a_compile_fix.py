from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")


class RemoteCsStage44ACompileFixTests(unittest.TestCase):
    def test_zoom_helper_declared_before_server_dialog(self):
        decl = "QToolButton *make_zoom_button(bool plus, QWidget *parent);"
        server = "class ServerDialog final : public QDialog"
        definition = "QToolButton *make_zoom_button(bool plus, QWidget *parent)\n{"
        self.assertIn(decl, BRIDGE)
        self.assertIn(server, BRIDGE)
        self.assertIn(definition, BRIDGE)
        self.assertLess(BRIDGE.index(decl), BRIDGE.index(server))
        self.assertLess(BRIDGE.index(server), BRIDGE.index(definition))

    def test_incomplete_server_pointer_comparison_is_explicit(self):
        start = BRIDGE.index("class RemoteClientEventFilter final")
        end = BRIDGE.index("void remote_broadcast_session_identity()", start)
        block = BRIDGE[start:end]
        self.assertIn('top == reinterpret_cast<QWidget *>(g_server_dialog)', block)
        self.assertNotIn('top == g_server_dialog ||', block)


if __name__ == "__main__":
    unittest.main()
