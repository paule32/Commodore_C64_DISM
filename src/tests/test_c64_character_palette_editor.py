from __future__ import annotations

import unittest
from pathlib import Path

from d64_dism import (
    C64_CHARACTER_FILE_SIZE,
    C64_CHARACTER_PALETTE,
    C64_PALETTE_FILE_SIZE,
    c64_output_format_extension,
    decode_c64_palette_data,
    encode_c64_palette_data,
    format_c64_charset_output,
    format_c64_palette_asm,
    format_c64_palette_basic,
    format_c64_palette_c,
    format_c64_palette_output,
    format_c64_palette_pascal,
    normalize_c64_color_hex,
    assemble_mos6510_source,
)

ROOT = Path(__file__).resolve().parents[1]
GUI_SOURCE = ROOT / "d64_dism.py"


class C64OutputFormatTests(unittest.TestCase):
    def test_character_output_supports_all_four_languages(self) -> None:
        charset = bytearray(C64_CHARACTER_FILE_SIZE)
        outputs = {
            name: format_c64_charset_output(charset, name)
            for name in ("Assembler", "Pascal", "C", "BASIC")
        }
        self.assertIn("C64CustomCharset:", outputs["Assembler"])
        self.assertIn("array[0..255, 0..7] of Byte", outputs["Pascal"])
        self.assertIn("C64CustomCharset[256][8]", outputs["C"])
        self.assertIn("DIM CS(255,7)", outputs["BASIC"])
        self.assertEqual(outputs["BASIC"].count(" DATA "), 256)

    def test_output_extensions_match_selected_language(self) -> None:
        self.assertEqual(c64_output_format_extension("Assembler"), ".asm")
        self.assertEqual(c64_output_format_extension("Pascal"), ".pas")
        self.assertEqual(c64_output_format_extension("C"), ".h")
        self.assertEqual(c64_output_format_extension("BASIC"), ".bas")


class C64PaletteDataTests(unittest.TestCase):
    def test_palette_binary_round_trip_contains_48_bytes(self) -> None:
        raw = encode_c64_palette_data(C64_CHARACTER_PALETTE)
        self.assertEqual(len(raw), C64_PALETTE_FILE_SIZE)
        decoded = decode_c64_palette_data(raw)
        self.assertEqual(decoded, C64_CHARACTER_PALETTE)

    def test_color_hex_normalization(self) -> None:
        self.assertEqual(normalize_c64_color_hex("#aabbcc"), "#AABBCC")
        self.assertEqual(normalize_c64_color_hex("$112233"), "#112233")
        self.assertEqual(normalize_c64_color_hex("0x445566"), "#445566")
        with self.assertRaises(ValueError):
            normalize_c64_color_hex("#12345")

    def test_palette_exports_all_sixteen_colors(self) -> None:
        asm = format_c64_palette_asm(C64_CHARACTER_PALETTE)
        pascal = format_c64_palette_pascal(C64_CHARACTER_PALETTE)
        c_source = format_c64_palette_c(C64_CHARACTER_PALETTE)
        basic = format_c64_palette_basic(C64_CHARACTER_PALETTE)

        self.assertEqual(asm.count(".byte "), 16)
        self.assertEqual(pascal.count("{ "), 17)  # header + 16 entries
        self.assertEqual(c_source.count("/* "), 17)  # header + 16 entries
        self.assertEqual(basic.count(" DATA "), 16)

    def test_palette_dispatcher_supports_all_languages(self) -> None:
        for output_format in ("Assembler", "Pascal", "C", "BASIC"):
            with self.subTest(output_format=output_format):
                self.assertTrue(
                    format_c64_palette_output(
                        C64_CHARACTER_PALETTE,
                        output_format,
                    ).strip()
                )

    def test_palette_assembler_export_is_accepted(self) -> None:
        program = assemble_mos6510_source(
            ".nostub\n.org $2000\n" + format_c64_palette_asm(C64_CHARACTER_PALETTE)
        )
        self.assertEqual(program.load_address, 0x2000)
        self.assertEqual(program.end_address, 0x202F)
        self.assertEqual(len(program.prg), 50)


class C64PaletteEditorIntegrationTests(unittest.TestCase):
    def test_gui_contains_output_group_and_palette_editor_action(self) -> None:
        source = GUI_SOURCE.read_text(encoding="utf-8")
        self.assertIn('QGroupBox("Ausgabe Format"', source)
        self.assertIn('"Quellcode speichern unter..."', source)
        self.assertIn('"Assembler",\n    "Pascal",\n    "C",\n    "BASIC",', source)
        self.assertIn("class C64PaletteEditorDialog", source)
        self.assertIn('"C64 Paletten-Editor …"', source)
        self.assertIn('QKeySequence("Ctrl+Alt+P")', source)
        self.assertIn('"PAL": {".pal", ".palette"}', source)
        self.assertIn('path.suffix.lower() in {".pal", ".palette"}', source)


if __name__ == "__main__":
    unittest.main()
