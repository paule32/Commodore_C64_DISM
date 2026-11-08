"""Stage 551: console DLL ABI and generated Pascal adapter regression tests.

Runs with the AST-only fallback from Stage 532 (no Windows runtime required).
Native DLL/EXE execution is a separate Windows test.
"""
import unittest
from pathlib import Path
from test_stage532 import _compiler

c = _compiler()
p = c.SourcePosition(1, 1)
ROOT = Path(__file__).resolve().parent


def sample():
    body = c.CompoundStatement(p, (
        c.CallStatement(p, 'writeln', (
            c.LiteralExpression(p, 'Ready'),
            c.LiteralExpression(p, 42),
            c.LiteralExpression(p, 3.25),
        )),
        c.CallStatement(p, 'readln', ()),
        c.CallStatement(p, 'clrscr', ()),
    ))
    return c.PascalProgram('ConsoleTest', (), (), body)


class TestStage551Console(unittest.TestCase):
    def test_both_targets_use_shared_runtime_not_embedded_winapi(self):
        for backend in (c._PE32CodeGenerator, c._PE64CodeGenerator):
            with self.subTest(backend=backend.__name__):
                asm = backend(sample()).generate().assembly
                for func in ('d64_console_init', 'd64_console_restore',
                             'd64_console_write_text', 'd64_console_write_int',
                             'd64_console_write_double', 'd64_console_newline',
                             'd64_console_read_string', 'd64_console_clear'):
                    self.assertIn(f'"libd64_console.dll", "{func}"', asm)
                self.assertNotIn('call AllocConsole', asm)
                self.assertNotIn('call GetConsoleMode', asm)
                self.assertNotIn('call WriteFile', asm)
                self.assertNotIn('__pas_write_cstring:', asm)
                self.assertNotIn('__pas_stdout_handle:', asm)
                self.assertNotIn('__pas_written:', asm)
                self.assertIn('call _d64_console_read_string', asm)
                self.assertIn('call _jit_free', asm)

    def test_32bit_argument_abi_and_x87(self):
        asm = c._PE32CodeGenerator(sample()).generate().assembly
        self.assertIn('__pas_print_string:\n    push eax\n    call _d64_console_write_text\n    add esp, 4\n    ret',asm)
        self.assertIn('__pas_print_double:\n    sub esp, 8\n    fstp qword ptr [esp]\n    call _d64_console_write_double\n    add esp, 8\n    ret', asm)

    def test_64bit_argument_abi_and_x87(self):
        asm = c._PE64CodeGenerator(sample()).generate().assembly
        self.assertIn('mov rcx, rax\n    sub rsp, 32\n    call _d64_console_write_text',asm)
        self.assertIn('sub rsp, 48\n    fstp qword ptr [rsp+32]\n    movsd xmm0, qword ptr [rsp+32]\n    call _d64_console_write_double',asm)

    def test_units_and_libraries_do_not_alloc_console(self):
        program = c.PascalProgram('PrintUnit', (), (), c.CompoundStatement(p, (
            c.CallStatement(p, 'writeln', (c.LiteralExpression(p, 'Hello'),)),
        )))
        for backend in (c._PE32CodeGenerator, c._PE64CodeGenerator):
            for opt in ({'unit_name': 'PrintUnit'}, {'library_name': 'PrintDLL'}):
                with self.subTest(backend=backend.__name__, opt=opt):
                    asm = backend(program, **opt).generate().assembly
                    self.assertNotIn('__pas_console_init:', asm)
                    self.assertNotIn('call AllocConsole', asm)
                    self.assertIn('_d64_console_write_text', asm)
                    if 'library_name' in opt:
                        self.assertIn('__pas_print_string:', asm)
                    else:
                        self.assertNotIn('__pas_print_string:', asm)

    def test_read_int_consumes_only_one_line(self):
        program = c.PascalProgram('InputTest', (),
            (c.VarDeclaration(('Number',), 'integer', None, p),),
            c.CompoundStatement(p, (
                c.CallStatement(p, 'readln', (c.DesignatorExpression(p,'Number'),)),
            )))
        for backend in (c._PE32CodeGenerator, c._PE64CodeGenerator):
            with self.subTest(backend=backend.__name__):
                asm = backend(program).generate().assembly
                self.assertIn('call _d64_console_read_int', asm)
                self.assertNotIn('call _d64_console_read_string', asm)

    def test_no_console_api_data_in_bss(self):
        for backend in (c._PE32CodeGenerator, c._PE64CodeGenerator):
            asm = backend(sample()).generate().assembly
            for name in ('console_info:', 'console_mode:', 'console_rect:',
                         'console_restore_rect:', 'format_buffer:', 'char_buffer:'):
                self.assertNotIn(name, asm)

    def test_dll_exports_and_matching_allocator(self):
        src = (ROOT / 'runtime/compiler/console_runtime.cc').read_text('utf-8')
        for name in ('init','restore','write_text','write_int','write_double',
                     'write_char','newline','clear','read_line','read_int','read_string'):
            self.assertIn('d64_console_' + name + '(',src)
        self.assertIn('GetProcAddress(runtime, "_jit_malloc")', src)
        self.assertIn('FreeConsole()', src)
        self.assertIn('if (state.created_console)', src)

    def test_build_scripts_for_both_architectures(self):
        for bits in ('32','64'):
            script = ROOT / f'runtime/compiler/build.console.win{bits}.sh'
            text = script.read_text('utf-8')
            self.assertIn(f'libd64_console.dll',text)
            self.assertIn('console_runtime.cc',text)
            self.assertIn(f'MINGW{bits}',text)

    def test_ide_deploys_target_architecture(self):
        text = (ROOT / 'd64_dism.py').read_text('utf-8')
        self.assertIn('def _stage551_deploy_pascal_console', text)
        self.assertIn('_pe_file_machine(candidate) != machine', text)
        self.assertIn('build.console.win32.sh', text)
        self.assertIn('build.console.win64.sh', text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
