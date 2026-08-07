from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class GraphicsFastPrimitiveTests(unittest.TestCase):
    def test_amiga_has_register_pixel_and_hline_paths(self):
        text = (ROOT / "runtime/graphics/amiga/graphics_amiga.asm").read_text(encoding="utf-8")
        self.assertIn("__gfx_setpixel_fast:", text)
        self.assertIn("__gfx_getpixel_fast:", text)
        self.assertIn("__gfx_hline_fast:", text)
        self.assertIn("bra __gfx_setpixel_fast", text)
        self.assertNotIn("__gfx_fr_x_loop:", text)

    def test_fill_circle_uses_horizontal_spans(self):
        text = (ROOT / "runtime/graphics/amiga/graphics_amiga.asm").read_text(encoding="utf-8")
        section = text.split("FillCircle:", 1)[1].split("__gfx_flood_push:", 1)[0]
        self.assertGreaterEqual(section.count("bsr __gfx_hline_fast"), 4)
        self.assertNotIn("__gfx_fc_fill_loop:", section)

    def test_c64_uses_direct_6510_primitives(self):
        header = (ROOT / "c64c/include/graphics.h").read_text(encoding="utf-8")
        target = (ROOT / "runtime/graphics/c64/graphics_c64.asm").read_text(encoding="utf-8")
        self.assertIn('graphics/c64/graphics_c64.asm', header)
        self.assertNotIn('graphics/c64/graphics_target.c', header)
        self.assertNotIn('graphics/common/graphics_api.c', header)
        for symbol in (
            "DrawLine:", "DrawRect:", "FillRect:", "DrawCircle:",
            "FillCircle:", "FloodFill:", "DrawTriangle:",
            "FillTriangle:", "DrawTriangleAngles:",
        ):
            self.assertIn(symbol, target)
        self.assertIn("__GraphicsHLine:", target)
        self.assertIn("__gfx_setpixel_core:", target)
        self.assertIn("__gfx_filltriangle_scanline:", target)

if __name__ == "__main__":
    unittest.main()
