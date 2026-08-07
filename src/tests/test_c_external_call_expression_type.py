from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PASCAL_COMPILER = ROOT / "c64pascal" / "compiler.py"
SET_RUNTIME = ROOT / "c64c" / "runtime" / "set_runtime.c"


class CExternalCallExpressionTypeTests(unittest.TestCase):
    def test_expression_type_checks_external_function_before_method_lookup(self) -> None:
        source = PASCAL_COMPILER.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(PASCAL_COMPILER))

        codegen = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "_CodeGenerator"
        )
        method = next(
            node
            for node in codegen.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "_expression_type"
        )
        method_source = ast.get_source_segment(source, method)
        self.assertIsNotNone(method_source)

        external_pos = method_source.index("routine = self.external_routines.get(name)")
        method_pos = method_source.index("self._resolve_method_call(designator)")
        self.assertLess(external_pos, method_pos)
        self.assertIn("return routine.result_type", method_source)

    def test_set_runtime_uses_setof_inside_binary_expressions(self) -> None:
        source = SET_RUNTIME.read_text(encoding="utf-8")
        self.assertIn("return value | SetOf(element);", source)
        self.assertIn("return value & ~SetOf(element);", source)
        self.assertIn("(value & SetOf(element)) != 0", source)


if __name__ == "__main__":
    unittest.main()
