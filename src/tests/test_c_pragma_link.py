from pathlib import Path
import tempfile
import unittest

from c64c.compiler import compile_c_to_assembly


class CPragmaLinkTests(unittest.TestCase):
    def _project(self, directory: Path) -> Path:
        (directory / "math_module.h").write_text(
            "#pragma once\n"
            "#pragma link \"math_module.c\"\n"
            "int AddValues(int left, int right);\n"
            "int ClampValue(int value, int minimum, int maximum);\n",
            encoding="utf-8",
        )
        (directory / "math_module.c").write_text(
            "#include \"math_module.h\"\n"
            "static int DoubleValue(int value) { return value + value; }\n"
            "int AddValues(int left, int right) { return left + right; }\n"
            "int ClampValue(int value, int minimum, int maximum) {\n"
            "  if (value < minimum) return minimum;\n"
            "  if (value > maximum) return maximum;\n"
            "  return value;\n"
            "}\n",
            encoding="utf-8",
        )
        main = directory / "main.c"
        main.write_text(
            "#include \"math_module.h\"\n"
            "int main(void) {\n"
            "  int value;\n"
            "  value = AddValues(20, 30);\n"
            "  value = ClampValue(value, 0, 40);\n"
            "  return value;\n"
            "}\n",
            encoding="utf-8",
        )
        return main

    def test_amiga_c_module_is_compiled_and_linked(self):
        with tempfile.TemporaryDirectory() as temporary:
            main = self._project(Path(temporary))
            generated = compile_c_to_assembly(
                main.read_text(encoding="utf-8"),
                filename=str(main),
                target="amiga",
            )
            self.assertEqual(len(generated.linked_c_files), 1)
            self.assertTrue(generated.linked_c_files[0].endswith("math_module.c"))
            self.assertIn("bsr AddValues", generated.assembly)
            self.assertIn("AddValues:", generated.assembly)
            self.assertIn("ClampValue:", generated.assembly)
            self.assertIn("_DoubleValue:", generated.assembly)

    def test_c64_c_module_is_compiled_and_linked(self):
        with tempfile.TemporaryDirectory() as temporary:
            main = self._project(Path(temporary))
            generated = compile_c_to_assembly(
                main.read_text(encoding="utf-8"),
                filename=str(main),
                target="c64",
            )
            self.assertEqual(len(generated.linked_c_files), 1)
            self.assertIn("jsr AddValues", generated.assembly)
            self.assertIn("AddValues:", generated.assembly)
            self.assertNotIn("@cframe:", generated.assembly)
            self.assertIn("sta $00FE,x", generated.assembly)


if __name__ == "__main__":
    unittest.main()
