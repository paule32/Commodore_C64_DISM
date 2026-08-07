from __future__ import annotations

import unittest
from pathlib import Path

from c64c import compile_c_to_assembly
from c64pascal import C64PascalError, compile_pascal_to_assembly


ROOT = Path(__file__).resolve().parents[1]


class PascalAggregateTypeTests(unittest.TestCase):
    def test_advanced_example_compiles(self) -> None:
        source = (ROOT / "examples" / "c64pascal" / "advanced_types.pas").read_text(
            encoding="utf-8"
        )
        generated = compile_pascal_to_assembly(source, filename="advanced_types.pas")
        self.assertIn("__pas_method_tcounter_create:", generated.assembly)
        self.assertIn("__pas_method_tcounter_inc:", generated.assembly)
        self.assertIn("__pas_method_tcounter_getvalue:", generated.assembly)
        self.assertIn("__pas_range_error:", generated.assembly)
        self.assertEqual(generated.variable_count, 4)

    def test_constant_array_index_is_checked_while_compiling(self) -> None:
        source = """program Bounds;
type TValues = array[1..3] of Byte;
var Values: TValues;
begin Values[4] := 1 end.
"""
        with self.assertRaisesRegex(C64PascalError, "außerhalb 1\\.\\.3"):
            compile_pascal_to_assembly(source)

    def test_unknown_record_field_is_rejected(self) -> None:
        source = """program Fields;
type TPoint = record X: Integer; end;
var Point: TPoint;
begin Point.Y := 1 end.
"""
        with self.assertRaisesRegex(C64PascalError, "Feld nicht gefunden"):
            compile_pascal_to_assembly(source)

    def test_declared_method_needs_implementation(self) -> None:
        source = """program Methods;
type TThing = class procedure Run; end;
var Thing: TThing;
begin Thing.Run end.
"""
        with self.assertRaisesRegex(C64PascalError, "Implementierung fehlt"):
            compile_pascal_to_assembly(source)

    def test_pascal_mixed_case_uses_lowercase_petscii_mode(self) -> None:
        generated = compile_pascal_to_assembly(
            "program Text; begin WriteLn('Counter = 5') end."
        )
        self.assertIn(
            "__pascal_start:\n    lda #$0E\n    jsr $FFD2",
            generated.assembly,
        )
        self.assertIn(
            ".byte $C3, $4F, $55, $4E, $54, $45, $52, $20, $3D, $20, $35, $00",
            generated.assembly,
        )

    def test_c_mixed_case_uses_lowercase_petscii_mode(self) -> None:
        generated = compile_c_to_assembly(
            'int main(void) { printf("Counter = %d\\n", 5); return 0; }'
        )
        self.assertIn(
            "__c_start:\n    lda #$0E\n    jsr $FFD2",
            generated.assembly,
        )
        self.assertIn(
            ".byte $C3, $4F, $55, $4E, $54, $45, $52, $20, $3D, $20, $00",
            generated.assembly,
        )


if __name__ == "__main__":
    unittest.main()
