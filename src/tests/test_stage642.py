"""Stage 642: FNINIT is encoded natively by both internal PE assemblers.

Run with: python -m unittest -q test_stage642
These checks exercise the original x87 initialization opcode DB E3, not NOP.
"""
import unittest
from test_stage605_link import _load_pe_linker
from test_stage641 import SOURCE, compile_src


class Stage642FninitAssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.link = _load_pe_linker()

    def _assemble(self, target, source):
        if target == 'pe32':
            return self.link['assemble_pe32_object_source'](source)
        return self.link['assemble_pe64_object_source'](source)

    def test_fninit_opcode_and_label_offsets(self):
        for target in ('pe32', 'pe64'):
            for spelling in ('fninit', 'FNINIT', 'FnInIt'):
                with self.subTest(target=target, spelling=spelling):
                    asm = ('bits 32\n' if target == 'pe32' else 'bits 64\n') + (
                        'section .text\nglobal _start\nentry _start\n'
                        '_start:\n    nop\n    ' + spelling + '\n'
                        'after_fninit:\n    ret\n'
                    )
                    obj = self._assemble(target, asm)
                    self.assertEqual(obj.code, b'\x90\xDB\xE3\xC3')
                    self.assertEqual(obj.symbols['after_fninit'], 3)

    def test_fninit_rejects_operands(self):
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target):
                asm = '_start:\n    fninit eax\n    ret\n'
                with self.assertRaises((self.link['PE32AssemblerError'], self.link['PE64AssemblerError'])):
                    self._assemble(target, asm)

    def test_real_class_exception_program_uses_opcode(self):
        for target in ('pe32', 'pe64'):
            with self.subTest(target=target):
                asm = compile_src(SOURCE, target)
                self.assertIn('    fninit', asm)
                obj = self._assemble(target, asm)
                self.assertIn(b'\xDB\xE3', obj.code)
                self.assertTrue(self.link['write_coff32_object'](obj) if target == 'pe32'
                                else self.link['write_coff64_object'](obj))


if __name__ == '__main__':
    unittest.main()
