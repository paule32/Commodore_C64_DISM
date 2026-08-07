from pathlib import Path
import unittest

from amiga500 import assemble_amiga_boot_source
from c64c import compile_c_to_assembly


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples" / "graphics" / "graphics_demo.c"


class CExternalGraphicsTests(unittest.TestCase):
    def test_amiga_graphics_calls_are_external_and_module_is_linked(self):
        generated = compile_c_to_assembly(
            DEMO.read_text(encoding="utf-8"),
            filename=str(DEMO),
            include_paths=(ROOT / "c64c" / "include", DEMO.parent),
            target="amiga",
        )

        self.assertIn("bsr SetTextColor", generated.assembly)
        self.assertIn("bsr InitGraphics", generated.assembly)
        self.assertIn("bsr DrawLine", generated.assembly)
        self.assertIn("bsr FillRect", generated.assembly)
        self.assertIn("bsr DrawCircle", generated.assembly)
        self.assertIn("bsr GetPixel", generated.assembly)
        self.assertIn("statisch gelinktes C-Modul", generated.assembly)
        self.assertTrue(generated.linked_assembly_files)

        assembled = assemble_amiga_boot_source(
            generated.assembly,
            filename="graphics_demo.generated.amiga.asm",
        )
        self.assertEqual(901120, len(assembled.adf))

    def test_old_prototype_error_is_removed(self):
        compiler = (ROOT / "c64c" / "compiler.py").read_text(encoding="utf-8")
        self.assertNotIn(
            "Codeerzeugung fuer benutzerdefinierte Funktionen folgt",
            compiler,
        )


if __name__ == "__main__":
    unittest.main()
