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
    DBaseSetColorStatement,
    compile_dbase_to_assembly,
    parse_dbase_statements,
)


def load_d64():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_dbase_stage15_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseColorRgbStage15Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cpp = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
        cls.header = (ROOT / "d64qt5" / "d64qt5_bridge.h").read_text(encoding="utf-8")
        cls.def_file = (ROOT / "d64qt5" / "d64qt5_bridge.def").read_text(encoding="utf-8")

    def test_unquoted_name_and_undefined_call_fail(self):
        for rhs in ("ActiveBorder", "ActiveBorder()"):
            with self.assertRaises(DBaseCompilerError):
                compile_dbase_to_assembly(
                    f"_app.colorNormal = {rhs}\n", filename="bad15.dbase", target="pe32"
                )

    def test_function_must_be_defined_before_color_property(self):
        source = """
_app.colorNormal = getColor()
function getColor()
    return "Window"
"""
        with self.assertRaises(DBaseCompilerError):
            compile_dbase_to_assembly(source, filename="latefunc15.dbase", target="pe32")

    def test_variable_function_and_macro_are_allowed(self):
        source = '''
#define MACRO_COLOR "Window"
function getColor()
    return "ActiveBorder"
C = "Menu"
_app.colorNormal = C
_app.colorNormal = getColor()
_app.colorNormal = MACRO_COLOR
? "ok"
'''
        result = compile_dbase_to_assembly(source, filename="symbols15.dbase", target="pe32")
        self.assertEqual(result.transcript, "ok\r\n")
        self.assertEqual(result.assembly.count("call DBaseQtSetColorNormal"), 3)

    def test_rgb_two_digit_hex_and_standard_hex_forms(self):
        for expression, expected in (
            ("RGB(FF,00,80)", "#FF0080"),
            ("RGB(0xFF,$00,080h)", "#FF0080"),
        ):
            result = compile_dbase_to_assembly(
                f"_app.colorNormal = {expression}\n? {expression}\n",
                filename="rgb15.dbase", target="pe32",
            )
            self.assertIn(expected, result.transcript)
            self.assertIn(expected.encode("utf-8").hex()[:4] if False else "DBaseQtSetColorNormal", result.assembly)

    def test_rgb_can_flow_through_variable(self):
        source = '''
C = RGB(12,34,56)
_app.colorNormal = C
? C
'''
        result = compile_dbase_to_assembly(source, filename="rgbvar15.dbase", target="pe32")
        # Zwei Hexdigits werden als Hex gelesen: 12/34/56 -> #123456.
        self.assertEqual(result.transcript, "#123456\r\n")

    def test_rgb_range_and_arity_errors(self):
        for expression in ("RGB(0x100,0,0)", "RGB(1,2)"):
            with self.assertRaises(DBaseCompilerError):
                compile_dbase_to_assembly(
                    f"_app.colorNormal = {expression}\n", filename="rgb_bad15.dbase", target="pe32"
                )

    def test_set_color_to_background_foreground(self):
        statements = parse_dbase_statements(
            'SET COLOR TO "W/N"\n? "Text"\n', filename="setcolor15.dbase"
        )
        self.assertIsInstance(statements[0], DBaseSetColorStatement)
        self.assertEqual(statements[0].spec, "W/N")
        result = compile_dbase_to_assembly(
            'SET COLOR TO "W/N"\n? "Text"\n', filename="setcolor15.dbase", target="pe32"
        )
        self.assertIn('import DBaseQtSetOutputColor, "d64qt5.dll", "DBaseQtSetOutputColor"', result.assembly)
        self.assertIn("call DBaseQtSetOutputColor", result.assembly)

    def test_invalid_set_color_codes_fail(self):
        for spec in ("W+/N", "W/N*", "X/N", "W"):
            with self.assertRaises(DBaseCompilerError):
                compile_dbase_to_assembly(
                    f'SET COLOR TO "{spec}"\n', filename="badset15.dbase", target="pe32"
                )

    def test_bridge_has_output_palette_and_rich_insert(self):
        self.assertIn("DBaseQtSetOutputColor", self.cpp)
        self.assertIn("DBaseQtSetOutputColor", self.header)
        self.assertIn("DBaseQtSetOutputColor", self.def_file)
        self.assertIn("QTextCharFormat format", self.cpp)
        self.assertIn("format.setForeground(g_output_foreground)", self.cpp)
        self.assertIn("format.setBackground(g_output_background)", self.cpp)
        self.assertIn("W/N = hellgrauer Hintergrund, schwarze Schrift", self.cpp)

    def test_color_normal_bridge_accepts_rgb_literal(self):
        self.assertIn("rgb_literal_color", self.cpp)
        self.assertIn('QStringLiteral("^#[0-9A-Fa-f]{6}$")', self.cpp)

    def test_pe32_pe64_link(self):
        d64 = load_d64()
        source = '''
C = RGB(FF,00,80)
_app.colorNormal = C
SET COLOR TO "W/N"
? "Stage15"
'''
        for target, magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(source, filename="stage15.dbase", target=target)
            program = (
                d64.assemble_pe32_source(result.assembly, filename="stage15_32.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="stage15_64.asm", gui=True)
            )
            pe = struct.unpack_from("<I", program.executable, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24)[0], magic)
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24 + 68)[0], 2)


if __name__ == "__main__":
    unittest.main()
