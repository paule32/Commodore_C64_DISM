"""Stage 416: 16-Farben-Roundtrip, Dateisicherheit und Menürouting."""
import ast
import tempfile
import unittest
from pathlib import Path

from c64_bitmap_sprite import (
    MAGIC, TRANSPARENT, decode_bitmap_sprites, encode_bitmap_sprites,
    empty_sprite, resized_sprite, save_bitmap_sprites, load_bitmap_sprites,
)

ROOT = Path(__file__).parent
SRC = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
EDITOR = (ROOT / 'c64_bitmap_sprite_editor.py').read_text(encoding='utf-8')
TREE = ast.parse(SRC)


class BitmapSpriteTests(unittest.TestCase):
    def test_file_header_and_16_colors(self):
        image = empty_sprite()
        for i in range(16):
            image[i] = i
        image[16] = TRANSPARENT
        binary = encode_bitmap_sprites([image], 24, 21)
        self.assertEqual(binary[:8], MAGIC)
        self.assertEqual(binary[8:14], bytes([24, 0, 21, 0, 1, 0]))
        sprites, width, height = decode_bitmap_sprites(binary)
        self.assertEqual((width, height), (24, 21))
        self.assertEqual(sprites[0], image)
        self.assertEqual(len(binary), 14 + 24 * 21)
        self.assertNotIn(b'{', binary[:14])

    def test_multiple_sprites_roundtrip(self):
        sprites = [empty_sprite(), empty_sprite()]
        sprites[0][5] = 15
        sprites[1][0] = 0
        sprites[1][-1] = 14
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / 'figur.bmsprite'
            save_bitmap_sprites(path, sprites, 24, 21)
            restored, width, height = load_bitmap_sprites(path)
            self.assertEqual(restored, sprites)
            self.assertEqual((width, height), (24, 21))

    def test_resize_preserves_overlap(self):
        pixels = bytearray((1, 2, 3, 4, 5, 6))
        bigger = resized_sprite(pixels, 3, 2, 4, 3)
        self.assertEqual(bigger, bytearray((1, 2, 3, 255, 4, 5, 6, 255, 255, 255, 255, 255)))
        smaller = resized_sprite(bigger, 4, 3, 2, 2)
        self.assertEqual(smaller, bytearray((1, 2, 4, 5)))

    def test_reject_corrupt_file(self):
        original = encode_bitmap_sprites([empty_sprite()], 24, 21)
        for data in (original[:-1], original + b'\0', b'{}', b'WRONGMAG' + original[8:]):
            with self.assertRaises(ValueError):
                decode_bitmap_sprites(data)
        corrupted = bytearray(original)
        corrupted[-1] = 16
        with self.assertRaises(ValueError):
            decode_bitmap_sprites(corrupted)

    def test_editor_contains_input_and_persistence(self):
        for token in ('class C64BitmapSpriteCanvas', 'class C64BitmapSpriteEditorDialog',
                      'Qt.RightButton', 'self.canvas.brush',
                      'save_bitmap_sprites', 'load_bitmap_sprites',
                      'self._confirm_discard()', 'self.project_owner._register_c64_sprite_editor_file'):
            self.assertIn(token, EDITOR)
        ast.parse(EDITOR)

    def test_context_menu_and_main_menu_order(self):
        context = SRC.index('if kind == PROJECT_NODE_C64_SPRITES_ROOT:', SRC.index('def _show_project_c64_sprites_menu'))
        self.assertLess(SRC.index('menu.addAction("Neues Bitmap Sprite")', context),
                        SRC.index('menu.addAction("Neues Sprite")', context))
        main = SRC.index('if profile_key == "c64":', SRC.index('def _populate_new_document_menu'))
        self.assertLess(SRC.index('submenu.addAction(self.new_c64_bitmap_sprite_action)', main),
                        SRC.index('submenu.addAction(self.new_c64_sprite_builder_action)', main))
        self.assertIn('"Bitmap Sprite Editor", self.new_c64_bitmap_sprite_project', SRC)

    def test_dock_and_project_tree_wired(self):
        for token in ('"bitmap_sprites": (', 'C64BitmapSpriteEditorDialog, "C64 Bitmap Sprite Editor"',
                      '"c64_bitmap_sprite_editor_dock"',
                      '".bmsprite", ".bmspr"', '"bitmap" if bitmap else "hardware"',
                      '"bitmap_sprites" if bitmap else "sprites"',
                      'self._add_project_c64_sprite_entry(bitmap=True)',
                      'if kind in ("sprites", "bitmap_sprites")'):
            self.assertIn(token, SRC)
        self.assertIn('"c64_bitmap_sprite_editor"', (ROOT/'d64_dism.spec').read_text())
        self.assertIn('"c64_bitmap_sprite"', (ROOT/'d64_dism.spec').read_text())


if __name__ == '__main__':
    unittest.main()
