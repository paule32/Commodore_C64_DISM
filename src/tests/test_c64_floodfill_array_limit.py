from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "runtime" / "graphics" / "common" / "graphics_api.c"


class C64FloodFillArrayLimitTests(unittest.TestCase):
    def test_no_512_byte_unsigned_int_flood_array(self):
        text = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("unsigned int GfxFloodX[GFX_FLOOD_STACK_SIZE]", text)
        self.assertIn("unsigned char GfxFloodXLow[GFX_FLOOD_STACK_SIZE]", text)
        self.assertIn("unsigned char GfxFloodXHigh[GFX_FLOOD_STACK_SIZE]", text)
        self.assertIn("unsigned char GfxFloodY[GFX_FLOOD_STACK_SIZE]", text)

    def test_each_flood_array_is_at_most_256_bytes(self):
        text = SOURCE.read_text(encoding="utf-8")
        self.assertIn("#define GFX_FLOOD_STACK_SIZE 256", text)
        declarations = re.findall(
            r"static\s+unsigned\s+char\s+(GfxFlood\w+)\[GFX_FLOOD_STACK_SIZE\]",
            text,
        )
        self.assertEqual(
            {"GfxFloodXLow", "GfxFloodXHigh", "GfxFloodY"},
            set(declarations),
        )

    def test_x_coordinate_is_reassembled_as_16_bit_value(self):
        text = SOURCE.read_text(encoding="utf-8")
        self.assertIn("GfxFloodXLow[index] = x & 255u;", text)
        self.assertIn("GfxFloodXHigh[index] = (x >> 8) & 255u;", text)
        self.assertIn("(GfxFloodXHigh[index] << 8)", text)
        self.assertIn("current_x = gfx_flood_load_x(top);", text)


if __name__ == "__main__":
    unittest.main()
