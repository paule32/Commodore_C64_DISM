from __future__ import annotations

import importlib.util
import struct
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from d64dbase import (
    DBaseCompilerError,
    DBaseMenuFileStatement,
    DBaseNewObjectStatement,
    DBaseWithStatement,
    compile_dbase_to_assembly,
    parse_dbase_statements,
)


def load_d64():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_dbase_stage13_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


MENU_SOURCE = r'''
_app.MFENSTER = new MENU(_app)
with (_app.MFENSTER)
    text = "&Fenster"
endwith

_app.MFENSTER.MCASCADE = new MENU(_app.MFENSTER)
with (_app.MFENSTER.MCASCADE)
    onClick = class::MCASCADE_ONCLICK
    text = "Ü&berlappend"
    shortCut = "Ctrl+F4"
endwith

_app.MFENSTER.MSEP = new MENU(_app.MFENSTER)
with (_app.MFENSTER.MSEP)
    text = ""
    separator = true
endwith

procedure MCASCADE_ONCLICK()
    ? "clicked"
    return

? "ready"
'''


class DBaseMenuClassStage13Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cpp = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
        cls.header = (ROOT / "d64qt5" / "d64qt5_bridge.h").read_text(encoding="utf-8")

    def test_menu_bar_is_first_console_row(self):
        self.assertIn("new QMenuBar(g_console_frame)", self.cpp)
        menu_pos = self.cpp.index("console_layout->addWidget(g_menu_bar, 0)")
        editor_pos = self.cpp.index("console_layout->addWidget(g_console, 1)")
        self.assertLess(menu_pos, editor_pos)
        self.assertIn("background-color: #909090", self.cpp)
        self.assertIn("color: #000000", self.cpp)
        self.assertIn('QStringLiteral("Consolas")', self.cpp)
        self.assertIn('QStringLiteral("Courier New")', self.cpp)

    def test_bridge_exports_menu_c_abi(self):
        for symbol in (
            "DBaseQtMenuCreate", "DBaseQtMenuSetText", "DBaseQtMenuSetSeparator",
            "DBaseQtMenuSetShortcut", "DBaseQtMenuSetOnClick",
        ):
            self.assertIn(symbol, self.cpp)
            self.assertIn(symbol, self.header)

    def test_app_new_menu_with_and_callback_parse(self):
        statements = parse_dbase_statements(MENU_SOURCE, filename="menu13.dbase")
        self.assertTrue(any(isinstance(x, DBaseNewObjectStatement) for x in statements))
        self.assertTrue(any(isinstance(x, DBaseWithStatement) for x in statements))
        with_stmt = next(x for x in statements if isinstance(x, DBaseWithStatement) and x.target.dotted.endswith("MCASCADE"))
        props = {p.name.casefold(): p for p in with_stmt.properties}
        self.assertEqual(props["onclick"].value, "MCASCADE_ONCLICK")
        self.assertEqual(props["text"].value, "Ü&berlappend")

    def test_codegen_emits_real_menu_calls_pe32_pe64(self):
        for target in ("pe32", "pe64"):
            asm = compile_dbase_to_assembly(MENU_SOURCE, filename="menu13.dbase", target=target).assembly
            for symbol in (
                "DBaseQtMenuCreate", "DBaseQtMenuSetText", "DBaseQtMenuSetSeparator",
                "DBaseQtMenuSetShortcut", "DBaseQtMenuSetOnClick",
            ):
                self.assertIn(f'import {symbol}, "d64qt5.dll", "{symbol}"', asm)
                self.assertIn(f"call {symbol}", asm)
            self.assertIn("__dbase_procedure_mcascade_onclick__void", asm)

    def test_this_is_alias_for_app(self):
        source = r'''
_app.MFENSTER = new MENU(_app)
this.MFENSTER.MCLOSE = new MENU(this.MFENSTER)
with (_app.MFENSTER.MCLOSE)
    text = "Close"
endwith
'''
        asm = compile_dbase_to_assembly(source, filename="this13.dbase", target="pe32").assembly
        self.assertIn("__dbase_object_app_mfenster", asm)
        self.assertIn("__dbase_object_app_mfenster_mclose", asm)

    def test_menu_file_is_included_relative_to_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            menu = root / "window.mnu"
            menu.write_text(
                '_app.MFENSTER = new MENU(_app)\n'
                'with (_app.MFENSTER)\n'
                '  text = "&Fenster"\n'
                'endwith\n',
                encoding="utf-8",
            )
            main = root / "main.dbase"
            main.write_text('_app.menuFile = "window.mnu"\n? "ready"\n', encoding="utf-8")
            statements = parse_dbase_statements(main.read_text(), filename=str(main))
            self.assertIsInstance(statements[0], DBaseMenuFileStatement)
            self.assertTrue(any(isinstance(x, DBaseNewObjectStatement) for x in statements))
            asm = compile_dbase_to_assembly(main.read_text(), filename=str(main), target="pe32").assembly
            self.assertIn("call DBaseQtMenuCreate", asm)

    def test_callback_must_be_parameterless_procedure(self):
        source = r'''
_app.M = new MENU(_app)
with (_app.M)
  onClick = class::bad
endwith
procedure bad(x)
  return
'''
        with self.assertRaises(DBaseCompilerError):
            compile_dbase_to_assembly(source, filename="bad13.dbase")

    def test_pe32_and_pe64_link_as_gui(self):
        d64 = load_d64()
        for target, magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(MENU_SOURCE, filename="menu13.dbase", target=target)
            program = (
                d64.assemble_pe32_source(result.assembly, filename="menu13_32.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="menu13_64.asm", gui=True)
            )
            pe = struct.unpack_from("<I", program.executable, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24)[0], magic)
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24 + 68)[0], 2)


if __name__ == "__main__":
    unittest.main()
