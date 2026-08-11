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
    DBASE_SYSTEM_COLOR_NAMES,
    DBaseAppColorStatement,
    DBaseCompilerError,
    compile_dbase_to_assembly,
    parse_dbase_statements,
)


def load_d64():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_dbase_stage14_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseAppColorStage14Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cpp = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
        cls.header = (ROOT / "d64qt5" / "d64qt5_bridge.h").read_text(encoding="utf-8")
        cls.def_file = (ROOT / "d64qt5" / "d64qt5_bridge.def").read_text(encoding="utf-8")

    def test_all_requested_system_color_names_are_supported(self):
        expected = {
            "ActiveBorder", "ActiveCaption", "AppWorkspace", "Background",
            "BtnFace", "BtnHighlight", "BtnShadow", "BtnText", "CaptionText",
            "GrayText", "Highlight", "HighlightText", "InactiveBorder",
            "InactiveCaption", "InactiveCaptionText", "InfoText", "InfoBk",
            "Menu", "MenuText", "Scrollbar", "Window", "WindowFrame", "WindowText",
        }
        self.assertEqual(set(DBASE_SYSTEM_COLOR_NAMES), expected)
        for name in expected:
            self.assertIn(f'{{"{name}",', self.cpp)

    def test_active_border_maps_to_windows_active_border(self):
        self.assertIn('{"ActiveBorder",        COLOR_ACTIVEBORDER}', self.cpp)
        self.assertIn("GetSysColor(entry.index)", self.cpp)

    def test_quoted_colornormal_parse(self):
        for rhs in ('"ActiveBorder"', "'ActiveBorder'"):
            statements = parse_dbase_statements(
                f"_app.colorNormal = {rhs}\n? \"ok\"\n",
                filename="color14.dbase",
            )
            self.assertIsInstance(statements[0], DBaseAppColorStatement)
            self.assertEqual(statements[0].color_name, "ActiveBorder")

    def test_unquoted_system_name_requires_symbol(self):
        with self.assertRaises(DBaseCompilerError):
            compile_dbase_to_assembly(
                '_app.colorNormal = ActiveBorder\n',
                filename="unquoted14.dbase", target="pe32",
            )

    def test_this_is_alias_for_app_color_property(self):
        statements = parse_dbase_statements(
            'this.colorNormal = "Window"\n? "ok"\n', filename="thiscolor14.dbase"
        )
        self.assertIsInstance(statements[0], DBaseAppColorStatement)
        self.assertEqual(statements[0].color_name, "Window")

    def test_invalid_system_color_fails_compile(self):
        with self.assertRaises(DBaseCompilerError):
            compile_dbase_to_assembly(
                '_app.colorNormal = NotAWindowsColor\n? "bad"\n',
                filename="badcolor14.dbase",
                target="pe32",
            )

    def test_bridge_exports_color_setter(self):
        self.assertIn("DBaseQtSetColorNormal", self.cpp)
        self.assertIn("DBaseQtSetColorNormal", self.header)
        self.assertIn("DBaseQtSetColorNormal", self.def_file)
        self.assertIn("apply_console_background", self.cpp)
        self.assertIn("QPlainTextEdit#dbaseConsole", self.cpp)

    def test_codegen_pe32_pe64(self):
        source = '_app.colorNormal = "ActiveBorder"\n? "Farbe gesetzt"\n'
        for target in ("pe32", "pe64"):
            asm = compile_dbase_to_assembly(source, filename="color14.dbase", target=target).assembly
            self.assertIn('import DBaseQtSetColorNormal, "d64qt5.dll", "DBaseQtSetColorNormal"', asm)
            self.assertIn("call DBaseQtSetColorNormal", asm)

    def test_pe32_and_pe64_link_as_gui(self):
        d64 = load_d64()
        source = '_app.colorNormal = "ActiveBorder"\n? "Farbe gesetzt"\n'
        for target, magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(source, filename="color14.dbase", target=target)
            program = (
                d64.assemble_pe32_source(result.assembly, filename="color14_32.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="color14_64.asm", gui=True)
            )
            pe = struct.unpack_from("<I", program.executable, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24)[0], magic)
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24 + 68)[0], 2)


if __name__ == "__main__":
    unittest.main()
