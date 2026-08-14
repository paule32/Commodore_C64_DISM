from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORK = (ROOT / "d64qt5" / "d64_workstation.cpp").read_text(encoding="utf-8")
HDR = (ROOT / "d64qt5" / "d64_workstation.h").read_text(encoding="utf-8")
BRIDGE = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")


class ApplicationMutexNoFlashStage42Tests(unittest.TestCase):
    def test_every_main_application_has_global_path_based_mutex(self):
        self.assertIn('L"Global\\\\dBase2Many.D64Application."', WORK)
        self.assertIn("g_application_mutex", WORK)
        self.assertIn("current_application_path()", WORK)
        self.assertIn("application_path_hash", WORK)
        self.assertIn("CreateMutexW(\n        nullptr,\n        FALSE,\n        g_application_mutex_name.c_str()", WORK)
        self.assertIn("GetLastError() == ERROR_ALREADY_EXISTS", WORK)
        self.assertIn("release_application_instance();", WORK)

    def test_application_mutex_is_acquired_before_workstation_role(self):
        block = WORK.split("bool D64WorkstationPrepare()", 1)[1].split(
            "bool D64WorkstationActivate", 1
        )[0]
        self.assertLess(
            block.index("acquire_application_instance()"),
            block.index("acquire_singleton_role()"),
        )

    def test_duplicate_manual_instance_activates_existing_application(self):
        block = WORK.split("bool acquire_application_instance()", 1)[1].split(
            "void release_application_instance", 1
        )[0]
        self.assertIn("ERROR_ALREADY_EXISTS", block)
        self.assertIn("activate_existing_application_by_path(g_application_path);", block)
        self.assertIn("return false;", block)

    def test_icon_launch_is_serialized_until_instance_is_ready(self):
        block = WORK.split("bool D64WorkstationLaunchProgram(", 1)[1].split(
            "bool D64WorkstationApplicationInstanceOwned", 1
        )[0]
        self.assertIn('L".LaunchGate"', block)
        self.assertIn('L".InstanceReady"', block)
        self.assertIn("WaitForSingleObject(gate, 5000)", block)
        self.assertIn("OpenMutexW(SYNCHRONIZE, FALSE, instanceName.c_str())", block)
        self.assertIn("activate_existing_application_by_path(canonicalPath);", block)
        self.assertIn("WaitForMultipleObjects(2, waits, FALSE, 2000)", block)

    def test_existing_instance_branch_does_not_create_second_process(self):
        block = WORK.split("HANDLE existing = OpenMutexW", 1)[1].split(
            "HANDLE readyEvent", 1
        )[0]
        self.assertIn("activate_existing_application_by_path(canonicalPath);", block)
        self.assertNotIn("CreateProcessW", block)

    def test_ready_event_is_signalled_after_application_window_activation(self):
        activate = WORK.split("bool D64WorkstationActivate(HWND mainWindow)", 1)[1].split(
            "bool D64WorkstationInstallKeyboardGuard", 1
        )[0]
        self.assertGreaterEqual(activate.count("signal_application_ready();"), 2)

    def test_existing_application_is_found_by_main_window_property(self):
        self.assertIn("application_window_property_name", WORK)
        self.assertIn("SetPropW(", WORK)
        self.assertIn("GetPropW(hwnd, context->propertyName->c_str())", WORK)
        self.assertIn("mark_application_main_window(mainWindow);", WORK)
        self.assertIn("RemovePropW(", WORK)
        self.assertNotIn("QueryFullProcessImageNameW", WORK)

    def test_application_instance_state_is_exposed_for_diagnostics(self):
        self.assertIn("bool D64WorkstationApplicationInstanceOwned();", HDR)
        self.assertIn("const wchar_t *D64WorkstationApplicationMutexName();", HDR)

    def test_db_restore_does_not_foreground_main_before_login_restore(self):
        callback = BRIDGE.split("void workstation_db_requested()", 1)[1].split(
            "void show_runtime_warning", 1
        )[0]
        self.assertLess(
            callback.index("g_window->show();"),
            callback.index("enforce_console_80x25_grid();"),
        )
        self.assertIn("Qt::WA_DontShowOnScreen", callback)
        self.assertLess(
            callback.index("restore_owner_application_windows();"),
            callback.index("g_window->raise();"),
        )
        before_restore = callback.split("restore_owner_application_windows();", 1)[0]
        self.assertNotIn("g_window->activateWindow();", before_restore)

    def test_joined_first_frame_is_prepared_offscreen(self):
        show = BRIDGE.split('extern "C" D64QT5_API void DBaseQtShowWindow(void)', 1)[1].split(
            'extern "C" D64QT5_API void DBaseQtProcessEvents', 1
        )[0]
        self.assertIn("D64WorkstationJoinedExisting()", show)
        self.assertIn("Qt::WA_DontShowOnScreen", show)
        self.assertIn("QEventLoop::ExcludeUserInputEvents", show)
        self.assertIn("enforce_console_80x25_grid();", show)

    def test_joined_activation_still_never_switches_desktop(self):
        activate = WORK.split("bool D64WorkstationActivate(HWND mainWindow)", 1)[1].split(
            "bool D64WorkstationInstallKeyboardGuard", 1
        )[0]
        joined = activate.split("if (!g_workstation_owner)", 1)[1].split("/* OWNER", 1)[0]
        self.assertNotIn("SwitchDesktop", joined)


if __name__ == "__main__":
    unittest.main()
