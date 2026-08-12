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
    DBaseClearScreenStatement,
    DBaseCompilerError,
    compile_dbase_to_assembly,
    parse_dbase_statements,
)


def load_d64():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_dbase_stage23_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseClearScreenExpressionStage23Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cpp = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
        cls.header = (ROOT / "d64qt5" / "d64qt5_bridge.h").read_text(encoding="utf-8")
        cls.def_file = (ROOT / "d64qt5" / "d64qt5_bridge.def").read_text(encoding="utf-8")

    def test_clear_screen_plain_stays_compatible(self):
        statements = parse_dbase_statements("CLEAR SCREEN\n", filename="plain23.dbase")
        clear = statements[0]
        self.assertIsInstance(clear, DBaseClearScreenStatement)
        self.assertIsNone(clear.expression)
        asm = compile_dbase_to_assembly("CLEAR SCREEN\n", target="pe32").assembly
        self.assertIn("call DBaseQtClearScreen", asm)

    def test_numeric_literal_uses_character_fill(self):
        result = compile_dbase_to_assembly(
            'SET COLOR TO "B/RG+"\nCLEAR SCREEN 0xB0\n',
            filename="char23.dbase",
            target="pe32",
            windows_application_mode="GUI",
        )
        self.assertIn('import DBaseQtClearScreenChar, "d64qt5.dll", "DBaseQtClearScreenChar"', result.assembly)
        self.assertIn("call DBaseQtClearScreenChar", result.assembly)
        self.assertNotIn("call DBaseQtClearScreenColor", result.assembly.split("call DBaseQtClearScreenChar", 1)[0])

    def test_numeric_macro_variable_and_function(self):
        source = '''
#define SHADE 0xB0
function getShade()
    return 0xB0
x = 0xB0
CLEAR SCREEN SHADE
CLEAR SCREEN x
CLEAR SCREEN getShade()
'''
        result = compile_dbase_to_assembly(source, filename="symbols23.dbase", target="pe64")
        self.assertEqual(result.assembly.count("call DBaseQtClearScreenChar"), 3)

    def test_rgb_and_hex_string_use_color_clear(self):
        source = '''
CLEAR SCREEN RGB(255,0,0)
CLEAR SCREEN "#001C46"
'''
        result = compile_dbase_to_assembly(source, filename="colors23.dbase", target="pe32")
        self.assertEqual(result.assembly.count("call DBaseQtClearScreenColor"), 2)
        self.assertIn("db 35, 70, 70, 48, 48, 48, 48", result.assembly)
        self.assertIn("db 35, 48, 48, 49, 67, 52, 54", result.assembly)

    def test_color_variable_and_function(self):
        source = '''
function getBackground()
    return "#000080"
c = "#FF0000"
CLEAR SCREEN c
CLEAR SCREEN getBackground()
'''
        result = compile_dbase_to_assembly(source, filename="color_symbols23.dbase", target="pe64")
        self.assertEqual(result.assembly.count("call DBaseQtClearScreenColor"), 2)

    def test_invalid_constant_character_code_rejected(self):
        for value in ("-1", "256", "12.5"):
            with self.subTest(value=value):
                with self.assertRaises(DBaseCompilerError):
                    compile_dbase_to_assembly(f"CLEAR SCREEN {value}\n", target="pe32")

    def test_invalid_constant_color_rejected(self):
        for value in ('"red"', '"#FFF"', '"#GG0000"'):
            with self.subTest(value=value):
                with self.assertRaises(DBaseCompilerError):
                    compile_dbase_to_assembly(f"CLEAR SCREEN {value}\n", target="pe32")

    def test_bridge_exports_and_cp437_b0(self):
        for symbol in ("DBaseQtClearScreenChar", "DBaseQtClearScreenColor"):
            self.assertIn(symbol, self.cpp)
            self.assertIn(symbol, self.header)
            self.assertIn(symbol, self.def_file)
        self.assertIn("0x2591", self.cpp)
        self.assertIn("const QString row(DBASE_TEXT_COLUMNS, glyph)", self.cpp)
        self.assertIn("for (int y = 0; y < DBASE_TEXT_ROWS; ++y)", self.cpp)

    def test_bridge_pattern_uses_set_color_foreground_background(self):
        self.assertIn("format.setForeground(g_output_foreground)", self.cpp)
        self.assertIn("format.setBackground(g_output_background)", self.cpp)
        self.assertIn("g_console_background = g_output_background", self.cpp)

    def test_bridge_color_clear_accepts_rgb_literal(self):
        self.assertIn("rgb_literal_color(requested, &color)", self.cpp)
        self.assertIn("g_console_background = color", self.cpp)

    def test_pe32_pe64_internal_link(self):
        d64 = load_d64()
        source = '''
SET COLOR TO "B/RG+"
CLEAR SCREEN 0xB0
CLEAR SCREEN RGB(255,0,0)
CLEAR SCREEN "#000080"
'''
        for target, magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(
                source,
                filename="stage23.dbase",
                target=target,
                windows_application_mode="GUI",
            )
            program = (
                d64.assemble_pe32_source(result.assembly, filename="stage23_32.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="stage23_64.asm", gui=True)
            )
            pe = struct.unpack_from("<I", program.executable, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24)[0], magic)
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24 + 68)[0], 2)


if __name__ == "__main__":
    unittest.main()
