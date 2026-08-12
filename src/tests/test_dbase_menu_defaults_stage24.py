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

from d64dbase import DBaseCompilerError, DBaseMenuFileStatement, compile_dbase_to_assembly, parse_dbase_statements

CPP = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
HDR = (ROOT / "d64qt5" / "d64qt5_bridge.h").read_text(encoding="utf-8")
DEF = (ROOT / "d64qt5" / "d64qt5_bridge.def").read_text(encoding="utf-8")


def load_d64():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_stage24_menu_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseMenuDefaultsStage24Tests(unittest.TestCase):
    def test_console_scrollbars_are_hidden(self):
        self.assertIn("g_console->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);", CPP)
        self.assertIn("g_console->setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff);", CPP)

    def test_reserved_trailing_blank_line_is_removed(self):
        self.assertNotIn("ensure_trailing_blank_line", CPP)
        self.assertIn("constexpr int DBASE_TEXT_COLUMNS = 80;", CPP)
        self.assertIn("constexpr int DBASE_TEXT_ROWS = 25;", CPP)

    def test_default_menu_has_requested_entries(self):
        for text in ('QStringLiteral("=")', 'QStringLiteral("Datei")',
                     'QStringLiteral("Neu")', 'QStringLiteral("Speichern")',
                     'QStringLiteral("Speichern unter...")',
                     'QStringLiteral("Alle Schließen")', 'QStringLiteral("Beenden")'):
            self.assertIn(text, CPP)
        self.assertIn("fileMenu->addSeparator();", CPP)
        self.assertIn("AsciiPopupMenu *fileMenu", CPP)
        self.assertIn("g_window->close();", CPP)
        self.assertIn("g_app->quit();", CPP)

    def test_default_menu_export_is_complete(self):
        self.assertIn("DBaseQtEnsureDefaultMenu", CPP)
        self.assertIn("DBaseQtEnsureDefaultMenu", HDR)
        self.assertIn("DBaseQtEnsureDefaultMenu", DEF)

    def test_no_menu_file_emits_default_before_show(self):
        asm = compile_dbase_to_assembly('? "ready"\n', filename="default24.dbase", target="pe32").assembly
        self.assertIn('import DBaseQtEnsureDefaultMenu, "d64qt5.dll", "DBaseQtEnsureDefaultMenu"', asm)
        self.assertIn("call DBaseQtEnsureDefaultMenu", asm)
        self.assertLess(asm.index("call DBaseQtEnsureDefaultMenu"), asm.index("call DBaseQtShowWindow"))

    def test_empty_menu_file_uses_default(self):
        asm = compile_dbase_to_assembly('_app.menuFile = ""\n? "ready"\n', filename="empty24.dbase", target="pe32").assembly
        self.assertIn("call DBaseQtEnsureDefaultMenu", asm)

    def test_string_menu_file_disables_default_and_includes_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "menu.mnu").write_text(
                '_app.M = new MENU(_app)\nwith (_app.M)\n text = "&Fenster"\nendwith\n',
                encoding="utf-8",
            )
            src = '_app.menuFile = "menu.mnu"\n? "ready"\n'
            statements = parse_dbase_statements(src, filename=str(root / "main.dbase"))
            menu_stmt = next(x for x in statements if isinstance(x, DBaseMenuFileStatement))
            self.assertEqual(menu_stmt.path, "menu.mnu")
            asm = compile_dbase_to_assembly(src, filename=str(root / "main.dbase"), target="pe32").assembly
            self.assertNotIn("call DBaseQtEnsureDefaultMenu", asm)
            self.assertIn("call DBaseQtMenuCreate", asm)

    def test_macro_variable_and_function_menu_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "menu.mnu").write_text(
                '_app.M = new MENU(_app)\nwith (_app.M)\n text = "Datei"\nendwith\n',
                encoding="utf-8",
            )
            sources = (
                '#define MF "menu.mnu"\n_app.menuFile = MF\n',
                'mf = "menu.mnu"\n_app.menuFile = mf\n',
                'function getMenu()\n return "menu.mnu"\n_app.menuFile = getMenu()\n',
                'function getMenu(prefix)\n return prefix + ".mnu"\n_app.menuFile = getMenu("menu")\n',
            )
            for index, src in enumerate(sources):
                with self.subTest(index=index):
                    statements = parse_dbase_statements(src, filename=str(root / f"main{index}.dbase"))
                    menu_stmt = next(x for x in statements if isinstance(x, DBaseMenuFileStatement))
                    self.assertEqual(menu_stmt.path, "menu.mnu")

    def test_old_angle_bracket_syntax_is_rejected(self):
        with self.assertRaises(DBaseCompilerError) as cm:
            parse_dbase_statements('_app.menuFile = <menu.mnu>\n', filename="old24.dbase")
        self.assertIn("nicht mehr unterstuetzt", str(cm.exception))

    def test_pe32_and_pe64_link_with_default_menu_export(self):
        d64 = load_d64()
        source = '? "ready"\n'
        for target, magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(source, filename=f"default_{target}.dbase", target=target)
            program = (
                d64.assemble_pe32_source(result.assembly, filename="default24_32.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="default24_64.asm", gui=True)
            )
            pe = struct.unpack_from("<I", program.executable, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24)[0], magic)
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24 + 68)[0], 2)


if __name__ == "__main__":
    unittest.main()
