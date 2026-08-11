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


def load_d64():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_dbase_qt5_stage5_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseQt5GuiStage5Tests(unittest.TestCase):
    def test_generated_assembly_uses_qt5_bridge_not_text_console(self):
        source = 'X=2+3*4\n? "Wert von X = " + X\n'
        for target in ("pe32", "pe64"):
            result = compile_dbase_to_assembly(source, target=target)
            self.assertEqual(result.windows_application_mode, "GUI")
            self.assertEqual(result.transcript, "Wert von X = 14\r\n")
            asm = result.assembly
            self.assertIn('import DBaseQtInitialize, "d64qt5.dll"', asm)
            self.assertIn("call DBaseQtShowWindow", asm)
            self.assertIn("call DBaseQtAppendConsole", asm)
            self.assertIn("call DBaseQtMarkProgramFinished", asm)
            self.assertIn("call DBaseQtExec", asm)
            self.assertNotIn("AllocConsole", asm)
            self.assertNotIn("GetStdHandle", asm)
            self.assertNotIn("WriteFile", asm)
            self.assertNotIn("cmd.exe", asm.casefold())

    def test_debug_on_off_controls_tab_and_output_function(self):
        source = (
            'SET FORMAT TO CONSOLE\n'
            'SET DEBUG ON\n'
            '? "debug"\n'
            'SET DEBUG OFF\n'
            '? "console"\n'
        )
        asm = compile_dbase_to_assembly(source).assembly
        self.assertIn("call DBaseQtSetDebugVisible", asm)
        self.assertIn("call DBaseQtAppendDebug", asm)
        self.assertIn("call DBaseQtAppendConsole", asm)
        self.assertIn("push 1\n    call DBaseQtSetDebugVisible", asm)
        self.assertIn("push 0\n    call DBaseQtSetDebugVisible", asm)

    def test_bridge_source_builds_two_plaintext_tabs_and_debug_input(self):
        cpp = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
        self.assertIn("new QTabBar(g_header)", cpp)
        self.assertIn("new QStackedWidget(g_root)", cpp)
        self.assertIn("new QPlainTextEdit(g_console_frame)", cpp)
        self.assertIn("new QPlainTextEdit(g_debug_frame)", cpp)
        self.assertIn("new QLineEdit(g_debug_frame)", cpp)
        self.assertIn('QStringLiteral("Konsole")', cpp)
        self.assertIn('QStringLiteral("DEBUG")', cpp)
        self.assertIn("QFrame::NoFrame", cpp)
        self.assertIn("returnPressed", cpp)
        self.assertIn("g_app->exec()", cpp)

    def test_program_code_starts_after_gui_setup(self):
        asm = compile_dbase_to_assembly('X=14\n? X\n').assembly
        show = asm.index("call DBaseQtShowWindow")
        process = asm.index("call DBaseQtProcessEvents", show)
        assignment = asm.index("fstp qword ptr [__dbase_var_x_num]")
        self.assertLess(show, process)
        self.assertLess(process, assignment)

    def test_pe32_and_pe64_link_as_gui(self):
        d64 = load_d64()
        source = 'X=2+3*4\n? "X=" + X\n'
        for target, magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(source, target=target)
            program = (
                d64.assemble_pe32_source(result.assembly, filename="qt32.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="qt64.asm", gui=True)
            )
            pe = struct.unpack_from("<I", program.executable, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24)[0], magic)
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24 + 68)[0], 2)


if __name__ == "__main__":
    unittest.main()
