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
    DBaseCallStatement,
    DBaseCompilerError,
    DBaseRoutineDefinition,
    compile_dbase_to_assembly,
    evaluate_dbase_statements,
    parse_dbase_statements,
)


def load_d64():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_dbase_stage7_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseProcedureFunctionStage7Tests(unittest.TestCase):
    def test_function_two_arguments_and_precedence(self):
        source = """
function foo(a, b)
    return a + b
? foo(2 + 3 * 4, 6)
"""
        statements = parse_dbase_statements(source)
        self.assertEqual(evaluate_dbase_statements(statements), "20\r\n")
        routine = next(s for s in statements if isinstance(s, DBaseRoutineDefinition))
        self.assertEqual(routine.kind, "function")
        self.assertEqual(routine.parameters, ("a", "b"))

    def test_procedure_bare_return_and_call_statement(self):
        source = """
procedure show(a, b)
    ? "sum=" + (a + b)
    return
show(4, 5)
"""
        statements = parse_dbase_statements(source)
        self.assertEqual(evaluate_dbase_statements(statements), "sum=9\r\n")
        self.assertIsInstance(statements[-1], DBaseCallStatement)
        for target in ("pe32", "pe64"):
            asm = compile_dbase_to_assembly(source, target=target).assembly
            self.assertIn("__dbase_procedure_show__number_number:", asm)
            self.assertIn("call __dbase_procedure_show__number_number", asm)

    def test_procedure_return_value_is_rejected(self):
        for value in ("123", '"foo"', "foo()"):
            source = f"procedure p()\n return {value}\n"
            with self.assertRaises(DBaseCompilerError) as ctx:
                parse_dbase_statements(source, filename="proc.dbp")
            self.assertIn("darf mit RETURN keinen Wert", str(ctx.exception))

    def test_function_requires_return_value(self):
        with self.assertRaises(DBaseCompilerError) as ctx:
            parse_dbase_statements("function f()\n return\n", filename="func.dbp")
        self.assertIn("RETURN <expr>", str(ctx.exception))

    def test_function_missing_return_is_rejected(self):
        with self.assertRaises(DBaseCompilerError) as ctx:
            parse_dbase_statements("function f(a)\n ? a\nendfunc\n", filename="func.dbp")
        self.assertIn("benoetigt RETURN <expr>", str(ctx.exception))

    def test_function_can_return_number_string_char_and_other_function(self):
        source = """
function number_value()
    return 123
function string_value()
    return "foo"
function char_value()
    return 'Z'
function relay()
    return string_value()
? number_value()
? string_value()
? char_value()
? relay()
"""
        statements = parse_dbase_statements(source)
        self.assertEqual(evaluate_dbase_statements(statements), "123\r\nfoo\r\nZ\r\nfoo\r\n")
        for target in ("pe32", "pe64"):
            asm = compile_dbase_to_assembly(source, target=target).assembly
            self.assertIn("__dbase_function_number_value__void:", asm)
            self.assertIn("__dbase_function_string_value__void:", asm)
            self.assertIn("__dbase_function_char_value__void:", asm)
            self.assertIn("__dbase_function_relay__void:", asm)

    def test_same_function_specializes_for_different_return_types(self):
        source = """
function identity(value)
    return value
? identity(123)
? identity("text")
? identity('A')
"""
        statements = parse_dbase_statements(source)
        self.assertEqual(evaluate_dbase_statements(statements), "123\r\ntext\r\nA\r\n")
        asm = compile_dbase_to_assembly(source).assembly
        self.assertIn("__dbase_function_identity__number:", asm)
        self.assertIn("__dbase_function_identity__string:", asm)
        self.assertIn("__dbase_function_identity__char:", asm)

    def test_dynamic_string_return_with_numeric_parameter(self):
        source = """
function label(value)
    return "Wert=" + value
? label(14)
"""
        statements = parse_dbase_statements(source)
        self.assertEqual(evaluate_dbase_statements(statements), "Wert=14\r\n")
        for target in ("pe32", "pe64"):
            asm = compile_dbase_to_assembly(source, target=target).assembly
            self.assertIn("call __dbase_malloc", asm)
            self.assertIn("call __dbase_memcpy", asm)

    def test_parameter_count_is_not_artificially_limited(self):
        names = [f"p{i}" for i in range(20)]
        values = [str(i + 1) for i in range(20)]
        source = (
            "function sum20(" + ",".join(names) + ")\n"
            " return " + "+".join(names) + "\n"
            "? sum20(" + ",".join(values) + ")\n"
        )
        statements = parse_dbase_statements(source)
        self.assertEqual(evaluate_dbase_statements(statements), "210\r\n")
        asm = compile_dbase_to_assembly(source).assembly
        self.assertIn("_param_19_p19_num", asm)
        self.assertIn("__dbase_call_1_arg_19_num", asm)

    def test_nested_same_signature_call_keeps_outer_arguments(self):
        source = """
function add(a,b)
    return a+b
? add(1, add(2,3))
"""
        statements = parse_dbase_statements(source)
        self.assertEqual(evaluate_dbase_statements(statements), "6\r\n")
        asm = compile_dbase_to_assembly(source).assembly
        # Zwei getrennte Call-Site-Tempbereiche verhindern, dass der innere
        # add()-Aufruf das erste Argument des aeusseren Aufrufs zerstoert.
        self.assertIn("__dbase_call_1_arg_0_num", asm)
        self.assertIn("__dbase_call_2_arg_0_num", asm)

    def test_procedure_cannot_be_used_as_expression(self):
        source = """
procedure p(a)
    return
? p(1)
"""
        with self.assertRaises(DBaseCompilerError) as ctx:
            compile_dbase_to_assembly(source)
        self.assertIn("liefert keinen Wert", str(ctx.exception))

    def test_argument_count_is_checked(self):
        source = """
function f(a,b)
    return a+b
? f(1)
"""
        with self.assertRaises(DBaseCompilerError) as ctx:
            compile_dbase_to_assembly(source)
        self.assertIn("erwartet 2 Parameter", str(ctx.exception))

    def test_optional_end_markers_are_accepted(self):
        source = """
function f(a)
    return a + 1
endfunc
procedure p(a)
    ? a
endproc
? f(4)
p(7)
"""
        statements = parse_dbase_statements(source)
        self.assertEqual(evaluate_dbase_statements(statements), "5\r\n7\r\n")

    def test_pe32_and_pe64_link_member_code(self):
        d64 = load_d64()
        source = """
function add6(a,b,c,d,e,f)
    return a+b+c+d+e+f
procedure show8(a,b,c,d,e,f,g,h)
    ? a+b+c+d+e+f+g+h
    return
? add6(1,2,3,4,5,6)
show8(1,2,3,4,5,6,7,8)
"""
        for target, magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(source, target=target)
            program = (
                d64.assemble_pe32_source(result.assembly, filename="member32.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="member64.asm", gui=True)
            )
            self.assertTrue(program.executable.startswith(b"MZ"))
            pe = struct.unpack_from("<I", program.executable, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24)[0], magic)
            self.assertEqual(struct.unpack_from("<H", program.executable, pe + 24 + 68)[0], 2)


if __name__ == "__main__":
    unittest.main()
