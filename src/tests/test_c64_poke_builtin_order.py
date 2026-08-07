from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPILER = ROOT / "c64pascal" / "compiler.py"


class C64PokeBuiltinOrderTests(unittest.TestCase):
    def test_poke_and_halt_are_lowered_before_external_routines(self) -> None:
        source = COMPILER.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(COMPILER))

        codegen = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "_CodeGenerator"
        )
        method = next(
            node
            for node in codegen.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "_compile_call_statement"
        )
        method_source = ast.get_source_segment(source, method)
        self.assertIsNotNone(method_source)

        poke_pos = method_source.index('if name == "poke":')
        halt_pos = method_source.index('if name == "halt":')
        external_pos = method_source.index("routine = self.external_routines.get(name)")

        self.assertLess(poke_pos, external_pos)
        self.assertLess(halt_pos, external_pos)
        self.assertIn(f"sta ({{self.ZP_LEFT_LO}}),y", method_source)

    def test_c64_header_keeps_poke_as_a_prototype(self) -> None:
        header = (ROOT / "c64c" / "include" / "c64.h").read_text(
            encoding="utf-8"
        )
        self.assertIn("void poke(uint16_t address, uint8_t value);", header)
        self.assertIn("void c64_poke(uint16_t address, uint8_t value);", header)


if __name__ == "__main__":
    unittest.main()
