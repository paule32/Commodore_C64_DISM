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
    name = "_d64_dbase_stage12_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseQt5CppBridgeStage12Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cpp = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")

    def test_bridge_uses_tabbar_and_stack_not_corner_widget(self):
        self.assertIn("new QTabBar(g_header)", self.cpp)
        self.assertIn("new QStackedWidget(g_root)", self.cpp)
        self.assertNotIn("setCornerWidget(", self.cpp)

    def test_console_and_debug_widgets_expand(self):
        self.assertIn("new QPlainTextEdit(g_console_frame)", self.cpp)
        self.assertIn("new QPlainTextEdit(g_debug_frame)", self.cpp)
        self.assertIn("new QLineEdit(g_debug_frame)", self.cpp)
        self.assertIn("QSizePolicy::Expanding, QSizePolicy::Expanding", self.cpp)
        self.assertIn("QSizePolicy::Expanding, QSizePolicy::Fixed", self.cpp)

    def test_output_does_not_horizontally_scroll_away(self):
        self.assertIn("editor->horizontalScrollBar()", self.cpp)
        self.assertIn("h->setValue(h->minimum())", self.cpp)
        self.assertIn("v->setValue(v->maximum())", self.cpp)
        self.assertNotIn("editor->ensureCursorVisible()", self.cpp)

    def test_codegen_uses_c_bridge_for_both_targets(self):
        source = '? "console"\nSET DEBUG ON\n? "debug"\nSET DEBUG OFF\n? "console2"\n'
        for target in ("pe32", "pe64"):
            asm = compile_dbase_to_assembly(source, target=target).assembly
            for symbol in (
                "DBaseQtInitialize", "DBaseQtShowWindow", "DBaseQtSetDebugVisible",
                "DBaseQtAppendConsole", "DBaseQtAppendDebug", "DBaseQtExec",
            ):
                self.assertIn(f'import {symbol}, "d64qt5.dll", "{symbol}"', asm)

    def test_pe32_and_pe64_link_as_gui(self):
        d64 = load_d64()
        source = '? "console"\nSET DEBUG ON\n? "debug"\n'
        for target, magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(source, target=target)
            program = (
                d64.assemble_pe32_source(result.assembly, filename="stage12_32.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="stage12_64.asm", gui=True)
            )
            pe = struct.unpack_from("<I", program.executable, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24)[0], magic)
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24 + 68)[0], 2)


if __name__ == "__main__":
    unittest.main()
