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
    DBaseIfStatement,
    compile_dbase_to_assembly,
    evaluate_dbase_statements,
    parse_dbase_statements,
)


def load_d64():
    sys.modules.setdefault("flags_rc", types.ModuleType("flags_rc"))
    name = "_d64_dbase_if_stage10_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "d64_dism.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class DBaseIfStage10Tests(unittest.TestCase):
    def test_simple_if_numeric(self):
        source = "X=14\nIF X >= 14\n? \"ok\"\nENDIF\n"
        statements = parse_dbase_statements(source)
        self.assertTrue(any(isinstance(item, DBaseIfStatement) for item in statements))
        self.assertEqual(evaluate_dbase_statements(statements), "ok\r\n")

    def test_if_else(self):
        source = "X=3\nIF X > 5\n? \"high\"\nELSE\n? \"low\"\nENDIF\n"
        self.assertEqual(evaluate_dbase_statements(parse_dbase_statements(source)), "low\r\n")

    def test_if_elseif_else(self):
        source = (
            "X=5\n"
            "IF X < 5\n? \"low\"\n"
            "ELSEIF X == 5\n? \"equal\"\n"
            "ELSE\n? \"high\"\nENDIF\n"
        )
        self.assertEqual(evaluate_dbase_statements(parse_dbase_statements(source)), "equal\r\n")

    def test_nested_if(self):
        source = (
            "X=5\n"
            "IF X >= 5\n"
            " IF X # 7\n"
            "  ? \"nested\"\n"
            " ENDIF\n"
            "ENDIF\n"
        )
        self.assertEqual(evaluate_dbase_statements(parse_dbase_statements(source)), "nested\r\n")

    def test_not_equal_operators(self):
        for operator in ("#", "<>"):
            source = f"X=1\nIF X {operator} 2\n? \"yes\"\nENDIF\n"
            self.assertEqual(evaluate_dbase_statements(parse_dbase_statements(source)), "yes\r\n")

    def test_numeric_hex_and_float_conditions(self):
        source = (
            "IF 0x10 == 16\n? \"hex\"\nENDIF\n"
            "IF 2.5 < 3.0\n? \"float\"\nENDIF\n"
        )
        self.assertEqual(evaluate_dbase_statements(parse_dbase_statements(source)), "hex\r\nfloat\r\n")

    def test_string_and_char_conditions(self):
        source = (
            "IF \"abc\" < \"abd\"\n? \"string\"\nENDIF\n"
            "IF 'A' # 'B'\n? \"char\"\nENDIF\n"
        )
        self.assertEqual(evaluate_dbase_statements(parse_dbase_statements(source)), "string\r\nchar\r\n")

    def test_mixed_number_and_text_comparison_is_rejected(self):
        source = 'IF 1 == "1"\n? "bad"\nENDIF\n'
        with self.assertRaises(DBaseCompilerError) as ctx:
            compile_dbase_to_assembly(source)
        self.assertIn("zwei numerische Werte oder zwei Textwerte", str(ctx.exception))

    def test_single_equal_is_not_comparison(self):
        with self.assertRaises(DBaseCompilerError) as ctx:
            parse_dbase_statements("IF 1 = 1\n? 1\nENDIF\n")
        self.assertIn("'=='", str(ctx.exception))

    def test_missing_endif_is_rejected(self):
        with self.assertRaises(DBaseCompilerError) as ctx:
            parse_dbase_statements("IF 1 == 1\n? 1\n")
        self.assertIn("ENDIF", str(ctx.exception))

    def test_function_and_procedure_end_only_with_return(self):
        source = (
            "function add(a,b)\n"
            " IF a > b\n  ? \"a>b\"\n ENDIF\n"
            " return a+b\n"
            "procedure show(v)\n ? v\n return\n"
            "? add(2,3)\nshow(9)\n"
        )
        self.assertEqual(evaluate_dbase_statements(parse_dbase_statements(source)), "5\r\n9\r\n")

    def test_return_inside_nested_if_works_at_runtime(self):
        source = (
            "function max2(a,b)\n"
            " IF a >= b\n  return a\n ENDIF\n"
            " return b\n"
            "? max2(7,3)\n? max2(2,9)\n"
        )
        self.assertEqual(evaluate_dbase_statements(parse_dbase_statements(source)), "7\r\n9\r\n")

    def test_old_member_end_markers_are_deleted(self):
        for marker in ("endfunc", "endfunction", "endproc", "endprocedure", "endunction"):
            prefix = "procedure p()\n return\n" if "proc" in marker else "function f()\n return 1\n"
            with self.assertRaises(DBaseCompilerError):
                parse_dbase_statements(prefix + marker + "\n")

    def test_generated_asm_contains_numeric_and_text_comparisons(self):
        source = (
            "X=14\nIF X >= 14\n? \"n\"\nENDIF\n"
            "S=\"abc\"\nIF S < \"abd\"\n? \"s\"\nENDIF\n"
        )
        asm = compile_dbase_to_assembly(source, target="pe32").assembly
        self.assertIn("fucomip st0, st1", asm)
        self.assertIn('import __dbase_memcmp, "msvcrt.dll", "memcmp"', asm)
        self.assertIn("call __dbase_memcmp", asm)

    def test_pe32_and_pe64_link_nested_if(self):
        d64 = load_d64()
        source = (
            "X=5\n"
            "IF X >= 5\n IF X <> 8\n  ? \"ok\"\n ENDIF\nENDIF\n"
            "S=\"abc\"\nIF S <= \"abc\"\n? \"text\"\nENDIF\n"
        )
        for target, magic in (("pe32", 0x10B), ("pe64", 0x20B)):
            result = compile_dbase_to_assembly(source, target=target, windows_application_mode="GUI")
            program = (
                d64.assemble_pe32_source(result.assembly, filename="if32.asm", gui=True)
                if target == "pe32"
                else d64.assemble_pe64_source(result.assembly, filename="if64.asm", gui=True)
            )
            exe = program.executable
            pe = struct.unpack_from("<I", exe, 0x3C)[0]
            self.assertEqual(struct.unpack_from("<H", exe, pe + 24)[0], magic)
            self.assertEqual(struct.unpack_from("<H", exe, pe + 24 + 68)[0], 2)


if __name__ == "__main__":
    unittest.main()
