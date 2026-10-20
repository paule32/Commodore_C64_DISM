"""Stage 401: C64 BASIC V2 LOAD via KERNAL, plus existing LOAD SCREEN.

GUI-free: python -m unittest -v test_stage401_c64_basic_load
"""
import ast
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from c64basic.compiler import C64BasicError, compile_basic_to_assembly
from test_stage395_vice_context import make_namespace


class Stage401LoadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.asm_namespace = make_namespace()
        cls.asm_namespace['ast'] = ast

    def compile_and_assemble(self, text):
        result = compile_basic_to_assembly(text, filename='test.bas')
        program = self.asm_namespace['assemble_mos6510_source'](result.assembly, filename='test.asm')
        self.assertEqual(program.entry_address, 0x080D)
        self.assertTrue(program.prg.startswith(b'\x01\x08'))
        return result

    def test_load_sprite_prg_device8_secondary1(self):
        result = self.compile_and_assemble(
            '10 IF F=1 THEN GOTO 70\n20 F=1\n30 LOAD "SPRITES",8,1\n'
            '40 PRINT "FERTIG"\n70 POKE 53269,0\n80 END\n'
        )
        asm = result.assembly
        self.assertRegex(asm, r'lda __basic_string_\d+\n    ldx #<__basic_string_\d+\+1')
        self.assertIn('    jsr $FFBD', asm)
        self.assertIn('    jsr $FFBA', asm)
        self.assertIn('    jsr $FFD5', asm)
        self.assertLess(asm.index('    jsr $FFBD'), asm.index('    jsr $FFBA'))
        self.assertLess(asm.index('    jsr $FFBA'), asm.index('    jsr $FFD5'))
        self.assertIn('    bcc __basic_load_success_', asm)
        self.assertIn('__basic_load_failed:', asm)
        self.assertIn('?LOAD ERROR ', asm)
        self.assertTrue(any('LOAD verwenden die C64-KERNAL' in note for note in result.notes))

    def test_several_loads_each_has_own_success_label(self):
        asm = self.compile_and_assemble('10 LOAD "SPRITES",8,1\n20 LOAD "OTHER",8,1\n30 END').assembly
        labels = [row for row in asm.splitlines() if row.startswith('__basic_load_success_') and row.endswith(':')]
        self.assertEqual(len(labels), 2)
        self.assertNotEqual(labels[0], labels[1])
        self.assertEqual(asm.count('__basic_load_failed:'), 1)

    def test_string_variable_and_numeric_device(self):
        asm = self.compile_and_assemble(
            '10 N$="SPRITES"\n20 D=8\n30 LOAD N$,D,1\n40 END'
        ).assembly
        self.assertIn('    lda __basic_string_expr', asm)
        self.assertIn('    jsr $FFD5', asm)

    def test_default_parameters_and_one_given_device(self):
        for code in ('LOAD "SPRITES"', 'LOAD "SPRITES",8'):
            with self.subTest(code=code):
                asm = self.compile_and_assemble('10 '+code+'\n20 END').assembly
                self.assertIn('    sta __basic_secondary', asm)
                self.assertIn('    jsr $FFD5', asm)

    def test_screen_load_is_not_reinterpreted_as_kernal_load(self):
        with TemporaryDirectory() as folder:
            screen = Path(folder)/'demo.scr'
            screen.write_bytes(bytes(1000))
            compiled = compile_basic_to_assembly(
                f'10 LOAD SCREEN "{screen}"\n20 END', filename=str(Path(folder)/'test.bas')
            )
        self.assertIn('    jsr __basic_load_screen_resource', compiled.assembly)
        self.assertNotIn('    jsr $FFD5', compiled.assembly)

    def test_other_sources_do_not_have_load_error_routine(self):
        asm = self.compile_and_assemble('10 PRINT "HALLO"\n20 END').assembly
        self.assertNotIn('__basic_load_failed:', asm)
        self.assertNotIn('?LOAD ERROR', asm)

    def test_invalid_load_syntax_reports_line(self):
        for source in ('10 LOAD\n20 END', '10 LOAD "SPRITES",8,1,2\n20 END',
                       '10 LOAD "SPRITES",\n20 END'):
            with self.subTest(source=source):
                with self.assertRaises(C64BasicError) as raised:
                    compile_basic_to_assembly(source)
                self.assertIn('BASIC-Zeile 10:', str(raised.exception))
                self.assertIn('LOAD-Syntax', str(raised.exception))


if __name__ == '__main__':
    unittest.main()
