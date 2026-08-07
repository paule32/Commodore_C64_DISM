from __future__ import annotations

import unittest
from pathlib import Path

from d64_dism import assemble_mos6510_source

ROOT = Path(__file__).resolve().parents[1]
ASM_PATH = ROOT / "runtime" / "graphics" / "c64" / "graphics_c64.asm"
HEADER_PATH = ROOT / "c64c" / "include" / "graphics.h"
PASCAL_WRAPPER = ROOT / "c64pascal" / "units" / "System" / "Graphics.c64.c"


class C64DirectGraphicsPrimitiveTests(unittest.TestCase):
    def test_all_public_primitives_are_exported_by_direct_asm(self) -> None:
        program = assemble_mos6510_source(
            ".nostub\n" + ASM_PATH.read_text(encoding="utf-8")
        )
        for symbol in (
            "settextcolor", "clearscreen", "initgraphics", "donegraphics",
            "setpixel", "getpixel", "drawline", "drawrect", "fillrect",
            "drawcircle", "fillcircle", "floodfill", "drawtriangle",
            "filltriangle", "drawtriangleangles",
        ):
            self.assertIn(symbol, program.symbols)
            self.assertGreaterEqual(program.symbols[symbol], 0x4000)
            self.assertLess(program.symbols[symbol], 0x8000)

    def test_c64_multicolor_target_does_not_link_generated_common_c_primitives(self) -> None:
        header = HEADER_PATH.read_text(encoding="utf-8")
        wrapper = PASCAL_WRAPPER.read_text(encoding="utf-8")
        c64_block = header.split(
            "#if defined(__D64_TARGET_C64__)", 1
        )[1].split("#endif", 1)[0]
        self.assertIn("graphics_c64.asm", c64_block)
        self.assertNotIn("graphics_api.c", c64_block)
        self.assertIn("graphics_c64.asm", wrapper)
        self.assertNotIn("graphics_api.c", wrapper)

    def test_multicolor_fill_algorithms_use_direct_spans_and_scanlines(self) -> None:
        source = ASM_PATH.read_text(encoding="utf-8")
        self.assertIn("__gfx_fillrect_row:", source)
        self.assertIn("__gfx_fillcircle_loop:", source)
        self.assertIn("__gfx_filltriangle_scanline:", source)
        self.assertIn("__gfx_filltri_draw_current_span:", source)
        self.assertNotIn("__cmod_graphics_api_", source)

    def test_triangle_angle_quadrants_cover_180_to_255_degrees(self) -> None:
        source = ASM_PATH.read_text(encoding="utf-8")
        section = source.split("__gfx_sin_quadrant:", 1)[1].split(
            "__gfx_sin_index:", 1
        )[0]
        self.assertIn("cmp #$B4", section)
        self.assertIn("__gfx_sin_q2_high:", section)
        self.assertIn("__gfx_sin_q1_low:", section)


if __name__ == "__main__":
    unittest.main()
