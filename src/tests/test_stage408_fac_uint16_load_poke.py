"""Stage 408: FAC -> uint16 adapter for KERNAL LOAD / VIC-II POKE.

Run from project root: python -m unittest -v test_stage408_fac_uint16_load_poke
"""
from pathlib import Path
import unittest
import ast

from c64basic.compiler import compile_basic_to_assembly
from test_stage395_vice_context import make_namespace


class Stage408FacTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ns = make_namespace()
        ns['ast'] = ast
        cls.asm = staticmethod(ns['assemble_mos6510_source'])

    def test_helper_uses_qint_and_low_byte_first(self):
        assembly = compile_basic_to_assembly('10 POKE 53269,1\n20 END').assembly
        helper = assembly.split('__basic_fac_to_int:\n', 1)[1].split('\n__basic_int_to_fac:', 1)[0]
        self.assertEqual(helper.splitlines(), [
            '    jsr $BC9B', '    lda $65', '    ldx $64', '    rts',
        ])
        self.assertNotIn('jsr $B1AA', helper)
        program = self.asm(assembly)
        self.assertIn(bytes.fromhex('20 9b bc a5 65 a6 64 60'), program.prg)

    def test_sprite_load_passes_device_and_secondary_in_low_byte(self):
        assembly = compile_basic_to_assembly('10 LOAD "sprites.spr",8,1\n20 END').assembly
        self.assertIn('    sta __basic_device', assembly)
        self.assertIn('    sta __basic_secondary', assembly)
        self.assertIn('    ldx __basic_device\n    ldy __basic_secondary\n    jsr $FFBA', assembly)
        self.assertIn('    jsr $FFD5', assembly)
        program = self.asm(assembly)
        self.assertTrue(program.prg.startswith(bytes.fromhex('01 08')))

    def test_vic_registers_and_sprite_pointer_store_16bit_low_high(self):
        source = '\n'.join([ 
            '10 POKE 2040,192', '20 POKE 53248,100', '30 POKE 53249,100',
            '40 POKE 53287,2', '50 POKE 53276,0', '60 POKE 53269,1',
            '70 END',
        ])
        result = compile_basic_to_assembly(source)
        assembly = result.assembly
        self.assertEqual(assembly.count('    sta $FB\n    stx $FC'), 6)
        self.assertEqual(assembly.split('__basic_line_70:', 1)[0].count('    sta ($FB),y'), 6)
        self.assertEqual(self.asm(assembly).entry_address, 0x080D)

    def test_original_user_bas_compiles(self):
        source = ('40 IF F = 1 THEN GOTO 60\n'
                  '50 LOAD "sprites.spr",8,1\n'
                  '60 F = 1\n'
                  '85 POKE 2040,192\n'
                  '100 POKE 53248,100\n'
                  '110 POKE 53249,100\n'
                  '120 POKE 53287,2\n'
                  '130 POKE 53276,0\n'
                  '140 POKE 53269,1\n'
                  '150 END\n')
        result = compile_basic_to_assembly(source)
        prg = self.asm(result.assembly).prg
        self.assertGreater(len(prg), 100)
        self.assertIn(bytes.fromhex('20 9b bc a5 65 a6 64 60'), prg)

    def test_already_prepared_sprite_is_not_double_prepended(self):
        from c64_vice_assets import c64_vice_sprite_program
        raw = bytes((0x00, 0x30)) + bytes(128)
        self.assertEqual(c64_vice_sprite_program(raw), raw)
        self.assertEqual(len(c64_vice_sprite_program(raw)), 130)
        with self.assertRaises(ValueError):
            c64_vice_sprite_program(bytes((0x00, 0x20)) + bytes(128))

    def test_raw_sprite_loaded_at_3000_is_not_code_dependency(self):
        from c64_vice_assets import c64_vice_sprite_program
        raw = bytes(64 * 2)
        file = c64_vice_sprite_program(raw)
        self.assertEqual(len(file), 130)
        self.assertEqual(file[:2], bytes.fromhex('00 30'))

if __name__ == '__main__':
    unittest.main()
