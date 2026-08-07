from pathlib import Path
import unittest

from c64c.compiler import compile_c_module_to_assembly


ROOT = Path(__file__).resolve().parents[1]


class C64DynamicArrayIndexTests(unittest.TestCase):
    def test_parameter_is_dynamic_array_index_not_constant(self):
        source = """
static unsigned char values[256];

int load_value(unsigned int index)
{
    return values[index];
}
"""
        generated = compile_c_module_to_assembly(
            source,
            filename="dynamic_array_index.c",
            include_paths=[ROOT / "c64c" / "include"],
            target="c64",
            module_prefix="__dynamic_index_test",
        )
        assembly = generated.assembly
        self.assertIn("load_value", assembly)
        self.assertNotIn("Konstanter Bezeichner nicht gefunden", assembly)

    def test_graphics_flood_stack_uses_parameter_index(self):
        source = (ROOT / "runtime" / "graphics" / "common" / "graphics_api.c").read_text(
            encoding="utf-8"
        )
        self.assertIn("GfxFloodXLow[index]", source)
        self.assertIn("GfxFloodXHigh[index]", source)
        self.assertIn("GfxFloodY[index]", source)

    def test_constant_probe_does_not_depend_on_error_class(self):
        compiler = (ROOT / "c64pascal" / "compiler.py").read_text(encoding="utf-8")
        self.assertIn("def _is_constant_expression", compiler)
        self.assertIn("if self._is_constant_expression(selector.expression):", compiler)
        self.assertNotIn("except C64PascalError:\n                index_value = None", compiler)


if __name__ == "__main__":
    unittest.main()
