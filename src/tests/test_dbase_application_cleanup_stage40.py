from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
WORK = (ROOT / "d64qt5" / "d64_workstation.cpp").read_text(encoding="utf-8")
HDR = (ROOT / "d64qt5" / "d64_workstation.h").read_text(encoding="utf-8")


class ApplicationCleanupStage40Tests(unittest.TestCase):
    def test_joined_application_close_is_real_shutdown(self):
        block = BRIDGE.split("class DBaseMainWindow final", 1)[1].split(
            "QString choose_menu_font_family", 1
        )[0]
        self.assertIn("D64WorkstationJoinedExisting()", block)
        joined = block.split("if (D64WorkstationJoinedExisting())", 1)[1]
        self.assertIn("request_runtime_shutdown();", joined)
        self.assertIn("QMainWindow::closeEvent(event);", joined)

    def test_owner_keeps_stage38_restore_semantics(self):
        block = BRIDGE.split("class DBaseMainWindow final", 1)[1].split(
            "QString choose_menu_font_family", 1
        )[0]
        self.assertIn("hide();", block)
        self.assertIn("event->ignore();", block)

    def test_shutdown_rejects_and_hides_all_dialogs(self):
        block = BRIDGE.rsplit("void close_runtime_application_windows()", 1)[1].split(
            "void request_runtime_shutdown()", 1
        )[0]
        self.assertIn("QApplication::topLevelWidgets()", block)
        self.assertIn("qobject_cast<QDialog *>", block)
        self.assertIn("dialog->reject();", block)
        self.assertIn("QPointer<QWidget> guard(widget);", block)
        self.assertIn("guard->hide();", block)
        self.assertIn("dialog->reject();", block)
        self.assertIn("if (guard)", block)
        self.assertIn("widget->close();", block)
        self.assertIn("D64WorkstationCloseApplicationWindows(mainWindow);", block)

    def test_shutdown_closes_databases_before_sessions(self):
        block = BRIDGE.split("void request_runtime_shutdown()", 1)[1].split(
            "void show_login_dialog(SessionNode *session)", 1
        )[0]
        self.assertIn("close_runtime_application_windows();", block)
        self.assertIn("close_runtime_data_files();", block)
        self.assertIn("invalidate_runtime_sessions();", block)
        self.assertLess(block.index("close_runtime_application_windows();"), block.index("close_runtime_data_files();"))
        self.assertLess(block.index("close_runtime_data_files();"), block.index("invalidate_runtime_sessions();"))

    def test_database_password_is_zeroed_on_application_close(self):
        block = BRIDGE.rsplit("void close_runtime_data_files()", 1)[1].split(
            "void invalidate_runtime_sessions()", 1
        )[0]
        self.assertIn("database_close_internal(database);", block)
        self.assertIn("database->passwordValue.fill(QChar(0));", block)
        self.assertIn("database->passwordValue.clear();", block)

    def test_sessions_are_invalidated_before_delete(self):
        block = BRIDGE.rsplit("void invalidate_runtime_sessions()", 1)[1].split(
            "void close_runtime_application_windows()", 1
        )[0]
        self.assertIn("session->authenticated = false;", block)
        self.assertIn("session->username.clear();", block)
        self.assertIn("session->group.clear();", block)
        self.assertIn("g_active_login_session = nullptr;", block)

    def test_native_windows_of_current_process_are_hidden_then_closed(self):
        self.assertIn("void D64WorkstationCloseApplicationWindows(HWND mainWindow);", HDR)
        block = WORK.split("void D64WorkstationCloseApplicationWindows(HWND mainWindow)", 1)[1].split(
            "bool D64WorkstationLaunchProgram", 1
        )[0]
        self.assertIn("GetCurrentProcessId()", block)
        self.assertIn("EnumDesktopWindows", block)
        callback = WORK.split("BOOL CALLBACK close_current_application_window", 1)[1].split(
            "void D64WorkstationCloseApplicationWindows", 1
        )[0]
        self.assertIn("GetWindowThreadProcessId", callback)
        self.assertIn("ShowWindow(hwnd, SW_HIDE);", callback)
        self.assertIn("PostMessageW(hwnd, WM_CLOSE, 0, 0);", callback)
        self.assertIn("hwnd == g_exit_window", callback)

    def test_generated_cleanup_still_releases_virtual_memory(self):
        old_test = (ROOT / "tests" / "test_dbase_shutdown_cleanup_stage29.py").read_text(encoding="utf-8")
        self.assertIn('asm.index("call VirtualFree", shutdown_pos)', old_test)


if __name__ == "__main__":
    unittest.main()
