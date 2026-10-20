"""Stage 411: Verify actual machine-code KERNAL SETNAM pointers, not only names.

Run: python -m unittest -v test_stage411_c64_setnam_pointer
"""
import ast
import unittest
from pathlib import Path
from c64basic.compiler import compile_basic_to_assembly
from c64_d64_disk import build_1541_d64, _offset
from c64_vice_assets import c64_vice_sprite_program
from test_stage395_vice_context import make_namespace


class Stage411KernalPointerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ns = make_namespace()
        ns['ast'] = ast
        cls.assemble = staticmethod(ns['assemble_mos6510_source'])

    def compiled(self, source):
        output = compile_basic_to_assembly(source).assembly
        return output, self.assemble(output)

    @staticmethod
    def pointer_at_setnam(prg):
        """Decode the LDX #low; LDY #high directly preceding JSR $FFBD."""
        i = prg.find(b'\x20\xbd\xff')
        if i < 4:
            raise AssertionError('JSR SETNAM nicht gefunden')
        if prg[i-4] != 0xa2 or prg[i-2] != 0xa0:
            raise AssertionError('SETNAM hat keine sofortigen X/Y-Adressbytes')
        return prg[i-3] | (prg[i-1] << 8)

    def test_literal_setnam_points_to_real_name_in_prg(self):
        asm, program = self.compiled('10 LOAD "sprites.spr",8,1\n20 END')
        literal = program.prg.index(b'\x0bSPRITES.SPR')
        expected = program.load_address + literal - 2 + 1
        self.assertEqual(self.pointer_at_setnam(program.prg), expected)
        self.assertEqual(program.prg[literal + 1:literal+12], b'SPRITES.SPR')
        self.assertIn('    ldx #<(', asm)
        self.assertIn('    ldy #>(', asm)
        self.assertNotIn('ldy #>__basic_string_3+1', asm)

    def test_variable_setnam_points_to_string_expression_data(self):
        asm, program = self.compiled('10 N$="sprites.spr"\n20 LOAD N$,8,1\n30 END')
        self.assertEqual(self.pointer_at_setnam(program.prg), program.symbols['__basic_string_expr']+1)

    def test_open_filename_setnam_points_to_string_expression_data(self):
        asm, program = self.compiled('10 OPEN 1,8,2,"sprites.spr"\n20 END')
        self.assertEqual(self.pointer_at_setnam(program.prg), program.symbols['__basic_string_expr']+1)

    def test_input_numeric_field_pointer_points_to_buffer_data(self):
        asm, program = self.compiled('10 INPUT X\n20 END')
        self.assertIn('    lda #<(__basic_field_buffer+1)', asm)
        self.assertIn('    lda #>(__basic_field_buffer+1)', asm)
        addr = program.symbols['__basic_field_to_float_nonempty']
        o = addr - program.load_address + 2
        seq = program.prg[o:o+12]
        self.assertEqual(seq[0], 0xa9)  # LDA #low
        self.assertEqual(seq[2:4], b'\x85\x22')  # STA $22
        self.assertEqual(seq[4], 0xa9) # LDA #high
        self.assertEqual(seq[6:8], b'\x85\x23')  # STA $23
        self.assertEqual(seq[1] | seq[5] << 8, program.symbols['__basic_field_buffer']+1)

    def test_assembler_expression_high_after_addition_page_boundary(self):
        source = '.org $10FB\n.nostub\n lda #>(value+1)\n nop\nvalue: .byte $00\n'
        image = self.assemble(source).prg
        self.assertEqual(image[2:4], b'\xa9\x10')  # ($10FE + 1) = $10FF
        # Regression proof: the old unparenthesized form is *not* equivalent.
        old = self.assemble(source.replace('>(value+1)', '>value+1')).prg
        self.assertNotEqual(old[3], image[3])

    def test_exact_user_sprite_program_disk_filename_and_pointer(self):
        source = (Path(__file__).parent / 'STAGE410_C64_LOAD_FILENAME_PETSCII.md').read_text(encoding='utf-8')
        self.assertIn('LOAD "sprites.spr",8,1', source)
        basic = '\n'.join((
            '40 IF F = 1 THEN GOTO 60', '50 LOAD "sprites.spr",8,1',
            '60 F = 1', '85 POKE 2040,192', '100 POKE 53248,100',
            '110 POKE 53249,100', '120 POKE 53287,2',
            '130 POKE 53276,0', '140 POKE 53269,1', '150 END',
        ))
        asm, p = self.compiled(basic)
        b = p.prg
        position = b.index(b'\x0bSPRITES.SPR')
        self.assertEqual(self.pointer_at_setnam(b), p.load_address + position - 1)
        spr = c64_vice_sprite_program(bytes((0x00,0x30)) + bytes(range(64))*2)
        d64 = build_1541_d64([('SPRITE_A', b), ('sprites.spr', spr)])
        directory_entry = _offset(18,1) + 32
        self.assertEqual(d64[directory_entry+5:directory_entry+16], b'SPRITES.SPR')


if __name__ == '__main__':
    unittest.main()
