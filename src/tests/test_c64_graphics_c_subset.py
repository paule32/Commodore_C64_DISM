from __future__ import annotations

import unittest
from pathlib import Path

from c64c import compile_c_module_to_assembly

ROOT = Path(__file__).resolve().parents[1]
UNIT_SOURCE = ROOT / "c64pascal" / "units" / "System" / "Graphics.c64.c"


class C64GraphicsCSubsetTests(unittest.TestCase):
    def test_pascal_graphics_c_translation_units_compile(self) -> None:
        generated = compile_c_module_to_assembly(
            UNIT_SOURCE.read_text(encoding="utf-8"),
            filename=str(UNIT_SOURCE),
            include_paths=[
                ROOT / "c64c" / "include",
                ROOT / "runtime" / "graphics" / "include",
            ],
            target="c64",
            module_prefix="__test_system_graphics",
        )

        self.assertIn("SetTextColor:", generated.assembly)
        self.assertIn("InitGraphics:", generated.assembly)
        self.assertIn("SetPixel:", generated.assembly)
        self.assertIn("GetPixel:", generated.assembly)
        self.assertIn("DrawTriangleAngles:", generated.assembly)

    def test_target_source_avoids_pointer_cast_array_syntax(self) -> None:
        source = (
            ROOT / "runtime" / "graphics" / "c64" / "graphics_target.c"
        ).read_text(encoding="utf-8")

        self.assertNotIn("((unsigned char *)", source)
        self.assertNotIn("C64_BITMAP[", source)
        self.assertNotIn("C64_SCREEN[", source)
        self.assertIn("poke(C64_BITMAP_BASE + i", source)
        self.assertIn("void __GraphicsHLine", source)


if __name__ == "__main__":
    unittest.main()
