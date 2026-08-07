from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMPILER = ROOT / "c64c" / "compiler.py"
GRAPHICS = ROOT / "runtime" / "graphics" / "common" / "graphics_api.c"


class CShiftArrayOperandTests(unittest.TestCase):
    def test_shift_lowering_accepts_array_operand(self):
        text = COMPILER.read_text(encoding="utf-8")
        self.assertIn("identifier_atom", text)
        self.assertIn('r"(?:\\s*\\[\\s*[^\\]\\r\\n]+\\s*\\])*"', text)
        self.assertIn('__d64_shl', text)
        self.assertIn('__d64_shr', text)

    def test_both_backends_emit_real_shift_instructions(self):
        text = COMPILER.read_text(encoding="utf-8")
        self.assertIn('def _compile_c_shift(self, expression: BinaryExpression):', text)
        self.assertIn('asl {self.ZP_LEFT_LO}', text)
        self.assertIn('rol {self.ZP_LEFT_HI}', text)
        self.assertIn('instruction = "lsl.w"', text)
        self.assertIn('instruction = "asr.w"', text)
        self.assertIn('instruction = "lsr.w"', text)

    def test_array_access_is_lowered_to_pascal_designator(self):
        text = COMPILER.read_text(encoding="utf-8")
        self.assertIn("def _array_designator(", text)
        self.assertIn("a[i][j][k] -> ((i * dim1 + j) * dim2 + k)", text)
        self.assertIn("return AssignmentStatement(position, designator, value)", text)
        self.assertIn("IndexSelector(position, flat_index)", text)
        self.assertNotIn("IndexSelector(flat_index)", text)

    def test_floodfill_uses_array_shift_case(self):
        text = GRAPHICS.read_text(encoding="utf-8")
        self.assertIn("GfxFloodXHigh[index] << 8", text)

    def test_lowering_order_keeps_array_rewrite_after_shift_rewrite(self):
        text = COMPILER.read_text(encoding="utf-8")
        shift_pos = text.index("shift_pattern = re.compile")
        array_pos = text.index("access_pattern = re.compile(chain)")
        self.assertLess(shift_pos, array_pos)


if __name__ == "__main__":
    unittest.main()
