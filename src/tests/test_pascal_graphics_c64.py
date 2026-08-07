from __future__ import annotations

import json
import unittest
from pathlib import Path

from c64pascal import compile_pascal_to_assembly

ROOT = Path(__file__).resolve().parents[1]
UNIT_DIR = ROOT / "c64pascal" / "units"
GRAPHICS_DIR = UNIT_DIR / "System"


class PascalGraphicsC64Tests(unittest.TestCase):
    def test_graphics_pui_references_c64_c_module(self) -> None:
        document = json.loads(
            (GRAPHICS_DIR / "Graphics.pui").read_text(encoding="utf-8")
        )
        self.assertEqual(
            document["implementation"]["c"]["c64"],
            "Graphics.c64.c",
        )
        self.assertEqual(
            document["implementation"]["assembly"]["amiga"],
            "Graphics.amiga.asm",
        )

    def test_same_pascal_source_compiles_for_c64(self) -> None:
        source = """program GraphicsDemo;

uses
    System.Graphics;

var
    CenterColor: TColor;

begin
    SetTextColor(ColorWhite, ColorBlack);
    InitGraphics;
    ClearScreen;

    DrawLine(0, 0, 319, 199, ColorWhite);
    DrawRect(10, 10, 90, 60, ColorRed);
    FillRect(100, 10, 200, 60, ColorCyan, ColorWhite, 2);
    DrawCircle(70, 130, 35, ColorPurple);
    FillCircle(165, 130, 35, ColorGreen, ColorWhite, 2);
    DrawTriangle(225, 175, 270, 95, 315, 175, ColorBlue);
    FillTriangle(210, 185, 260, 105, 310, 185, ColorYellow, ColorWhite, 2);
    DrawTriangleAngles(160, 100, 50, 50, 50, 270, 30, 150, ColorWhite);

    CenterColor := GetPixel(165, 130);
    WriteLn('Graphics demo finished: ', CenterColor);
end.
"""
        generated = compile_pascal_to_assembly(
            source,
            filename=str(ROOT / "examples" / "graphics" / "graphics_demo.pas"),
            include_paths=[UNIT_DIR],
            target="c64",
        )

        self.assertIn("jsr __pas_System_Graphics_SetTextColor", generated.assembly)
        self.assertIn("jsr __pas_System_Graphics_InitGraphics", generated.assembly)
        self.assertIn("jsr __pas_System_Graphics_GetPixel", generated.assembly)
        self.assertIn("__pas_System_Graphics_SetTextColor:", generated.assembly)
        self.assertIn("__pas_System_Graphics_DrawTriangleAngles:", generated.assembly)
        self.assertNotIn("Amiga-spezifische Anweisung", generated.assembly)
        self.assertTrue(
            any(path.endswith("Graphics.generated.c64.asm")
                for path in generated.linked_assembly_files)
        )


if __name__ == "__main__":
    unittest.main()
