"""Stage 404: VIC-II-Binaersprites statt JSON beim Speichern im GUI.

Diese Tests extrahieren die echten Save/Load-Methoden per AST; PyQt5 muss
nicht installiert sein. Legacy-JSON bleibt ausschliesslich Importformat.
"""
import ast
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from c64_sprite_codec import (
    decode_raw_sprites, encode_raw_sprites, default_sprite_meta, save_document,
    set_sprite_pixel,
)

ROOT = Path(__file__).parent
CODE = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
TREE = ast.parse(CODE)
EDITOR = next(n for n in ast.walk(TREE)
              if isinstance(n, ast.ClassDef) and n.name == 'C64SpriteEditorDialog')
METHODS = {node.name: node for node in EDITOR.body
           if isinstance(node, ast.FunctionDef)}


def methods(*names, namespace=None):
    ns = {'Path': Path, 'encode_raw_sprites': encode_raw_sprites,
          'decode_raw_sprites': decode_raw_sprites,
          'default_sprite_meta': default_sprite_meta,
          'C64_CHARACTER_PALETTE': [('White', '#FFFFFF')]*16}
    if namespace:
        ns.update(namespace)
    nodes = [METHODS[name] for name in names]
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                 str(ROOT / 'd64_dism.py'), 'exec'), ns)
    return ns


class Dialog:
    def __init__(self, choice=None):
        self.path = choice
        self.errors = []

    def getSaveFileName(self, *args):
        return (str(self.path), 'C64 Sprite-Rohdaten (*.spr)') if self.path else ('', '')

    def critical(self, *args):
        self.errors.append(args)


class NativeSpriteStorageTests(unittest.TestCase):
    def owner(self, initial=None, size=64):
        class Owner: pass
        owner = Owner()
        owner.initial_directory = Path('/unused')
        owner.current_path = initial
        owner.record_size = size
        owner.sprites = [bytearray(size) for _ in range(2)]
        owner.metas = [default_sprite_meta() for _ in range(2)]
        owner.palette_entries = [('White', '#FFFFFF')]*16
        owner.path_label = SimpleNamespace(setText=MagicMock())
        owner._mark_modified = MagicMock()
        owner.project_owner = None
        return owner

    def test_gui_default_is_raw_spr_not_json(self):
        self.assertIn("self.initial_directory / 'sprites.spr'", CODE)
        self.assertIn('title = f"Sprite_{number}.spr"', CODE)
        self.assertNotIn('save_document(self.current_path', METHODS['save'].__dict__.get('str', ''))
        self.assertNotIn('save_document(', ast.unparse(METHODS['save']))
        self.assertIn('encode_raw_sprites(', ast.unparse(METHODS['save']))

    def test_native_saving_bytes_without_header(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'hero.spr'
            actor = self.owner(target)
            actor.sprites[0][-1] = 0xB4
            set_sprite_pixel(actor.sprites[0], 23, 20, 1)
            ns = methods('save', namespace={'QMessageBox': Dialog()})
            self.assertTrue(ns['save'](actor))
            raw = target.read_bytes()
            self.assertEqual(len(raw), 128)
            self.assertEqual(raw[63], 0xB4)
            self.assertEqual(raw[60+2], 1)
            self.assertEqual(raw[:2], bytes([0,0]))
            self.assertFalse(raw.startswith(b'{'))
            parsed, rec = decode_raw_sprites(raw)
            self.assertEqual(rec, 64)
            self.assertEqual(parsed, actor.sprites)

    def test_legacy_json_is_not_overwritten_by_save(self):
        with tempfile.TemporaryDirectory() as d:
            legacy = Path(d) / 'legacy.c64sprite'
            legacy.write_text('{"format":"legacy"}', encoding='utf-8')
            actor = self.owner(legacy)
            actor.save_as = MagicMock(return_value=True)
            ns = methods('save', namespace={'QMessageBox': Dialog()})
            self.assertTrue(ns['save'](actor))
            actor.save_as.assert_called_once()
            self.assertEqual(legacy.read_text(encoding='utf-8'), '{"format":"legacy"}')

    def test_first_save_as_creates_spr(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'sprites'
            chooser = Dialog(target)
            actor = self.owner()
            ns = methods('save_as', 'save', namespace={'QFileDialog':chooser, 'QMessageBox':chooser})
            actor.save = lambda: ns['save'](actor)
            self.assertTrue(ns['save_as'](actor))
            self.assertEqual(actor.current_path, target.with_suffix('.spr'))
            self.assertEqual(target.with_suffix('.spr').stat().st_size, 128)

    def test_json_extension_rejected_without_writing(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'sprite.c64sprite'
            chooser = Dialog(target)
            actor = self.owner()
            ns = methods('save_as', namespace={'QFileDialog':chooser, 'QMessageBox':chooser})
            self.assertFalse(ns['save_as'](actor))
            self.assertTrue(chooser.errors)
            self.assertFalse(target.exists())

    def test_raw63_64_roundtrips(self):
        for size in (63, 64):
            sprites = [bytes(range(size)), bytes((255 - i) for i in range(size))]
            raw = encode_raw_sprites(sprites, size)
            got, detected = decode_raw_sprites(raw)
            self.assertEqual(detected, size)
            self.assertEqual([bytes(x) for x in got], sprites)

    def test_legacy_json_import_still_available(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'legacy.c64sprite'
            save_document(p, [bytearray(64)], [default_sprite_meta()],
                          [(str(i), '#FFFFFF') for i in range(16)])
            self.assertTrue(p.read_bytes().startswith(b'{'))
            self.assertIn("path.suffix.casefold() == '.c64sprite'", ast.unparse(METHODS['load_file']))
            self.assertIn('load_document(path)', ast.unparse(METHODS['load_file']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
