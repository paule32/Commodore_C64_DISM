"""Stage 544: PE32/PE32+ Pascal DLL/UNIT WriteLn console storage.

Run: python -m unittest -v test_stage544
The tests operate on actual code-generator output without requiring ANTLR or Windows.
"""
from __future__ import annotations

import re
import unittest

from test_stage532 import _compiler

c = _compiler()
POS = c.SourcePosition(1, 1)


def _program_with_output():
    call = c.CallStatement(POS, 'writeln', (c.LiteralExpression(POS, 'Test'),))
    procedure = c.GlobalRoutineImplementation(
        'procedure', 'Say', (), None, (), c.CompoundStatement(POS, (call,)), POS
    )
    return c.PascalProgram('Runtime', (), (), c.CompoundStatement(POS, ()),
                           global_routines=(procedure,))


def _generate(bits, kind, *, emit_output=True):
    implementation = c._PE32CodeGenerator if bits == 32 else c._PE64CodeGenerator
    prog = _program_with_output() if emit_output else c.PascalProgram(
        'Runtime', (), (), c.CompoundStatement(POS, ()))
    args = {'console_mode': False}
    args['library_name' if kind == 'library' else 'unit_name'] = 'Runtime'
    return implementation(prog, **args).generate().assembly


class Stage544ConsoleSupportTests(unittest.TestCase):
    def test_both_architectures_define_missing_symbols_in_libraries(self):
        for bits in (32, 64):
            with self.subTest(bits=bits):
                asm = _generate(bits, 'library')
                self.assertRegex(asm, rf'(?m)^__pas_stdout_handle: res[qd] 1$')
                self.assertIn('__pas_written: resd 1', asm)
                self.assertIn('call GetStdHandle', asm)
                self.assertIn('call WriteFile', asm)
                self.assertIn('section .bss', asm)
                if bits == 64:
                    self.assertIn('__pas_write_ptr: resq 1', asm)

    def test_unit_namespaces_do_not_conflict_with_main_program(self):
        for bits in (32, 64):
            with self.subTest(bits=bits):
                asm = _generate(bits, 'unit')
                self.assertIn('__pas_unit_Runtime_stdout_handle:', asm)
                self.assertIn('__pas_unit_Runtime_written:', asm)
                self.assertIn('extern GetStdHandle', asm)
                self.assertIn('extern WriteFile', asm)
                self.assertIn('extern lstrlenA', asm)
                self.assertIn('call GetStdHandle', asm)

    def test_invalid_no_console_mode_does_not_allocate_console(self):
        for bits in (32, 64):
            for kind in ('library', 'unit'):
                with self.subTest(bits=bits, kind=kind):
                    asm = _generate(bits, kind)
                    self.assertNotIn('call AllocConsole', asm)
                    self.assertNotIn('__pas_console_init:', asm)
                    self.assertIn('call GetStdHandle', asm)

    def test_write_cstring_preserves_pointer_around_getstdhandle(self):
        asm = _generate(32, 'library')
        body = asm.split('__pas_write_cstring:\n', 1)[1].split('    ret', 1)[0]
        self.assertRegex(body,
            r'push eax\n\s*push -11\n\s*call GetStdHandle\n'
            r'\s*mov dword ptr \[__pas_stdout_handle\], eax\n'
            r'\s*pop eax\n\s*push eax\n\s*push eax')
        asm = _generate(64, 'library')
        body = asm.split('__pas_write_cstring:\n', 1)[1]
        self.assertIn('mov qword ptr [__pas_write_ptr], rax', body)
        self.assertIn('mov rax, qword ptr [__pas_write_ptr]', body)

    def test_pe64_library_declares_console_winapi_externs(self):
        asm = _generate(64, 'library')
        self.assertIn('extern WriteFile', asm)
        self.assertIn('extern lstrlenA', asm)
        self.assertIn('extern GetStdHandle', asm)

    def test_no_output_does_not_create_unneeded_console_data(self):
        for bits in (32, 64):
            for kind in ('library', 'unit'):
                with self.subTest(bits=bits, kind=kind):
                    asm = _generate(bits, kind, emit_output=False)
                    self.assertNotIn('stdout_handle: res', asm)
                    self.assertNotIn('written: resd', asm)
                    self.assertNotIn('call GetStdHandle', asm)

    def test_existing_program_still_uses_console_setup(self):
        prog = _program_with_output()
        for bits, cls in ((32, c._PE32CodeGenerator),
                          (64, c._PE64CodeGenerator)):
            with self.subTest(bits=bits):
                asm = cls(prog, console_mode=True).generate().assembly
                self.assertIn('call AllocConsole', asm)
                self.assertIn('__pas_stdout_handle:', asm)
                self.assertIn('__pas_written:', asm)
                self.assertIn('call WriteFile', asm)


if __name__ == '__main__':
    unittest.main()
