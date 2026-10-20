"""Stage 410: Filename byte equality across BASIC compiler / D64 / VICE keyboard feed.

Run: python -m unittest -v test_stage410_c64_load_filename_petscii
"""
import ast
import re
import unittest
from pathlib import Path

from c64basic.compiler import (
    _petscii_bytes, _petscii_filename_bytes, compile_basic_to_assembly,
)
from c64_d64_disk import _cbm_name, _offset, build_1541_d64
from test_stage395_vice_context import make_namespace, extract, SOURCE


class Stage410PetsciiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        asm_ns = make_namespace()
        asm_ns['ast'] = ast
        cls.assemble = staticmethod(asm_ns['assemble_mos6510_source'])

    @staticmethod
    def string_blobs(assembly):
        items = []
        for line in assembly.splitlines():
            match = re.fullmatch(r'(__basic_string_\d+): \.byte (.+)', line)
            if match:
                items.append((match.group(1), bytes(int(x.strip().lstrip('$'), 16)
                                                    for x in match.group(2).split(','))))
        return items

    def test_ascii_lowercase_matches_d64_directory_petscii(self):
        asm = compile_basic_to_assembly('10 LOAD "sprites.spr",8,1\n20 END').assembly
        blobs = self.string_blobs(asm)
        self.assertIn(b'\x0bSPRITES.SPR', [v for _, v in blobs])
        prg = self.assemble(asm).prg
        self.assertIn(b'\x0bSPRITES.SPR', prg)
        self.assertNotIn(b'\x0bsprites.spr', prg)
        disk = build_1541_d64([('sprites.spr', b'\x00\x30' + bytes(64))])
        entry = disk[_offset(18, 1) + 5:_offset(18, 1) + 21]
        self.assertEqual(prg[prg.index(b'\x0bSPRITES.SPR') + 1:][:11],
                         entry[:11])
        self.assertEqual(_cbm_name('sprites.spr'), b'SPRITES.SPR')

    def test_other_strings_are_not_corrupted(self):
        asm = compile_basic_to_assembly(
            '10 PRINT "sprites.spr"\n20 LOAD "sprites.spr",8,1\n30 END'
        ).assembly
        strings = [value for _, value in self.string_blobs(asm)]
        self.assertIn(b'\x0bsprites.spr', strings)
        self.assertIn(b'\x0bSPRITES.SPR', strings)
        self.assertNotEqual(strings.index(b'\x0bsprites.spr'), strings.index(b'\x0bSPRITES.SPR'))
        self.assertIn(b'\x0bsprites.spr', self.assemble(asm).prg)

    def test_direct_petscii_input_is_not_uppercased(self):
        self.assertEqual(_petscii_filename_bytes('ab\ue073.'), b'ABs.')
        self.assertEqual(_petscii_bytes('sprites.spr'), b'sprites.spr')

    def test_dynamic_filename_uses_copy_normalizer(self):
        asm = compile_basic_to_assembly(
            '10 N$="sprites.spr"\n20 LOAD N$,8,1\n30 END'
        ).assembly
        self.assertIn('    jsr __basic_load_normalize_name\n    lda __basic_string_expr', asm)
        self.assertIn('__basic_load_normalize_name:', asm)
        self.assertIn('    sta __basic_string_expr+1,y', asm)
        self.assertIn(b'\x0bsprites.spr', self.assemble(asm).prg)
        # Runtime acts only on an expression copy, not on variable N$.
        self.assertNotIn('    sta __basic_str_N', asm)

    def test_existing_uppercase_unchanged_and_deduped(self):
        asm = compile_basic_to_assembly(
            '10 LOAD "SPRITES.SPR",8,1\n20 LOAD "sprites.spr",8,1\n30 END'
        ).assembly
        self.assertEqual([v for _, v in self.string_blobs(asm)].count(b'\x0bSPRITES.SPR'), 1)
        self.assertIn(b'\x0bSPRITES.SPR', self.assemble(asm).prg)

    def test_vice_keyboard_feed_has_same_letter_bytes(self):
        fn=extract('c64_basic_text_to_petscii')
        ns={'ViceBinaryMonitorError': type('ViceBinaryMonitorError',(Exception,), {})}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])),str(SOURCE),'exec'),ns)
        wire = ns['c64_basic_text_to_petscii']('50 LOAD "sprites.spr",8,1\r')
        self.assertIn(b'SPRITES.SPR', wire)
        self.assertNotIn(b'sprites.spr', wire)

    def test_user_sprite_program_compiles_and_disk_lookup_matches(self):
        source = (Path(__file__).parent / 'test_stage408_fac_uint16_load_poke.py').read_text(encoding='utf8')
        self.assertIn('LOAD "sprites.spr",8,1', source)
        program_text = (
            '40 IF F = 1 THEN GOTO 60\n50 LOAD "sprites.spr",8,1\n'
            '60 F = 1\n85 POKE 2040,192\n100 POKE 53248,100\n'
            '110 POKE 53249,100\n120 POKE 53287,2\n'
            '130 POKE 53276,0\n140 POKE 53269,1\n150 END\n'
        )
        asm = compile_basic_to_assembly(program_text).assembly
        prg = self.assemble(asm).prg
        self.assertIn(b'\x0bSPRITES.SPR', prg)
        disk = build_1541_d64([('Sprite_A', prg), ('sprites.spr', b'\x00\x30' + bytes(128))])
        self.assertEqual(disk[_offset(18,1) + 32 + 5:_offset(18,1) + 32 + 16],b'SPRITES.SPR')

if __name__ == '__main__':
    unittest.main()
