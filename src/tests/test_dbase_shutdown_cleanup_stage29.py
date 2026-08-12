from __future__ import annotations

import importlib.util
import struct
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from d64dbase import compile_dbase_to_assembly

CPP = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
HDR = (ROOT / "d64qt5" / "d64qt5_bridge.h").read_text(encoding="utf-8")
DEF = (ROOT / "d64qt5" / "d64qt5_bridge.def").read_text(encoding="utf-8")


def load_d64():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_stage29_shutdown_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseShutdownCleanupStage29Tests(unittest.TestCase):
    SOURCE = '''
_app.security = new Session()
? LOGINSESSION
? "after dialog"
'''

    def compile(self, target: str):
        return compile_dbase_to_assembly(
            self.SOURCE,
            filename=f"shutdown_stage29_{target}.dbase",
            target=target,
            windows_application_mode="GUI",
        )

    def test_main_window_owns_central_close_path(self):
        self.assertIn("class DBaseMainWindow final : public QMainWindow", CPP)
        self.assertIn("void closeEvent(QCloseEvent *event) override", CPP)
        self.assertIn("request_runtime_shutdown();", CPP)
        self.assertIn("QMainWindow::closeEvent(event);", CPP)

    def test_shutdown_cancels_focused_login_and_closes_top_levels(self):
        self.assertIn("cancel_login_dialog();", CPP)
        self.assertIn("g_login_dialog->reject();", CPP)
        self.assertIn("QApplication::topLevelWidgets()", CPP)
        self.assertIn("if (!widget || widget == g_window)", CPP)
        self.assertIn("widget->close();", CPP)
        self.assertIn("g_app->quit();", CPP)

    def test_shutdown_state_is_exported_and_exec_will_not_restart(self):
        self.assertIn("DBaseQtShutdownRequested", CPP)
        self.assertIn("DBaseQtShutdownRequested", HDR)
        self.assertIn("DBaseQtShutdownRequested", DEF)
        self.assertIn("if (g_shutdown_requested)\n        return 0;", CPP)
        self.assertIn("g_shutdown_requested = false;", CPP)

    def test_runtime_cleanup_deletes_qt_objects_sessions_and_menu_nodes(self):
        shutdown = CPP[CPP.index('extern "C" D64QT5_API void DBaseQtShutdown(void)'):]
        self.assertLess(shutdown.index("request_runtime_shutdown();"), shutdown.index("delete g_window;"))
        self.assertIn("close_runtime_data_files();", shutdown)
        self.assertIn("for (MenuNode *node : g_menu_nodes)", shutdown)
        self.assertIn("delete node;", shutdown)
        self.assertIn("for (SessionNode *session : g_session_nodes)", shutdown)
        self.assertIn("delete session;", shutdown)
        self.assertIn("delete g_app;", shutdown)

    def test_generated_code_jumps_to_one_cleanup_path(self):
        for target in ("pe32", "pe64"):
            asm = self.compile(target).assembly
            self.assertIn(
                'import DBaseQtShutdownRequested, "d64qt5.dll", "DBaseQtShutdownRequested"',
                asm,
            )
            self.assertGreaterEqual(asm.count("call DBaseQtShutdownRequested"), 2)
            cleanup_lines = [line[:-1] for line in asm.splitlines() if line.startswith("__dbase_program_cleanup_") and line.endswith(":" )]
            self.assertEqual(len(cleanup_lines), 1)
            cleanup = cleanup_lines[0]
            self.assertIn(f"jne {cleanup}", asm)
            cleanup_pos = asm.index(cleanup + ":")
            shutdown_pos = asm.index("call DBaseQtShutdown", cleanup_pos)
            free_pos = asm.index("call VirtualFree", shutdown_pos)
            self.assertLess(cleanup_pos, shutdown_pos)
            self.assertLess(shutdown_pos, free_pos)

    def test_pe32_pe64_internal_link_with_shutdown_import(self):
        d64 = load_d64()
        for target, magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = self.compile(target)
            program = (
                d64.assemble_pe32_source(result.assembly, filename="shutdown29_32.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="shutdown29_64.asm", gui=True)
            )
            pe = struct.unpack_from("<I", program.executable, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24)[0], magic)
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24 + 68)[0], 2)


if __name__ == "__main__":
    unittest.main()
