from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "d64qt5" / "d64qt5_bridge.cpp"
WORK_CPP = ROOT / "d64qt5" / "d64_workstation.cpp"
WORK_H = ROOT / "d64qt5" / "d64_workstation.h"
SMOKE = ROOT / "d64qt5" / "workstation_smoke_test.cpp"


class WorkstationStage35Tests(unittest.TestCase):
    def test_prepare_binds_gui_thread_before_any_desktop_switch(self):
        text = WORK_CPP.read_text(encoding="utf-8")
        prepare = text.index("bool D64WorkstationPrepare()")
        activate = text.index("bool D64WorkstationActivate", prepare)
        body = text[prepare:activate]
        set_thread = body.index("SetThreadDesktop(g_work_desktop)")
        self.assertGreater(set_thread, 0)
        self.assertNotIn("SwitchDesktop(g_work_desktop)", body)

    def test_activate_requires_visible_real_window_before_switch(self):
        text = WORK_CPP.read_text(encoding="utf-8")
        start = text.index("bool D64WorkstationActivate")
        end = text.index("bool D64WorkstationInstallKeyboardGuard", start)
        body = text[start:end]
        self.assertIn("IsWindow(mainWindow)", body)
        self.assertIn("IsWindowVisible(mainWindow)", body)
        self.assertIn("SwitchDesktop(g_work_desktop)", body)
        self.assertLess(body.index("IsWindowVisible(mainWindow)"), body.index("SwitchDesktop(g_work_desktop)"))

    def test_bridge_creates_native_window_before_activating_workstation(self):
        text = BRIDGE.read_text(encoding="utf-8")
        start = text.index('extern "C" D64QT5_API void DBaseQtShowWindow')
        end = text.index('extern "C" D64QT5_API void DBaseQtProcessEvents', start)
        body = text[start:end]
        self.assertIn("g_window->show()", body)
        self.assertIn("g_window->winId()", body)
        self.assertIn("D64WorkstationActivate(workstation_hwnd)", body)
        self.assertLess(body.index("g_window->winId()"), body.index("D64WorkstationActivate(workstation_hwnd)"))

    def test_keyboard_guard_is_only_installed_after_successful_activation(self):
        text = BRIDGE.read_text(encoding="utf-8")
        start = text.index('extern "C" D64QT5_API void DBaseQtShowWindow')
        end = text.index('extern "C" D64QT5_API void DBaseQtProcessEvents', start)
        body = text[start:end]
        activate = body.index("D64WorkstationActivate(workstation_hwnd)")
        guard = body.index("D64WorkstationInstallKeyboardGuard(workstation_hwnd)")
        self.assertLess(activate, guard)
        self.assertIn("D64WorkstationIsVisible()", body)

    def test_activation_failure_requests_clean_shutdown(self):
        text = BRIDGE.read_text(encoding="utf-8")
        start = text.index('extern "C" D64QT5_API void DBaseQtShowWindow')
        end = text.index('extern "C" D64QT5_API void DBaseQtProcessEvents', start)
        body = text[start:end]
        failure = body.index("if (!D64WorkstationActivate(workstation_hwnd))")
        self.assertIn("request_runtime_shutdown();", body[failure:failure + 300])

    def test_shutdown_returns_to_original_input_desktop_before_final_close(self):
        text = WORK_CPP.read_text(encoding="utf-8")
        begin = text.index("void D64WorkstationBeginLeave()")
        finalize = text.index("void D64WorkstationFinalizeLeave()", begin)
        begin_body = text[begin:finalize]
        self.assertIn("switch_to_original_input_desktop();", begin_body)
        final_body = text[finalize:text.index("bool D64WorkstationIsActive", finalize)]
        self.assertIn("SetThreadDesktop(g_original_thread_desktop)", final_body)
        self.assertIn("close_desktop_handle(g_work_desktop)", final_body)

    def test_root_desktop_fallback_is_available(self):
        text = WORK_CPP.read_text(encoding="utf-8")
        self.assertIn('L"Default"', text)
        self.assertIn("OpenDesktopW(", text)
        self.assertIn("g_original_input_name", text)

    def test_smoke_test_uses_prepare_create_show_activate_order(self):
        text = SMOKE.read_text(encoding="utf-8")
        prepare = text.index("D64WorkstationPrepare()")
        create = text.index("CreateWindowExW(")
        show = text.index("ShowWindow(hwnd", create)
        activate = text.index("D64WorkstationActivate(hwnd)", show)
        guard = text.index("D64WorkstationInstallKeyboardGuard(hwnd)", activate)
        self.assertLess(prepare, create)
        self.assertLess(create, show)
        self.assertLess(show, activate)
        self.assertLess(activate, guard)

    def test_header_exposes_activation_state(self):
        text = WORK_H.read_text(encoding="utf-8")
        self.assertIn("D64WorkstationActivate(HWND mainWindow)", text)
        self.assertIn("D64WorkstationIsVisible()", text)


if __name__ == "__main__":
    unittest.main()
