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
    DBaseLocalObjectDeclaration,
    DBaseNewObjectStatement,
    DBaseObjectMethodStatement,
    DBaseObjectPropertyStatement,
    compile_dbase_to_assembly,
    parse_dbase_statements,
)

CPP = (ROOT / "d64qt5" / "d64qt5_bridge.cpp").read_text(encoding="utf-8")
HDR = (ROOT / "d64qt5" / "d64qt5_bridge.h").read_text(encoding="utf-8")
DEF = (ROOT / "d64qt5" / "d64qt5_bridge.def").read_text(encoding="utf-8")
PRO = (ROOT / "d64qt5" / "d64qt5_bridge.pro").read_text(encoding="utf-8")
GRAMMAR = (ROOT / "d64dbase" / "grammar" / "DBaseParser.g4").read_text(encoding="utf-8")
LEXER = (ROOT / "d64dbase" / "grammar" / "DBaseLexer.g4").read_text(encoding="utf-8")


def load_d64():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_stage30_database_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseDatabaseStage30Tests(unittest.TestCase):
    def test_local_database_alias_and_creation(self):
        statements = parse_dbase_statements(
            "local db as Database\ndb = new Database()\n",
            filename="database30.dbase",
        )
        decl = next(s for s in statements if isinstance(s, DBaseLocalObjectDeclaration))
        obj = next(s for s in statements if isinstance(s, DBaseNewObjectStatement))
        self.assertEqual(decl.name, "db")
        self.assertEqual(decl.class_name, "DATABASE")
        self.assertEqual(obj.target.dotted, "db")
        self.assertEqual(obj.owner.dotted, "_app")
        self.assertEqual(obj.class_name, "DATABASE")

    def test_database_properties_and_methods_parse(self):
        source = '''
_app.security = new Session()
local db as Database
db = new Database()
db.session = _app.security
db.path = "C:\\Data"
db.databaseName = "Kunden"
db.userName = "user"
db.password = "secret"
db.alias = "MY_DSN"
db.active = true
db.commit()
db.close()
'''
        statements = parse_dbase_statements(source, filename="database_props30.dbase")
        props = [s for s in statements if isinstance(s, DBaseObjectPropertyStatement)]
        methods = [s for s in statements if isinstance(s, DBaseObjectMethodStatement)]
        self.assertEqual(
            [p.property_name.casefold() for p in props],
            ["session", "path", "databasename", "username", "password", "alias", "active"],
        )
        self.assertEqual([m.method_name.casefold() for m in methods], ["commit", "close"])

    def test_database_string_properties_accept_variables_functions_and_macros(self):
        source = '''
#define ROOT "C:\\Data"
function dbName()
    return "Kunden"
_app.security = new Session()
local db as Database
db = new Database()
db.session = _app.security
p = ROOT
db.path = p
db.databaseName = dbName()
db.userName = ""
db.password = ""
db.alias = ""
db.open()
'''
        result = compile_dbase_to_assembly(source, filename="database_expr30.dbase", target="pe64")
        self.assertIn("call DBaseQtDatabaseSetPath", result.assembly)
        self.assertIn("call DBaseQtDatabaseSetDatabaseName", result.assembly)
        self.assertIn("call DBaseQtDatabaseOpen", result.assembly)

    def test_database_session_must_be_session_object(self):
        source = '''
_app.m = new MENU(_app)
local db as Database
db = new Database()
db.session = _app.m
'''
        with self.assertRaises(DBaseCompilerError) as cm:
            compile_dbase_to_assembly(source, filename="database_bad_session30.dbase")
        self.assertIn("nicht als SESSION", str(cm.exception))

    def test_active_accepts_boolean_or_zero_one_only(self):
        base = 'local db as Database\ndb = new Database()\n'
        compile_dbase_to_assembly(base + "db.active = true\n", filename="active_true30.dbase")
        compile_dbase_to_assembly(base + "db.active = false\n", filename="active_false30.dbase")
        compile_dbase_to_assembly(base + "db.active = 1\n", filename="active_one30.dbase")
        with self.assertRaises(DBaseCompilerError) as cm:
            compile_dbase_to_assembly(base + "db.active = 2\n", filename="active_bad30.dbase")
        self.assertIn("TRUE/FALSE oder 0/1", str(cm.exception))

    def test_database_codegen_contains_lifecycle_and_properties(self):
        source = '''
_app.security = new Session()
local db as Database
db = new Database()
db.session = _app.security
db.path = "."
db.databaseName = "TEST"
db.userName = "u"
db.password = "p"
db.alias = ""
db.open()
db.commit()
db.active = false
'''
        for target in ("pe32", "pe64"):
            result = compile_dbase_to_assembly(source, filename=f"database30_{target}.dbase", target=target)
            for symbol in (
                "DBaseQtDatabaseCreate",
                "DBaseQtDatabaseSetPath",
                "DBaseQtDatabaseSetDatabaseName",
                "DBaseQtDatabaseSetUserName",
                "DBaseQtDatabaseSetPassword",
                "DBaseQtDatabaseSetAlias",
                "DBaseQtDatabaseSetSession",
                "DBaseQtDatabaseSetActive",
                "DBaseQtDatabaseOpen",
                "DBaseQtDatabaseCommit",
            ):
                self.assertIn(f"call {symbol}", result.assembly)

    def test_runtime_requires_authenticated_session_and_closes_on_logout(self):
        self.assertIn("struct DatabaseNode", CPP)
        self.assertIn("database->session->authenticated", CPP)
        self.assertIn("keine legitimierte SESSION", CPP)
        self.assertIn("database_close_internal(database);", CPP)
        self.assertIn("close_database_tables(database);", CPP)
        self.assertIn("database->active = false;", CPP)
        self.assertIn("for (DatabaseNode *database : g_database_nodes)", CPP)

    def test_local_directory_and_odbc_alias_backends(self):
        self.assertIn("QDir directory(requestedPath);", CPP)
        self.assertIn("SQLDriverConnectW(", CPP)
        self.assertIn("SQL_ATTR_AUTOCOMMIT", CPP)
        self.assertIn("SQLEndTran(SQL_HANDLE_DBC, database->odbcDbc, SQL_COMMIT)", CPP)
        self.assertIn("-lodbc32", PRO)

    def test_warning_dialog_is_custom_nonmodal_grid_dialog(self):
        self.assertIn("class WarningDialog final : public QDialog", CPP)
        self.assertIn('setWindowTitle(QStringLiteral("Warnung"));', CPP)
        self.assertIn("setWindowModality(Qt::NonModal);", CPP)
        self.assertIn("setModal(false);", CPP)
        self.assertIn('QStringLiteral("OK")', CPP)
        self.assertIn("background-color: #ff0000", CPP)
        self.assertIn("color: #000000", CPP)
        self.assertIn("QColor(255, 255, 255)", CPP)
        self.assertIn("DBASE_WARNING_DIALOG_COLUMNS", CPP)
        self.assertIn("DBASE_WARNING_DIALOG_ROWS", CPP)
        self.assertIn("g_console->viewport()->mapToGlobal(QPoint(0, 0))", CPP)

    def test_warning_dialog_is_shutdown_safe(self):
        self.assertIn("if (g_warning_dialog)", CPP)
        self.assertIn("g_warning_dialog->reject();", CPP)
        self.assertIn("g_warning_dialog = nullptr;", CPP)

    def test_database_exports_and_grammar(self):
        symbols = (
            "DBaseQtDatabaseCreate",
            "DBaseQtDatabaseSetPath",
            "DBaseQtDatabaseSetDatabaseName",
            "DBaseQtDatabaseSetUserName",
            "DBaseQtDatabaseSetPassword",
            "DBaseQtDatabaseSetAlias",
            "DBaseQtDatabaseSetSession",
            "DBaseQtDatabaseSetActive",
            "DBaseQtDatabaseOpen",
            "DBaseQtDatabaseClose",
            "DBaseQtDatabaseCommit",
        )
        for symbol in symbols:
            self.assertIn(symbol, HDR)
            self.assertIn(symbol, DEF)
        self.assertIn("databaseLocalDeclaration", GRAMMAR)
        self.assertIn("databaseObjectStatement", GRAMMAR)
        self.assertIn("databasePropertyStatement", GRAMMAR)
        self.assertIn("databaseMethodStatement", GRAMMAR)
        for token in ("DATABASE", "LOCAL", "DATABASENAME", "ACTIVE", "ALIAS", "COMMIT"):
            self.assertIn(token, LEXER)

    def test_pe32_pe64_internal_link(self):
        d64 = load_d64()
        source = '''
_app.security = new Session()
local db as Database
db = new Database()
db.session = _app.security
db.path = "."
db.databaseName = "TEST"
db.open()
db.commit()
db.close()
'''
        for target, magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(
                source,
                filename=f"database30_{target}.dbase",
                target=target,
                windows_application_mode="GUI",
            )
            program = (
                d64.assemble_pe32_source(result.assembly, filename="database30_32.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="database30_64.asm", gui=True)
            )
            pe = struct.unpack_from("<I", program.executable, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24)[0], magic)
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24 + 68)[0], 2)


if __name__ == "__main__":
    unittest.main()
