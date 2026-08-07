from __future__ import annotations

import json
import unittest

from pathlib import Path

from amiga500 import assemble_amiga_boot_source
from c64pascal import compile_pascal_to_assembly


ROOT = Path(__file__).resolve().parents[1]
UNIT_DIR = ROOT / "c64pascal" / "units"
GRAPHICS_DIR = UNIT_DIR / "System"


class PascalGraphicsAmigaTests(unittest.TestCase):
    def test_graphics_pui_references_amiga_module(self) -> None:
        document = json.loads(
            (GRAPHICS_DIR / "Graphics.pui").read_text(encoding="utf-8")
        )
        self.assertEqual(document["unit"], "System.Graphics")
        self.assertEqual(
            document["implementation"]["assembly"]["amiga"],
            "Graphics.amiga.asm",
        )
        self.assertEqual(len(document["interface"]["routines"]), 15)

    def test_pascal_program_links_real_amiga_graphics_routines(self) -> None:
        source = (
            "program GraphicsLinkTest;\n"
            "uses System.Graphics;\n"
            "var PixelColor: TColor;\n"
            "begin\n"
            "  SetTextColor(ColorWhite, ColorBlack);\n"
            "  InitGraphics;\n"
            "  ClearScreen;\n"
            "  SetPixel(10, 20, ColorRed);\n"
            "  PixelColor := GetPixel(10, 20);\n"
            "  DrawLine(0, 0, 319, 199, ColorWhite);\n"
            "  DrawRect(10, 10, 100, 60, ColorCyan);\n"
            "  FillRect(20, 20, 80, 50, ColorBlue, ColorWhite, 1);\n"
            "  DrawCircle(160, 100, 30, ColorYellow);\n"
            "  FillCircle(160, 100, 20, ColorGreen, ColorWhite, 1);\n"
            "  FloodFill(160, 100, ColorPurple);\n"
            "  DrawTriangle(20, 180, 80, 100, 140, 180, ColorRed);\n"
            "  FillTriangle(180, 180, 240, 100, 300, 180, ColorOrange, ColorWhite, 1);\n"
            "  DrawTriangleAngles(160, 100, 50, 50, 50, 270, 30, 150, ColorWhite);\n"
            "  DoneGraphics(tmUpperLower);\n"
            "end.\n"
        )
        generated = compile_pascal_to_assembly(
            source,
            filename=str(ROOT / "examples" / "graphics" / "graphics_link_test.pas"),
            include_paths=[UNIT_DIR],
            target="amiga",
        )

        self.assertIn(
            "bsr __pas_System_Graphics_InitGraphics",
            generated.assembly,
        )
        self.assertIn(
            "__pas_System_Graphics_SetPixel:",
            generated.assembly,
        )
        self.assertIn(
            "__pas_System_Graphics_GetPixel:",
            generated.assembly,
        )
        self.assertIn(
            "__pas_System_Graphics_DrawTriangleAngles:",
            generated.assembly,
        )
        self.assertTrue(
            any(path.endswith("Graphics.amiga.asm") for path in generated.linked_assembly_files)
        )

        assembled = assemble_amiga_boot_source(generated.assembly)
        self.assertGreater(assembled.instruction_count, 1000)


if __name__ == "__main__":
    unittest.main()
