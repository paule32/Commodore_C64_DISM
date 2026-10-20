"""Regressionstests Stage 396 – ohne Abhängigkeit von PyQt5."""
import ast
import tempfile
import unittest
from pathlib import Path

from c64_sprite_codec import (
    default_sprite_meta, normalize_meta, sprite_pixel, set_sprite_pixel,
    decode_raw_sprites, encode_raw_sprites, palette_from_bytes,
    save_document, load_document,
)

ROOT = Path(__file__).parent


class SpriteCodecTests(unittest.TestCase):
    def test_hires_pixel_bits(self):
        data = bytearray(64)
        for x, y in ((0, 0), (23, 0), (8, 20), (16, 3)):
            self.assertTrue(set_sprite_pixel(data, x, y, 1))
            self.assertEqual(sprite_pixel(data, x, y), 1)
        self.assertEqual(data[0], 0x80)
        self.assertEqual(data[2], 0x01)
        self.assertEqual(data[60+1], 0x80)
        self.assertTrue(set_sprite_pixel(data, 0, 0, 0))
        self.assertEqual(sprite_pixel(data, 0, 0), 0)

    def test_multicolor_two_bit_encoding(self):
        data = bytearray(63)
        for x, v in enumerate((0, 1, 2, 3)):
            set_sprite_pixel(data, x, 0, v, 'multicolor')
        self.assertEqual(data[0], 0b00011011)
        for x in range(4):
            self.assertEqual(sprite_pixel(data, x, 0, 'multicolor'), x)
        set_sprite_pixel(data, 3, 0, 0, 'multicolor')
        self.assertEqual(data[0], 0b00011000)

    def test_raw63_64_round_trip(self):
        for size in (63, 64):
            blob = bytes(range(size)) * 3
            sprites, detected = decode_raw_sprites(blob)
            self.assertEqual(detected, size)
            self.assertEqual(encode_raw_sprites(sprites, size), blob)

    def test_raw64_last_byte_preserved(self):
        blob = bytes(63) + b'\xB4'
        sprites, size = decode_raw_sprites(blob)
        set_sprite_pixel(sprites[0], 12, 12, 1)
        self.assertEqual(encode_raw_sprites(sprites, size)[63], 0xB4)

    def test_invalid_raw_rejected(self):
        for value in (b'', bytes(62), bytes(65)):
            with self.assertRaises(ValueError):
                decode_raw_sprites(value)

    def test_palette_16_colors(self):
        rgb = bytes(range(48))
        colors = palette_from_bytes(rgb, [f'Farbe{i}' for i in range(16)])
        self.assertEqual(len(colors), 16)
        self.assertEqual(colors[0][1], '#000102')
        self.assertEqual(colors[-1][1], '#2D2E2F')
        with self.assertRaises(ValueError):
            palette_from_bytes(bytes(47), [str(i) for i in range(16)])

    def test_meta_validation(self):
        for mode, width in (('hires', 24), ('multicolor', 12)):
            m = default_sprite_meta()
            m.update(mode=mode, width=width, expand_x=True, expand_y=True)
            self.assertEqual(normalize_meta(m)['width'], width)
        m = default_sprite_meta()
        m.update(mode='multicolor', width=24)
        with self.assertRaises(ValueError):
            normalize_meta(m)

    def test_metadata_json_roundtrip(self):
        palette = [(f'Farbe{i}', f'#{i:02X}01A0') for i in range(16)]
        bitmaps = [bytearray(64) for _ in range(2)]
        bitmaps[0][-1] = 0xB1
        set_sprite_pixel(bitmaps[0], 23, 20, 1)
        set_sprite_pixel(bitmaps[1], 10, 20, 3, 'multicolor')
        one = default_sprite_meta()
        two = default_sprite_meta()
        two.update(mode='multicolor', width=11, height=15, sprite_color=10,
                   expand_x=True, expand_y=True)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 's.c64sprite'
            save_document(path, bitmaps, [one, two], palette)
            sprites, metas, restored_palette, record_size = load_document(path)
            self.assertEqual(sprites, bitmaps)
            self.assertEqual(metas[1], two)
            self.assertEqual(restored_palette, [[name, color] for name, color in palette])
            self.assertEqual(record_size, 64)

    def test_bad_json_file_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 's.c64sprite'
            path.write_text('{"format":"unknown"}', encoding='utf-8')
            with self.assertRaises(ValueError):
                load_document(path)


class SpriteIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'd64_dism.py').read_text('utf-8')
        cls.tree = ast.parse(cls.source)

    def test_menu_action(self):
        self.assertIn('"Sprite Editor", self.new_c64_sprite_project', self.source)
        self.assertIn('submenu.addAction(self.new_c64_sprite_builder_action)', self.source)

    def test_dock_registration(self):
        self.assertIn('"sprites": (\n                    C64SpriteEditorDialog', self.source)
        self.assertIn('"c64_sprite_builder_dock"', self.source)
        self.assertIn('self._show_c64_tool_dock("sprites", initial_path=initial_path)', self.source)
        self.assertIn('C64SpriteEditorDialog(QWidget)', self.source)

    def test_project_tree_sprite_extensions(self):
        self.assertIn('".c64sprite"', self.source)
        self.assertIn('"sprites": self.show_sprite_editor', self.source)


if __name__ == '__main__':
    unittest.main(verbosity=2)
