from __future__ import annotations

import unittest
from pathlib import Path

from d64_dism import (
    C64_PIXEL_SCREEN_PACKED_SIZE,
    C64_PIXEL_SCREEN_PIXEL_COUNT,
    C64_PIXEL_SCREEN_WIDTH,
    C64_TEXT_SCREEN_CELL_COUNT,
    C64_TEXT_SCREEN_FILE_SIZE,
    c64_pixel_screen_draw_circle,
    c64_pixel_screen_draw_line,
    c64_pixel_screen_draw_rect,
    c64_pixel_screen_fill_circle,
    c64_pixel_screen_fill_rect,
    c64_pixel_screen_flood_fill,
    decode_c64_pixel_screen_data,
    decode_c64_text_screen_data,
    encode_c64_pixel_screen_data,
    encode_c64_text_screen_data,
    format_c64_pixel_screen_output,
    format_c64_text_screen_output,
)

ROOT = Path(__file__).resolve().parents[1]
GUI_SOURCE = ROOT / "d64_dism.py"


class C64TextScreenDataTests(unittest.TestCase):
    def test_text_screen_round_trip_preserves_characters_and_colors(self) -> None:
        characters = bytearray((index * 7) & 0xFF for index in range(C64_TEXT_SCREEN_CELL_COUNT))
        colors = bytearray(index & 0x0F for index in range(C64_TEXT_SCREEN_CELL_COUNT))
        payload = encode_c64_text_screen_data(characters, colors)
        self.assertEqual(len(payload), C64_TEXT_SCREEN_FILE_SIZE)
        decoded_characters, decoded_colors = decode_c64_text_screen_data(payload)
        self.assertEqual(decoded_characters, characters)
        self.assertEqual(decoded_colors, colors)

    def test_1000_byte_screen_gets_default_white_color(self) -> None:
        characters = bytes([32]) * C64_TEXT_SCREEN_CELL_COUNT
        decoded_characters, decoded_colors = decode_c64_text_screen_data(characters)
        self.assertEqual(decoded_characters, bytearray(characters))
        self.assertEqual(decoded_colors, bytearray([1] * C64_TEXT_SCREEN_CELL_COUNT))

    def test_text_screen_exports_all_languages(self) -> None:
        characters = bytearray([32] * C64_TEXT_SCREEN_CELL_COUNT)
        colors = bytearray([1] * C64_TEXT_SCREEN_CELL_COUNT)
        outputs = {
            name: format_c64_text_screen_output(characters, colors, name)
            for name in ("Assembler", "Pascal", "C", "BASIC")
        }
        self.assertIn("C64TextScreenCharacters:", outputs["Assembler"])
        self.assertIn("array[0..24, 0..39] of Byte", outputs["Pascal"])
        self.assertIn("C64TextScreenCharacters[25][40]", outputs["C"])
        self.assertIn("DIM SC(999)", outputs["BASIC"])


class C64PixelScreenDataTests(unittest.TestCase):
    def test_pixel_screen_round_trip_preserves_all_sixteen_colors(self) -> None:
        pixels = bytearray(index & 0x0F for index in range(C64_PIXEL_SCREEN_PIXEL_COUNT))
        packed = encode_c64_pixel_screen_data(pixels)
        self.assertEqual(len(packed), C64_PIXEL_SCREEN_PACKED_SIZE)
        self.assertEqual(decode_c64_pixel_screen_data(packed), pixels)

    def test_drawing_primitives_change_expected_pixels(self) -> None:
        pixels = bytearray(C64_PIXEL_SCREEN_PIXEL_COUNT)
        c64_pixel_screen_draw_line(pixels, 0, 0, 319, 199, 1)
        self.assertEqual(pixels[0], 1)
        self.assertEqual(pixels[199 * C64_PIXEL_SCREEN_WIDTH + 319], 1)

        c64_pixel_screen_draw_rect(pixels, 10, 10, 20, 20, 2)
        self.assertEqual(pixels[10 * C64_PIXEL_SCREEN_WIDTH + 10], 2)
        self.assertEqual(pixels[20 * C64_PIXEL_SCREEN_WIDTH + 20], 2)

        c64_pixel_screen_fill_rect(pixels, 30, 30, 39, 39, 3)
        filled = sum(
            pixels[y * C64_PIXEL_SCREEN_WIDTH + x] == 3
            for y in range(30, 40)
            for x in range(30, 40)
        )
        self.assertEqual(filled, 100)

        c64_pixel_screen_draw_circle(pixels, 80, 80, 12, 4)
        self.assertEqual(pixels[80 * C64_PIXEL_SCREEN_WIDTH + 92], 4)
        self.assertEqual(pixels[68 * C64_PIXEL_SCREEN_WIDTH + 80], 4)

        c64_pixel_screen_fill_circle(pixels, 120, 80, 10, 5)
        self.assertEqual(pixels[80 * C64_PIXEL_SCREEN_WIDTH + 120], 5)

    def test_flood_fill_stays_inside_rectangle(self) -> None:
        pixels = bytearray(C64_PIXEL_SCREEN_PIXEL_COUNT)
        c64_pixel_screen_draw_rect(pixels, 5, 5, 15, 15, 1)
        c64_pixel_screen_flood_fill(pixels, 10, 10, 6)
        self.assertEqual(pixels[10 * C64_PIXEL_SCREEN_WIDTH + 10], 6)
        self.assertEqual(pixels[5 * C64_PIXEL_SCREEN_WIDTH + 5], 1)
        self.assertEqual(pixels[4 * C64_PIXEL_SCREEN_WIDTH + 4], 0)

    def test_pixel_screen_exports_all_languages(self) -> None:
        pixels = bytearray(C64_PIXEL_SCREEN_PIXEL_COUNT)
        outputs = {
            name: format_c64_pixel_screen_output(pixels, name)
            for name in ("Assembler", "Pascal", "C", "BASIC")
        }
        self.assertIn("C64PixelScreenData:", outputs["Assembler"])
        self.assertIn("array[0..31999] of Byte", outputs["Pascal"])
        self.assertIn("C64PixelScreenData[32000]", outputs["C"])
        self.assertIn("DIM PX(31999)", outputs["BASIC"])


class C64ScreenEditorIntegrationTests(unittest.TestCase):
    def test_character_output_is_beside_grid_under_preview(self) -> None:
        source = GUI_SOURCE.read_text(encoding="utf-8")
        character_start = source.index("class C64CharacterEditorDialog")
        palette_start = source.index("class C64PaletteEditorDialog")
        character_source = source[character_start:palette_start]
        self.assertNotIn("self.export_button", character_source)
        self.assertIn('QGroupBox("Ausgabe Format", right_panel)', character_source)
        self.assertIn('"Quellcode speichern unter..."', character_source)
        self.assertLess(
            character_source.index("preview_column.addWidget(self.preview"),
            character_source.index("preview_column.addWidget(self.output_format_box)"),
        )
        self.assertLess(
            character_source.index("preview_column.addWidget(self.output_format_box)"),
            character_source.index("preview_column.addWidget(self.output_save_as_button)"),
        )

    def test_tools_and_file_routes_are_integrated(self) -> None:
        source = GUI_SOURCE.read_text(encoding="utf-8")
        self.assertIn("class C64TextScreenEditorDialog", source)
        self.assertIn("class C64PixelScreenEditorDialog", source)
        self.assertIn('"C64 Text-Bildschirm-Editor …"', source)
        self.assertIn('"C64 Pixel-Bildschirm-Editor …"', source)
        self.assertIn('path.suffix.lower() in {".scr", ".screen"}', source)
        self.assertIn('path.suffix.lower() in {".px16", ".pixel", ".pix"}', source)
        for tool in ("Pencil", "Eraser", "Line", "Rect", "FillRect", "Circle", "FillCircle", "Fill"):
            self.assertIn(f'("{tool}",', source)


if __name__ == "__main__":
    unittest.main()
