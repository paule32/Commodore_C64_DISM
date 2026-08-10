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
    DBaseBinaryExpression,
    DBaseCallExpression,
    DBaseCompilerError,
    DBaseIdentifierExpression,
    compile_dbase_to_assembly,
    parse_dbase_statements,
)


def load_d64_dism():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_dism_dbase_expr_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("d64_dism.py konnte nicht geladen werden")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBasePrintExpressionTests(unittest.TestCase):
    def test_question_appends_crlf(self):
        result = compile_dbase_to_assembly('? "Text"\n')
        self.assertEqual(result.transcript, "Text\r\n")

    def test_double_question_does_not_append_newline(self):
        result = compile_dbase_to_assembly('?? "Text"\n?? " danach"\n')
        self.assertEqual(result.transcript, "Text danach")

    def test_question_and_double_question_chain_exactly(self):
        source = '?? "Summe: "\n? 1 + 2 + 3\n?? "Ende"\n'
        result = compile_dbase_to_assembly(source)
        self.assertEqual(result.transcript, "Summe: 6\r\nEnde")

    def test_arithmetic_precedence_and_parentheses(self):
        result = compile_dbase_to_assembly(
            '? 1 + 2 * 3\n? (1 + 2) * 3\n? 10 / 4\n'
        )
        self.assertEqual(result.transcript, "7\r\n9\r\n2.5\r\n")

    def test_unary_operators(self):
        result = compile_dbase_to_assembly('? -2 + +5\n')
        self.assertEqual(result.transcript, "3\r\n")

    def test_string_literals_support_both_delimiters(self):
        source = '? "Text"\n? \' text\'\n? "Text \' text \' "\n'
        result = compile_dbase_to_assembly(source)
        self.assertEqual(result.transcript, "Text\r\n text\r\nText ' text ' \r\n")

    def test_string_concatenation(self):
        result = compile_dbase_to_assembly('? "a" + \'b\' + "c"\n')
        self.assertEqual(result.transcript, "abc\r\n")

    def test_doubled_delimiter_inside_string(self):
        result = compile_dbase_to_assembly('? "Text ""Zitat"""\n? \'it\'\'s\'\n')
        self.assertEqual(result.transcript, 'Text "Zitat"\r\nit\'s\r\n')

    def test_comments_may_split_expression(self):
        source = '? 2 /* erster\nzweiter */ + 3 // Rest\n'
        result = compile_dbase_to_assembly(source)
        self.assertEqual(result.transcript, "5\r\n")

    def test_line_comment_ends_logical_statement(self):
        source = '? 1 + 2 && Kommentar\n? 4 + 5\n'
        result = compile_dbase_to_assembly(source)
        self.assertEqual(result.transcript, "3\r\n9\r\n")

    def test_division_by_zero_has_operator_position(self):
        with self.assertRaises(DBaseCompilerError) as ctx:
            compile_dbase_to_assembly('? 4 / 0\n', filename='zero.dbp')
        self.assertEqual(ctx.exception.line, 1)
        self.assertEqual(ctx.exception.column, 5)
        self.assertIn("Division durch 0", str(ctx.exception))

    def test_mixed_string_number_addition_converts_number_to_text(self):
        result = compile_dbase_to_assembly('? 2 + "Text"\n', filename='type.dbp')
        self.assertEqual(result.transcript, "2Text\r\n")

    def test_variable_is_parsed_for_future_stage(self):
        statements = parse_dbase_statements('? 2 + variable + 3\n')
        root = statements[0].expression
        self.assertIsInstance(root, DBaseBinaryExpression)
        self.assertIsInstance(root.left, DBaseBinaryExpression)
        self.assertIsInstance(root.left.right, DBaseIdentifierExpression)
        with self.assertRaises(DBaseCompilerError) as ctx:
            compile_dbase_to_assembly('? 2 + variable + 3\n', filename='var.dbp')
        self.assertIn("Variable 'variable'", str(ctx.exception))

    def test_function_call_is_emitted_as_external_runtime_value(self):
        statements = parse_dbase_statements('? test() + "text"\n')
        root = statements[0].expression
        self.assertIsInstance(root, DBaseBinaryExpression)
        self.assertIsInstance(root.left, DBaseCallExpression)
        result = compile_dbase_to_assembly('? test() + "text"\n', filename='func.dbp')
        self.assertIn("extern test", result.assembly)
        self.assertIn("call test", result.assembly)
        self.assertEqual(result.external_functions, ("test",))

    def test_missing_expression_is_error(self):
        with self.assertRaises(DBaseCompilerError):
            compile_dbase_to_assembly('? // nichts\n')
        with self.assertRaises(DBaseCompilerError):
            compile_dbase_to_assembly('?? ** nichts\n')

    def test_pe32_and_pe32plus_assembly_links(self):
        d64 = load_d64_dism()
        source = '?? "Wert="\n? 1 + 2 * 3\n? "Text" + "!"\n'
        for target, expected_magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(source, target=target)
            self.assertIn("DBaseQtAppendConsole", result.assembly)
            program = (
                d64.assemble_pe32_source(result.assembly, filename="dbase_expr32.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="dbase_expr64.asm", gui=True)
            )
            self.assertTrue(program.executable.startswith(b"MZ"))
            pe_offset = struct.unpack_from("<I", program.executable, 0x3C)[0]
            optional = pe_offset + 24
            self.assertEqual(struct.unpack_from("<H", program.executable, optional)[0], expected_magic)
            self.assertEqual(struct.unpack_from("<H", program.executable, optional + 68)[0], 2)

    def test_gui_subsystem_still_links_but_question_output_is_console(self):
        d64 = load_d64_dism()
        for target in ("pe32", "pe64"):
            result = compile_dbase_to_assembly(
                '? "GUI dBase ? schreibt trotzdem auf die Konsole"\n',
                target=target,
                windows_application_mode="GUI",
            )
            self.assertNotIn("AllocConsole", result.assembly)
            self.assertIn("DBaseQtAppendConsole", result.assembly)
            program = (
                d64.assemble_pe32_source(result.assembly, filename="dbase_expr32g.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="dbase_expr64g.asm", gui=True)
            )
            pe_offset = struct.unpack_from("<I", program.executable, 0x3C)[0]
            optional = pe_offset + 24
            self.assertEqual(struct.unpack_from("<H", program.executable, optional + 68)[0], 2)


if __name__ == "__main__":
    unittest.main()
