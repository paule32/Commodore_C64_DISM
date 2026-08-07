from __future__ import annotations

import unittest
from pathlib import Path

from d64_dism import (
    C64_CHARACTER_EDITABLE_FILE_SIZE,
    C64_CHARACTER_FILE_SIZE,
    c64_character_invert,
    c64_character_mirror_horizontal,
    c64_character_mirror_vertical,
    c64_character_shift,
    c64_charset_character_rows,
    c64_charset_set_character_rows,
    format_c64_charset_asm,
    format_c64_charset_c,
    format_c64_charset_pascal,
    normalize_c64_charset_data,
    assemble_mos6510_source,
)

ROOT = Path(__file__).resolve().parents[1]
GUI_SOURCE = ROOT / "d64_dism.py"


class C64CharacterEditorDataTests(unittest.TestCase):
    def test_normalizes_complete_and_editable_only_charset_files(self) -> None:
        full = bytes((index & 0xFF) for index in range(C64_CHARACTER_FILE_SIZE))
        self.assertEqual(bytes(normalize_c64_charset_data(full)), full)

        compact = bytes((index & 0xFF) for index in range(C64_CHARACTER_EDITABLE_FILE_SIZE))
        normalized = normalize_c64_charset_data(compact)
        self.assertEqual(len(normalized), C64_CHARACTER_FILE_SIZE)
        self.assertEqual(normalized[:8], b"\x00" * 8)
        self.assertEqual(normalized[8:], compact)

    def test_rejects_invalid_charset_size(self) -> None:
        for size in (0, 7, 2039, 2041, 2047, 2049):
            with self.subTest(size=size):
                with self.assertRaises(ValueError):
                    normalize_c64_charset_data(bytes(size))

    def test_reads_and_writes_all_eight_rows(self) -> None:
        charset = bytearray(C64_CHARACTER_FILE_SIZE)
        rows = (0x18, 0x3C, 0x66, 0x7E, 0x66, 0x66, 0x66, 0x00)
        c64_charset_set_character_rows(charset, 0x41, rows)
        self.assertEqual(c64_charset_character_rows(charset, 0x41), rows)
        self.assertEqual(charset[0x41 * 8 : 0x41 * 8 + 8], bytes(rows))

    def test_character_zero_remains_reserved(self) -> None:
        charset = bytearray(C64_CHARACTER_FILE_SIZE)
        with self.assertRaises(ValueError):
            c64_charset_set_character_rows(charset, 0, (0xFF,) * 8)

    def test_transformations_preserve_eight_byte_shape(self) -> None:
        rows = (0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01)
        self.assertEqual(
            c64_character_mirror_horizontal(rows),
            (0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80),
        )
        self.assertEqual(c64_character_mirror_vertical(rows), tuple(reversed(rows)))
        self.assertEqual(c64_character_invert((0x00, 0xFF) * 4), (0xFF, 0x00) * 4)
        self.assertEqual(c64_character_shift((0x80,) + (0,) * 7, 1, 1)[1], 0x40)
        self.assertEqual(c64_character_shift((0x01,) + (0,) * 7, 1, 0)[0], 0x00)

    def test_exports_all_256_characters(self) -> None:
        charset = bytearray(C64_CHARACTER_FILE_SIZE)
        c64_charset_set_character_rows(charset, 0xFF, (0xFF,) * 8)

        asm = format_c64_charset_asm(charset)
        c_source = format_c64_charset_c(charset)
        pascal = format_c64_charset_pascal(charset)

        self.assertEqual(asm.count(".byte "), 256)
        self.assertEqual(c_source.count("/* 0x"), 256)
        self.assertEqual(pascal.count("{ $"), 256)
        self.assertIn("C64CustomCharset:", asm)
        self.assertIn("C64CustomCharset[256][8]", c_source)
        self.assertIn("array[0..255, 0..7] of Byte", pascal)

    def test_exported_asm_is_accepted_by_internal_assembler(self) -> None:
        charset = bytearray(C64_CHARACTER_FILE_SIZE)
        c64_charset_set_character_rows(
            charset,
            0x01,
            (0x3C, 0x42, 0xA5, 0x81, 0xA5, 0x99, 0x42, 0x3C),
        )
        program = assemble_mos6510_source(
            ".nostub\n.org $2000\n" + format_c64_charset_asm(charset)
        )
        self.assertEqual(program.load_address, 0x2000)
        self.assertEqual(program.end_address, 0x27FF)
        self.assertEqual(len(program.prg), 2050)


class C64CharacterEditorIntegrationTests(unittest.TestCase):
    def test_gui_exposes_editor_action_and_raw_charset_extensions(self) -> None:
        source = GUI_SOURCE.read_text(encoding="utf-8")
        self.assertIn("class C64CharacterEditorDialog", source)
        self.assertIn("class CharacterPixelGrid", source)
        self.assertIn('"C64 Character-Editor …"', source)
        self.assertIn('"CHR": {".chr", ".charset"}', source)
        self.assertIn('path.suffix.lower() in {".chr", ".charset"}', source)


if __name__ == "__main__":
    unittest.main()
