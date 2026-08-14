from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORK = (ROOT / "d64qt5" / "d64_workstation.cpp").read_text(encoding="utf-8")
HDR = (ROOT / "d64qt5" / "d64_workstation.h").read_text(encoding="utf-8")
BRIDGE = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
PRO = (ROOT / "d64qt5" / "d64qt5_bridge.pro").read_text(encoding="utf-8")


class WorkstationSingletonStage39Tests(unittest.TestCase):
    def test_uses_windows_global_named_singleton(self):
        self.assertIn('L"Global\\\\dBase2Many.D64Workstation.Singleton"', WORK)
        self.assertIn('L"Global\\\\dBase2Many.D64Workstation.Ready"', WORK)
        self.assertIn("CreateMutexW(", WORK)
        self.assertIn("CreateEventW(", WORK)
        self.assertIn("WaitForSingleObject(g_workstation_mutex, 0)", WORK)

    def test_workstation_desktop_has_stable_shared_name(self):
        self.assertIn('L"D64Workstation"', WORK)
        self.assertNotIn('L"D64Workstation_%lu"', WORK)

    def test_owner_creates_joiner_opens_same_desktop(self):
        prepare = WORK.split("bool D64WorkstationPrepare()", 1)[1].split(
            "bool D64WorkstationActivate", 1
        )[0]
        self.assertIn("if (g_workstation_owner)", prepare)
        self.assertIn("CreateDesktopW(", prepare)
        self.assertIn("OpenDesktopW(", prepare)
        self.assertIn("SetThreadDesktop(g_work_desktop)", prepare)
        self.assertIn("SetEvent(g_workstation_ready_event)", prepare)

    def test_joined_activation_does_not_create_second_panel(self):
        block = WORK.split("bool D64WorkstationActivate(HWND mainWindow)", 1)[1].split(
            "bool D64WorkstationInstallKeyboardGuard", 1
        )[0]
        joined = block.split("if (!g_workstation_owner)", 1)[1].split(
            "/* OWNER", 1
        )[0]
        self.assertIn("SetForegroundWindow(mainWindow);", joined)
        self.assertNotIn("create_exit_window", joined)
        self.assertNotIn("SwitchDesktop", joined)

    def test_only_owner_installs_keyboard_guard(self):
        block = WORK.split(
            "bool D64WorkstationInstallKeyboardGuard(HWND mainWindow)", 1
        )[1].split("void D64WorkstationBeginLeave", 1)[0]
        self.assertIn("if (!g_workstation_owner)", block)
        self.assertIn("return true;", block)
        self.assertIn("SetWindowsHookExW(", block)

    def test_joined_shutdown_does_not_switch_or_destroy_owner_workstation(self):
        block = WORK.split("void D64WorkstationBeginLeave()", 1)[1].split(
            "void D64WorkstationFinalizeLeave", 1
        )[0]
        joined = block.split("if (!g_workstation_owner)", 1)[1].split(
            "if (g_keyboard_hook)", 1
        )[0]
        self.assertNotIn("SwitchDesktop", joined)
        self.assertNotIn("destroy_exit_window", joined)

    def test_owner_join_state_is_exposed_in_workstation_header(self):
        self.assertIn("bool D64WorkstationOwnsDesktop();", HDR)
        self.assertIn("bool D64WorkstationJoinedExisting();", HDR)

    def test_bridge_prepares_before_qapplication(self):
        init = BRIDGE.split("extern \"C\" D64QT5_API int DBaseQtInitialize", 1)[1]
        self.assertLess(init.index("D64WorkstationPrepare()"), init.index("new QApplication"))

    def test_qmake_build_contains_workstation_source(self):
        self.assertIn("d64_workstation.cpp", PRO)
        self.assertIn("d64_workstation.h", PRO)


if __name__ == "__main__":
    unittest.main()
