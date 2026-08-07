from __future__ import annotations

import unittest
from pathlib import Path

from d64_dism import assemble_mos6510_source

ROOT = Path(__file__).resolve().parents[1]
ASM_PATH = ROOT / "runtime" / "graphics" / "c64" / "graphics_c64.asm"


class C64MulticolorPaletteTests(unittest.TestCase):
    def test_target_assembles_and_exposes_palette_diagnostics(self) -> None:
        program = assemble_mos6510_source(
            ".nostub\n" + ASM_PATH.read_text(encoding="utf-8")
        )
        self.assertIn("__gfx_palette_overflow", program.symbols)
        self.assertIn("__gfx_select_pixel_code", program.symbols)
        self.assertIn("__gfx_write_pixel_code", program.symbols)
        self.assertLess(program.end_address, 0x8000)

    def test_two_adjacent_x_coordinates_share_one_multicolor_field(self) -> None:
        source = ASM_PATH.read_text(encoding="utf-8")
        self.assertIn(
            ".byte $C0, $C0, $30, $30, $0C, $0C, $03, $03",
            source,
        )
        self.assertIn(
            ".byte $06, $06, $04, $04, $02, $02, $00, $00",
            source,
        )

    def test_demo_artifacts_exist(self) -> None:
        prg = ROOT / "examples" / "graphics" / "graphics_demo.generated.prg"
        image = ROOT / "examples" / "graphics" / "graphics_demo.expected.c64.png"
        self.assertGreater(prg.stat().st_size, 1000)
        self.assertGreater(image.stat().st_size, 100)


if __name__ == "__main__":
    unittest.main()
