"""Stage 397: echte VIC-II-Farbregister statt 16 Farben pro Bitmap-Pixel."""
import ast
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from c64_sprite_codec import (
    default_sprite_meta, sprite_pixel, set_sprite_pixel,
    synchronize_shared_sprite_colors, vicii_sprite_color_registers,
    save_document, load_document,
)

ROOT = Path(__file__).resolve().parent


class VICIIHardwareColorsTests(unittest.TestCase):
    def test_all_sixteen_sprite_colors_selectable(self):
        for color in range(16):
            meta = default_sprite_meta()
            meta['sprite_color'] = color
            self.assertEqual(vicii_sprite_color_registers(meta)[0xD027], color)

    def test_hires_hardware_color_is_only_one_register(self):
        meta = default_sprite_meta()
        meta['sprite_color'] = 14
        self.assertEqual(vicii_sprite_color_registers(meta, 3), {0xD02A: 14})
        pixels = bytearray(63)
        set_sprite_pixel(pixels, 23, 20, 1, 'hires')
        self.assertEqual(sprite_pixel(pixels, 23, 20, 'hires'), 1)

    def test_multicolor_three_visible_colors_and_transparency(self):
        meta = default_sprite_meta()
        meta.update(mode='multicolor', width=12, multicolor_1=4,
                    sprite_color=7, multicolor_2=15)
        self.assertEqual(vicii_sprite_color_registers(meta, 0),
                         {0xD027: 7, 0xD025: 4, 0xD026: 15})
        pixels = bytearray(63)
        for x, code in enumerate((0, 1, 2, 3)):
            set_sprite_pixel(pixels, x, 0, code, 'multicolor')
        self.assertEqual(pixels[0], 0x1b)

    def test_invalid_hardware_sprite_number(self):
        for index in (-1, 8, '1'):
            with self.assertRaises(ValueError):
                vicii_sprite_color_registers(default_sprite_meta(), index)

    def test_global_vicii_registers_apply_to_all_sprites(self):
        metas = [default_sprite_meta() for _ in range(3)]
        metas[1]['sprite_color'] = 12
        metas[2]['sprite_color'] = 14
        self.assertTrue(synchronize_shared_sprite_colors(metas,
                             multicolor_1=0, multicolor_2=15))
        self.assertEqual([m['multicolor_1'] for m in metas], [0] * 3)
        self.assertEqual([m['multicolor_2'] for m in metas], [15] * 3)
        self.assertEqual([m['sprite_color'] for m in metas], [1, 12, 14])
        self.assertFalse(synchronize_shared_sprite_colors(metas,
                             multicolor_1=0, multicolor_2=15))
        with self.assertRaises(ValueError):
            synchronize_shared_sprite_colors(metas, multicolor_1=16)

    def test_legacy_document_conflicting_shared_colors_normalized(self):
        palette = [(str(i), f'#{i:02X}{i:02X}{i:02X}') for i in range(16)]
        metas = [default_sprite_meta(), default_sprite_meta()]
        metas[0].update(multicolor_1=2, multicolor_2=6, sprite_color=14)
        metas[1].update(multicolor_1=9, multicolor_2=7, sprite_color=5)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'sprites.c64sprite'
            save_document(path, [bytearray(64), bytearray(64)], metas, palette)
            data = json.loads(path.read_text(encoding='utf-8'))
            # Save always serializes hardware-compatible common register values.
            self.assertEqual(data['sprites'][1]['settings']['multicolor_1'], 2)
            self.assertEqual(data['sprites'][1]['settings']['multicolor_2'], 6)
            # In-memory inputs are not modified during serialization.
            self.assertEqual(metas[1]['multicolor_1'], 9)
            # Also accept and normalize an older non-hardware-compatible document.
            data['sprites'][1]['settings']['multicolor_1'] = 10
            path.write_text(json.dumps(data), encoding='utf-8')
            sprites, loaded_metas, loaded_palette, rec_size = load_document(path)
            self.assertEqual(loaded_metas[1]['multicolor_1'], 2)
            self.assertEqual(loaded_metas[1]['sprite_color'], 5)
            self.assertEqual(rec_size, 64)


class SpriteEditorWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src = (ROOT / 'd64_dism.py').read_text('utf-8')
        cls.src = src
        tree = ast.parse(src)
        editor = next(n for n in ast.walk(tree)
                      if isinstance(n, ast.ClassDef) and n.name == 'C64SpriteEditorDialog')
        cls.methods = {n.name: n for n in editor.body if isinstance(n, ast.FunctionDef)}

    def test_ui_shows_three_hardware_registers_and_16_colors(self):
        for token in ('MC 1 · $D025 (alle Sprites)',
                      'Sprite · $D027 + Nr.',
                      'MC 2 · $D026 (alle Sprites)',
                      'combo.setItemData(i, QColor(rgb), Qt.DecorationRole)',
                      'for i in range(16):'):
            self.assertIn(token, self.src)

    def test_multicolor_register_edit_updates_all_sprites(self):
        # Exercise actual class method without requiring Qt installed on CI.
        method = self.methods['_set_vicii_color']
        copy = ast.FunctionDef(name=method.name, args=method.args, body=method.body,
                               decorator_list=[], returns=method.returns, type_comment=None)
        ns = {'synchronize_shared_sprite_colors': synchronize_shared_sprite_colors}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[copy], type_ignores=[])),
                     '<sprite_methods>', 'exec'), ns)
        metas = [default_sprite_meta(), default_sprite_meta()]
        metas[1]['sprite_color'] = 9
        redraws = []
        modified = []
        editor_stub = SimpleNamespace(
            metas=metas,
            _current_meta=lambda: metas[0],
            _mark_modified=lambda: modified.append(True),
            _update_palette_buttons=lambda: redraws.append(True),
        )
        ns['_set_vicii_color'](editor_stub, 'multicolor_1', 15)
        self.assertEqual([m['multicolor_1'] for m in metas], [15, 15])
        ns['_set_vicii_color'](editor_stub, 'sprite_color', 6)
        self.assertEqual([m['sprite_color'] for m in metas], [6, 9])
        self.assertEqual(len(modified), 2)
        self.assertEqual(len(redraws), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
