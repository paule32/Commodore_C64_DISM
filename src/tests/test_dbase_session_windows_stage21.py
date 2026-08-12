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
    DBaseNewObjectStatement,
    DBaseSessionLoginStatement,
    compile_dbase_to_assembly,
    parse_dbase_statements,
)


def load_d64():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_dbase_stage21_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseSessionWindowsStage21Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cpp = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
        cls.header = (ROOT / "d64qt5" / "d64qt5_bridge.h").read_text(encoding="utf-8")
        cls.def_file = (ROOT / "d64qt5" / "d64qt5_bridge.def").read_text(encoding="utf-8")
        cls.pro = (ROOT / "d64qt5" / "d64qt5_bridge.pro").read_text(encoding="utf-8")

    def test_session_creation_and_default_parent(self):
        statements = parse_dbase_statements("foo = new Session()\n")
        obj = next(s for s in statements if isinstance(s, DBaseNewObjectStatement))
        self.assertEqual(obj.class_name, "SESSION")
        self.assertEqual(obj.target.dotted, "foo")
        self.assertEqual(obj.owner.dotted, "_app")

    def test_nested_session_parent_is_object_predecessor(self):
        statements = parse_dbase_statements("form1.foo = new Session()\n")
        obj = next(s for s in statements if isinstance(s, DBaseNewObjectStatement))
        self.assertEqual(obj.target.dotted, "form1.foo")
        self.assertEqual(obj.owner.dotted, "form1")

    def test_app_session_parent_is_app(self):
        statements = parse_dbase_statements("_app.security = new SESSION()\n")
        obj = next(s for s in statements if isinstance(s, DBaseNewObjectStatement))
        self.assertEqual(obj.owner.dotted, "_app")

    def test_login_three_string_parameters_and_numeric_result(self):
        source = '''
foo = new Session()
result = foo.Login("user", "pass", "Users")
? result
'''
        statements = parse_dbase_statements(source, filename="session21.dbase")
        login = next(s for s in statements if isinstance(s, DBaseSessionLoginStatement))
        self.assertEqual(login.result_name, "result")
        self.assertEqual(login.target.dotted, "foo")
        result = compile_dbase_to_assembly(source, filename="session21.dbase", target="pe32")
        info = {v.name.casefold(): v for v in result.variables}["result"]
        self.assertEqual(info.value_type, "number")
        self.assertTrue(info.dynamic)
        self.assertIn("call DBaseQtSessionCreate", result.assembly)
        self.assertIn("call DBaseQtSessionLogin", result.assembly)

    def test_login_accepts_variables_and_functions(self):
        source = '''
function getGroup()
  return "Users"
foo = new Session()
u = "user"
p = "pass"
result = foo.Login(u, p, getGroup())
'''
        result = compile_dbase_to_assembly(source, filename="session_expr21.dbase", target="pe64")
        self.assertIn("call DBaseQtSessionLogin", result.assembly)

    def test_login_requires_three_parameters(self):
        source = 'foo = new Session()\nresult = foo.Login("u", "p")\n'
        with self.assertRaises(DBaseCompilerError) as cm:
            compile_dbase_to_assembly(source, filename="bad_session21.dbase")
        self.assertIn("genau drei Parameter", str(cm.exception))

    def test_login_requires_session_target(self):
        source = '''
_app.M = new MENU(_app)
result = _app.M.Login("u", "p", "Users")
'''
        with self.assertRaises(DBaseCompilerError) as cm:
            compile_dbase_to_assembly(source, filename="wrong_target21.dbase")
        self.assertIn("nicht als SESSION", str(cm.exception))

    def test_login_parameters_must_be_text(self):
        source = 'foo = new Session()\nresult = foo.Login(1, "p", "Users")\n'
        with self.assertRaises(DBaseCompilerError) as cm:
            compile_dbase_to_assembly(source, filename="bad_arg21.dbase")
        self.assertIn("Benutzername muss String/Char", str(cm.exception))

    def test_windows_authentication_runtime(self):
        self.assertIn("struct SessionNode", self.cpp)
        self.assertIn("DBaseQtSessionCreate", self.cpp)
        self.assertIn("DBaseQtSessionLogin", self.cpp)
        self.assertIn("LogonUserW(", self.cpp)
        self.assertIn("LOGON32_LOGON_NETWORK", self.cpp)
        self.assertIn("LOGON32_PROVIDER_DEFAULT", self.cpp)
        self.assertIn("LookupAccountNameW(", self.cpp)
        self.assertIn("CheckTokenMembership(", self.cpp)
        self.assertIn("SecureZeroMemory", self.cpp)
        self.assertIn("CloseHandle(token);", self.cpp)
        self.assertNotIn("QString password;", self.cpp)

    def test_runtime_exports_and_advapi32_link(self):
        for symbol in ("DBaseQtSessionCreate", "DBaseQtSessionLogin"):
            self.assertIn(symbol, self.header)
            self.assertIn(symbol, self.def_file)
        self.assertIn("-ladvapi32", self.pro)

    def test_pe32_pe64_internal_link(self):
        d64 = load_d64()
        source = '''
_app.security = new Session()
result = _app.security.Login("testuser", "testpass", "Users")
? result
'''
        for target, magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(
                source,
                filename="session21.dbase",
                target=target,
                windows_application_mode="GUI",
            )
            program = (
                d64.assemble_pe32_source(result.assembly, filename="session21_32.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="session21_64.asm", gui=True)
            )
            pe = struct.unpack_from("<I", program.executable, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24)[0], magic)
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24 + 68)[0], 2)


if __name__ == "__main__":
    unittest.main()
