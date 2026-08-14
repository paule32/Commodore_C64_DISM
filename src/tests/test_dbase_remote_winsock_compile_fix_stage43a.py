from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
PRO = (ROOT / "d64qt5" / "d64qt5_bridge.pro").read_text(encoding="utf-8")


class RemoteWinsockCompileFixStage43ATests(unittest.TestCase):
    def test_server_dialog_uses_global_winsock_connect(self):
        server = BRIDGE.split("class ServerDialog final", 1)[1].split(
            "void workstation_server_requested", 1
        )[0]
        self.assertIn("const int result = ::connect(", server)
        self.assertIn("reinterpret_cast<const sockaddr *>(&address)", server)
        self.assertIn("static_cast<int>(sizeof(address))", server)
        self.assertNotRegex(server, r"(?<!:)\bconnect\s*\(\s*socketValue")

    def test_remote_native_winsock_calls_are_globally_qualified(self):
        remote = BRIDGE.split("Stage 43: zeichenorientierte IPv4", 1)[1].split(
            "#endif // _WIN32", 1
        )[0]
        for name in (
            "socket", "bind", "listen", "accept", "send", "recv",
            "shutdown", "closesocket", "ioctlsocket", "setsockopt",
            "getsockopt", "inet_pton", "htons", "WSAStartup",
            "WSAGetLastError", "WSACleanup",
        ):
            pattern = re.compile(rf"(?<![:\w]){name}\s*\(")
            self.assertIsNone(pattern.search(remote), f"unqualified Winsock call: {name}")

    def test_qt_signal_connections_remain_qobject_connect(self):
        self.assertIn("QObject::connect(m_connect, &QPushButton::clicked", BRIDGE)
        self.assertIn("QObject::connect(m_timer, &QTimer::timeout", BRIDGE)

    def test_winsock_library_is_still_linked(self):
        self.assertIn("-lws2_32", PRO)


if __name__ == "__main__":
    unittest.main()
