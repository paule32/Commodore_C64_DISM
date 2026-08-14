from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "d64qt5" / "d64qt5_bridge.cpp"
PRO = ROOT / "d64qt5" / "d64qt5_bridge.pro"
WORK_CPP = ROOT / "d64qt5" / "d64_workstation.cpp"
WORK_H = ROOT / "d64qt5" / "d64_workstation.h"


class WorkstationStage34Tests(unittest.TestCase):
    def test_sources_are_part_of_qmake_project(self):
        text = PRO.read_text(encoding="utf-8")
        self.assertIn("d64_workstation.cpp", text)
        self.assertIn("d64_workstation.h", text)
        self.assertIn("-luser32", text)

    def test_prepare_happens_before_qapplication_creation(self):
        text = BRIDGE.read_text(encoding="utf-8")
        init = text.index('extern "C" D64QT5_API int DBaseQtInitialize')
        prepare = text.index("D64WorkstationPrepare()", init)
        create_app = text.index("new QApplication", init)
        self.assertLess(prepare, create_app)

    def test_show_installs_keyboard_guard(self):
        text = BRIDGE.read_text(encoding="utf-8")
        show = text.index('extern "C" D64QT5_API void DBaseQtShowWindow')
        self.assertIn("D64WorkstationInstallKeyboardGuard", text[show:show+1800])
        self.assertIn("g_window->winId()", text[show:show+1800])

    def test_shutdown_switches_back_then_finalizes_after_qt_cleanup(self):
        text = BRIDGE.read_text(encoding="utf-8")
        request = text.index("void request_runtime_shutdown()")
        begin = text.index("D64WorkstationBeginLeave()", request)
        shutdown = text.index('extern "C" D64QT5_API void DBaseQtShutdown')
        finalize = text.index("D64WorkstationFinalizeLeave()", shutdown)
        delete_window = text.index("delete g_window", shutdown)
        self.assertLess(begin, shutdown)
        self.assertGreater(finalize, delete_window)

    def test_win32_desktop_and_guard_apis_are_present(self):
        text = WORK_CPP.read_text(encoding="utf-8")
        for token in (
            "CreateDesktopW(",
            "SwitchDesktop(",
            "OpenInputDesktop(",
            "SetThreadDesktop(",
            "CloseDesktop(",
            "WH_KEYBOARD_LL",
            "SetWindowsHookExW(",
            "UnhookWindowsHookEx(",
        ):
            self.assertIn(token, text)

    def test_guard_blocks_requested_shell_shortcuts(self):
        text = WORK_CPP.read_text(encoding="utf-8")
        for token in (
            "VK_LWIN",
            "VK_RWIN",
            "VK_TAB",
            "VK_ESCAPE",
            "VK_F12",
            "WM_CLOSE",
        ):
            self.assertIn(token, text)

    def test_no_explorer_shell_is_started(self):
        text = WORK_CPP.read_text(encoding="utf-8").lower()
        # Stage 38 uses CreateProcessW intentionally for BTX.exe on the private
        # desktop. It must still never start Explorer/the normal shell.
        self.assertNotIn('shellexecute', text)
        self.assertNotIn('explorer.exe', text)

    def test_public_workstation_lifecycle_is_declared(self):
        text = WORK_H.read_text(encoding="utf-8")
        for token in (
            "D64WorkstationPrepare",
            "D64WorkstationInstallKeyboardGuard",
            "D64WorkstationBeginLeave",
            "D64WorkstationFinalizeLeave",
            "D64WorkstationIsActive",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
