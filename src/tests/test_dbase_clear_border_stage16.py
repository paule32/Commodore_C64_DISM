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

from d64dbase import (
    DBaseCompilerError,
    DBaseClearScreenStatement,
    DBaseSetBorderColorStatement,
    compile_dbase_to_assembly,
    parse_dbase_statements,
)


def load_d64():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_dbase_stage16_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseClearBorderStage16Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cpp = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
        cls.header = (ROOT / "d64qt5" / "d64qt5_bridge.h").read_text(encoding="utf-8")
        cls.def_file = (ROOT / "d64qt5" / "d64qt5_bridge.def").read_text(encoding="utf-8")

    def test_clear_screen_parses_and_clears_preview(self):
        source = 'SET COLOR TO "W/N"\n? "vorher"\nCLEAR SCREEN\n? "nachher"\n'
        statements = parse_dbase_statements(source, filename="clear16.dbase")
        self.assertTrue(any(isinstance(s, DBaseClearScreenStatement) for s in statements))
        result = compile_dbase_to_assembly(source, filename="clear16.dbase", target="pe32")
        self.assertEqual(result.transcript, "nachher\r\n")
        self.assertIn('import DBaseQtClearScreen, "d64qt5.dll", "DBaseQtClearScreen"', result.assembly)
        self.assertIn("call DBaseQtClearScreen", result.assembly)

    def test_bordercolor_string_and_rgb(self):
        source = '''
SET BORDERCOLOR TO "ActiveBorder"
SET BORDERCOLOR TO RGB(FF,00,80)
? "ok"
'''
        statements = parse_dbase_statements(source, filename="border16.dbase")
        self.assertEqual(sum(isinstance(s, DBaseSetBorderColorStatement) for s in statements), 2)
        result = compile_dbase_to_assembly(source, filename="border16.dbase", target="pe32")
        self.assertEqual(result.assembly.count("call DBaseQtSetBorderColor"), 2)
        self.assertIn('import DBaseQtSetBorderColor, "d64qt5.dll", "DBaseQtSetBorderColor"', result.assembly)

    def test_bordercolor_variable_function_macro(self):
        source = '''
#define FRAME "InactiveBorder"
function getBorder()
    return RGB(00,FF,00)
C = "WindowFrame"
SET BORDERCOLOR TO C
SET BORDERCOLOR TO getBorder()
SET BORDERCOLOR TO FRAME
? "ok"
'''
        result = compile_dbase_to_assembly(source, filename="border_symbols16.dbase", target="pe32")
        self.assertEqual(result.assembly.count("call DBaseQtSetBorderColor"), 3)

    def test_unquoted_system_name_and_undefined_function_fail(self):
        for rhs in ("ActiveBorder", "ActiveBorder()"):
            with self.assertRaises(DBaseCompilerError):
                compile_dbase_to_assembly(
                    f"SET BORDERCOLOR TO {rhs}\n",
                    filename="bad_border16.dbase",
                    target="pe32",
                )

    def test_invalid_border_string_fails(self):
        with self.assertRaises(DBaseCompilerError):
            compile_dbase_to_assembly(
                'SET BORDERCOLOR TO "NichtEineSystemfarbe"\n',
                filename="bad_border_literal16.dbase",
                target="pe32",
            )

    def test_clear_and_border_work_nested_in_if(self):
        source = '''
X = 1
IF X == 1
    SET COLOR TO "B*/W+"
    SET BORDERCOLOR TO RGB(FF,FF,00)
    CLEAR SCREEN
    ? "nested"
ENDIF
'''
        result = compile_dbase_to_assembly(source, filename="nested16.dbase", target="pe32")
        self.assertIn("call DBaseQtSetBorderColor", result.assembly)
        self.assertIn("call DBaseQtClearScreen", result.assembly)
        self.assertEqual(result.transcript, "nested\r\n")

    def test_clear_and_border_work_inside_function(self):
        source = '''
function prepare()
    SET COLOR TO "W/N"
    SET BORDERCOLOR TO RGB(00,FF,00)
    CLEAR SCREEN
    return "ready"
X = prepare()
? X
'''
        result = compile_dbase_to_assembly(source, filename="routine16.dbase", target="pe64")
        self.assertIn("call DBaseQtSetBorderColor", result.assembly)
        self.assertIn("call DBaseQtClearScreen", result.assembly)

    def test_bridge_clear_uses_output_background_and_preserves_border_state(self):
        self.assertIn("DBaseQtClearScreen", self.cpp)
        self.assertIn("g_console_background = g_output_background", self.cpp)
        self.assertIn("g_console_border_color", self.cpp)
        self.assertIn("apply_console_appearance()", self.cpp)
        self.assertNotIn("delete g_console", self.cpp)

    def test_bridge_border_export_and_default_white_border(self):
        self.assertIn("DBaseQtSetBorderColor", self.cpp)
        self.assertIn("DBaseQtSetBorderColor", self.header)
        self.assertIn("DBaseQtSetBorderColor", self.def_file)
        self.assertIn("QColor g_console_border_color(255, 255, 255)", self.cpp)
        self.assertIn('" border: 3px solid %1;"', self.cpp)
        self.assertIn("QFrame#dbaseConsoleFrame", self.cpp)

    def test_pe32_pe64_link(self):
        d64 = load_d64()
        source = '''
SET COLOR TO "W/N"
SET BORDERCOLOR TO RGB(FF,FF,FF)
? "old"
CLEAR SCREEN
? "Stage16"
'''
        for target, magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(source, filename="stage16.dbase", target=target)
            program = (
                d64.assemble_pe32_source(result.assembly, filename="stage16_32.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="stage16_64.asm", gui=True)
            )
            pe = struct.unpack_from("<I", program.executable, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24)[0], magic)
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24 + 68)[0], 2)
            self.assertEqual(result.transcript, "Stage16\r\n")


if __name__ == "__main__":
    unittest.main()
