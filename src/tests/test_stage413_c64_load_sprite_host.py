"""Stage 413 regression: distinct disk LOAD vs host LOAD SPRITE."""
from __future__ import annotations
import ast
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from c64basic import (
    C64BasicError, compile_basic_to_assembly,
    c64_basic_sprite_command, load_c64_basic_sprite_resource,
)
from c64_vice_assets import c64_basic_sprite_load_names
from test_stage395_vice_context import make_namespace


class Stage413HostSpriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ns = make_namespace()
        ns['ast'] = ast
        cls.assembler = staticmethod(ns['assemble_mos6510_source'])

    def test_command_with_default_hex_and_decimal_address(self):
        self.assertEqual(c64_basic_sprite_command('10 LOAD SPRITE "demo.spr"'), (10, 'demo.spr', 0x3000))
        self.assertEqual(c64_basic_sprite_command('LOADSPRITE "demo.spr",$3040'), (None, 'demo.spr', 0x3040))
        self.assertEqual(c64_basic_sprite_command('LOAD SPRITE "demo.spr",12352'), (None, 'demo.spr', 0x3040))
        self.assertIsNone(c64_basic_sprite_command('LOAD "demo.spr",8,1'))

    def test_binary_64_byte_and_prepared_header(self):
        with TemporaryDirectory() as td:
            directory = Path(td)
            data = bytes(range(64)) + bytes(reversed(range(64)))
            (directory / 'Sprite.SPR').write_bytes(data)
            resource = load_c64_basic_sprite_resource('sprite.spr', str(directory/'test.bas'))
            self.assertEqual(resource.data, data)
            self.assertEqual(resource.address, 0x3000)
            (directory / 'prepared.spr').write_bytes(b'\x00\x30' + data)
            prepared = load_c64_basic_sprite_resource('prepared.spr', str(directory/'test.bas'))
            self.assertEqual(prepared.data, data)

    def test_raw_63_byte_padding(self):
        with TemporaryDirectory() as td:
            directory = Path(td)
            raw = bytes(range(63))
            (directory/'short.spr').write_bytes(raw)
            data = load_c64_basic_sprite_resource('short.spr', str(directory/'a.bas')).data
            self.assertEqual(data, raw + b'\x00')

    def test_missing_invalid_and_address_mismatch(self):
        with TemporaryDirectory() as td:
            directory = Path(td)
            (directory/'bad.spr').write_bytes(b'\x00\x30' + bytes(128))
            for name, address in [('missing.spr', 0x3000), ('bad.spr', 0x3040), ('../bad.spr', 0x3000), ('bad.spr', 0x3001)]:
                with self.subTest(name=name, address=address), self.assertRaises(C64BasicError):
                    load_c64_basic_sprite_resource(name, str(directory/'prog.bas'), address=address)

    def test_compiler_embeds_raw_exactly_without_kernal_load(self):
        with TemporaryDirectory() as td:
            directory = Path(td)
            raw = bytes(range(64)) + bytes(range(64))
            (directory/'sprites.spr').write_bytes(raw)
            asm = compile_basic_to_assembly(
                '10 LOAD SPRITE "sprites.spr"\n20 POKE 2040,192\n30 END',
                filename=str(directory/'sprite.bas'),
            ).assembly
            self.assertIn('jsr __basic_sprite_copy', asm)
            self.assertIn('__basic_sprite_resource_1_data:', asm)
            self.assertNotIn('jsr $FFD5', asm)
            prg = self.assembler(asm)
            data_address = prg.symbols['__basic_sprite_resource_1_data']
            index = data_address - prg.load_address + 2
            self.assertEqual(prg.prg[index:index+len(raw)], raw)
            self.assertGreater(prg.symbols['__basic_sprite_pages'], prg.symbols['__basic_image_end'])
            self.assertLess(prg.symbols['__basic_image_end'], 0x3000)
            self.assertLess(prg.symbols['__basic_cbss_end'], 0x3000)

    def test_compiler_3040_for_one_sprite(self):
        with TemporaryDirectory() as td:
            path = Path(td)/'test.spr'; path.write_bytes(bytes(range(64)))
            asm = compile_basic_to_assembly('10 LOAD SPRITE "test.spr",$3040\n20 END', filename=str(path.with_suffix('.bas'))).assembly
            self.assertIn('    lda #$40\n    sta $FD\n    lda #$30\n    sta $FE', asm)
            self.assertIn('    lda #$40\n    sta __basic_sprite_rem', asm)
            self.assembler(asm)

    def test_disk_load_remains_separate(self):
        self.assertEqual(c64_basic_sprite_load_names('10 LOAD "other.spr",8,1'), ('other.spr',))
        self.assertEqual(c64_basic_sprite_load_names('10 LOAD SPRITE "other.spr"'), ())
        source = compile_basic_to_assembly('10 LOAD "other.spr",8,1\n20 END').assembly
        self.assertIn('jsr $FFD5', source)
        self.assertNotIn('jsr __basic_sprite_copy', source)

    def test_debug_path_uses_monitor(self):
        code = (Path(__file__).parent/'d64_dism.py').read_text(encoding='utf-8')
        self.assertIn('client.load_sprite_resource(sprite_resource.address, sprite_resource.data)', code)
        self.assertIn('client.feed_basic_line(f\'{line_number} REM LOAD SPRITE HOST\')', code)
        self.assertIn('self.write_memory(address, payload)', code)


if __name__ == '__main__':
    unittest.main()
