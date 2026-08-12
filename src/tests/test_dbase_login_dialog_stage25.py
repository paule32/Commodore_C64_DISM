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

from d64dbase import DBaseCompilerError, compile_dbase_to_assembly

CPP = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
HDR = (ROOT / "d64qt5" / "d64qt5_bridge.h").read_text(encoding="utf-8")
DEF = (ROOT / "d64qt5" / "d64qt5_bridge.def").read_text(encoding="utf-8")


def load_d64():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_stage25_login_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseLoginDialogStage25Tests(unittest.TestCase):
    def test_default_file_menu_contains_login_and_exit(self):
        self.assertIn('fileMenu->addAction(QStringLiteral("Login"))', CPP)
        self.assertIn('fileMenu->addAction(QStringLiteral("Beenden"))', CPP)
        self.assertIn("connect_login_action(g_login_action);", CPP)
        self.assertIn("connect_quit_action(g_quit_action);", CPP)

    def test_new_session_opens_login_dialog(self):
        self.assertIn("show_login_dialog(session);", CPP)
        self.assertIn("class LoginDialog final : public QDialog", CPP)
        self.assertIn("QEventLoop waitLoop;", CPP)
        self.assertIn("setModal(false);", CPP)

    def test_login_dialog_has_requested_controls(self):
        for text in (
            'QStringLiteral("Benutzer")',
            'QStringLiteral("Passwort")',
            'QStringLiteral("Gruppe")',
            'QStringLiteral("Login")',
            'QStringLiteral("Abbrechen")',
        ):
            self.assertIn(text, CPP)
        self.assertIn("m_passwordEdit->setEchoMode(QLineEdit::Password);", CPP)
        self.assertIn("QGridLayout", CPP)

    def test_dialog_colors_fonts_and_custom_ascii_border(self):
        self.assertIn("background-color: #909090", CPP)
        self.assertIn("background-color: #008000", CPP)
        self.assertIn("color: #ffffff", CPP)
        self.assertIn("choose_menu_font_family()", CPP)
        self.assertIn("choose_popup_border_font_family()", CPP)
        for codepoint in ("0x2554", "0x2557", "0x255A", "0x255D", "0x2550", "0x2551"):
            self.assertIn(codepoint, CPP)
        self.assertIn("m_moving ? QColor(255, 216, 0) : QColor(255, 255, 255)", CPP)

    def test_dialog_moves_in_character_cells_and_clamps_to_console(self):
        self.assertIn("delta.x()) / qMax(1, m_cellWidth)", CPP)
        self.assertIn("delta.y()) / qMax(1, m_cellHeight)", CPP)
        self.assertIn("g_console->viewport()->mapToGlobal(QPoint(0, 0))", CPP)
        self.assertIn("g_console->viewport()->height()", CPP)
        self.assertIn("updateViewportClipMask()", CPP)
        self.assertIn("DBASE_LOGIN_DIALOG_COLUMNS", CPP)
        self.assertIn("DBASE_LOGIN_DIALOG_ROWS", CPP)

    def test_zoom_updates_open_login_dialog(self):
        self.assertIn("g_login_dialog->updateForGrid(true);", CPP)
        self.assertIn("change_font_size(+1);", CPP)
        self.assertIn("change_font_size(-1);", CPP)

    def test_cancel_sets_loginsession_false_and_success_true(self):
        self.assertIn("set_login_session_state(false);", CPP)
        self.assertIn("set_login_session_state(true);", CPP)
        self.assertIn("DBaseQtGetLoginSession", CPP)
        self.assertIn("DBaseQtGetLoginSession", HDR)
        self.assertIn("DBaseQtGetLoginSession", DEF)

    def test_menu_access_is_locked_until_login(self):
        self.assertIn("update_menu_access_state()", CPP)
        self.assertIn("action == g_login_action || action == g_quit_action", CPP)
        self.assertIn("menu == g_security_file_menu", CPP)
        self.assertIn("dbaseSecuritySavedEnabled", CPP)

    def test_loginsession_is_runtime_read_only_global(self):
        src = '''
_app.security = new Session()
? LOGINSESSION
IF LOGINSESSION == 1
    ? "login ok"
ENDIF
'''
        for target in ("pe32", "pe64"):
            result = compile_dbase_to_assembly(src, filename=f"login25_{target}.dbase", target=target)
            self.assertIn('import DBaseQtGetLoginSession, "d64qt5.dll", "DBaseQtGetLoginSession"', result.assembly)
            self.assertGreaterEqual(result.assembly.count("call DBaseQtGetLoginSession"), 2)
        with self.assertRaises(DBaseCompilerError) as cm:
            compile_dbase_to_assembly("LOGINSESSION = 1\n", filename="readonly25.dbase")
        self.assertIn("schreibgeschuetzt", str(cm.exception))

    def test_pe32_pe64_link_with_new_runtime_import(self):
        d64 = load_d64()
        source = '_app.security = new Session()\n? LOGINSESSION\n'
        for target, magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(source, filename=f"login25_{target}.dbase", target=target)
            program = (
                d64.assemble_pe32_source(result.assembly, filename="login25_32.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="login25_64.asm", gui=True)
            )
            pe = struct.unpack_from("<I", program.executable, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24)[0], magic)
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24 + 68)[0], 2)


if __name__ == "__main__":
    unittest.main()
