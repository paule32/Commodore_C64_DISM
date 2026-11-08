"""Stage 538: architecture-specific no-frame safety and Pascal string storage."""
import ast
import configparser
import unittest
from pathlib import Path
from pascal_optimizer import omit_safe_pascal_stack_frames
from test_stage532 import _compiler

ROOT = Path(__file__).resolve().parent


class Stage538Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = _compiler()
        cls.p = cls.c.SourcePosition(1, 1)

    def make_program(self, *, parameters=(), local_variables=(), body=None):
        c, p = self.c, self.p
        routine = c.GlobalRoutineImplementation(
            'procedure', 'Tick', tuple(parameters), None,
            tuple(local_variables), body or c.CompoundStatement(p, ()), p, 'cdecl')
        return c.PascalProgram('FrameCheck', (), (), c.CompoundStatement(p, ()),
                               global_routines=(routine,))

    def test_x86_frame_omission_and_saved_registers(self):
        c = self.c
        for level in (0, 1, 2, 3):
            asm = c._PE32CodeGenerator(self.make_program(),
                                      optimization_level=level,
                                      no_stack_frames=True).generate().assembly
            region = asm.split('__pas_global_tick:', 1)[1].split('\n__pas_console_init:', 1)[0]
            self.assertNotIn('mov ebp, esp', region)
            self.assertIn('push ebx', region)
            self.assertIn('pop edi', region)
            self.assertIn('pop esi', region)
            self.assertIn('pop ebx', region)

    def test_x64_frame_omission_only_leaf(self):
        c = self.c
        asm = c._PE64CodeGenerator(self.make_program(),
                                   no_stack_frames=True).generate().assembly
        region = asm.split('__pas_global_tick:', 1)[1].split('\n__pas_console_init:', 1)[0]
        self.assertNotIn('mov rbp, rsp', region)
        self.assertIn('ret', region)
        statement = c.CallStatement(self.p, 'writeln', (c.LiteralExpression(self.p, 12),))
        asm = c._PE64CodeGenerator(self.make_program(
            body=c.CompoundStatement(self.p, (statement,))),
            no_stack_frames=True).generate().assembly
        region = asm.split('__pas_global_tick:', 1)[1].split('\n__pas_console_init:', 1)[0]
        self.assertIn('mov rbp, rsp', region)

    def test_stack_cookie_always_retains_frame(self):
        c = self.c
        for cls, reg in ((c._PE32CodeGenerator, 'ebp'), (c._PE64CodeGenerator, 'rbp')):
            generated = cls(self.make_program(), no_stack_frames=True,
                            stack_protector=True).generate().assembly
            section = generated.split('__pas_global_tick:', 1)[1].split('\n__pas_console_init:', 1)[0]
            self.assertIn(f'mov {reg},', section)
            self.assertIn('__pas_cookie_secret', section)

    def test_parameter_frame_preserved_pe32(self):
        c, p = self.c, self.p
        param = c.ParameterDeclaration(('Value',), 'integer', 'value', p)
        generated = c._PE32CodeGenerator(self.make_program(parameters=(param,), body=c.CompoundStatement(p, (
                                            c.CallStatement(p, 'writeln', (c.NameExpression(p, 'Value'),)),
                                        ))),
                                        optimization_level=2,
                                        no_stack_frames=True).generate().assembly
        section = generated.split('__pas_global_tick:', 1)[1].split('\n__pas_console_init:', 1)[0]
        self.assertIn('mov ebp, esp', section)
        self.assertIn('[ebp+8]', section)

    def test_local_frame_preserved_at_O2(self):
        c, p = self.c, self.p
        local = c.VarDeclaration(('A',), 'integer', None, p)
        generated = c._PE32CodeGenerator(self.make_program(local_variables=(local,)),
                                        optimization_level=2,
                                        no_stack_frames=True).generate().assembly
        section = generated.split('__pas_global_tick:', 1)[1].split('\n__pas_console_init:', 1)[0]
        self.assertIn('mov ebp, esp', section)
        self.assertIn('sub esp,', section)

    def test_pure_assembler_pass_guards(self):
        instructions = ['__pas_global_a:', 'push ebp', 'mov ebp, esp',
                        'push ebx', 'push esi', 'push edi',
                        'mov eax, [ebp+8]', 'mov ebx, dword ptr [ebp-4]',
                        'mov esi, dword ptr [ebp-8]', 'mov edi, dword ptr [ebp-12]',
                        'mov esp, ebp', 'pop ebp', 'ret 8']
        out, _ = omit_safe_pascal_stack_frames(instructions, {}, ['__pas_global_a'])
        self.assertEqual(out, instructions)
        ins64 = ['__pas_method_test:', 'push rbp', 'mov rbp, rsp', 'push rsi',
                 'sub rsp, 8', 'mov rsi, rcx', 'xor eax, eax',
                 'lea rsp, [rbp-16]', 'pop rsi', 'pop rbp', 'ret']
        output, _ = omit_safe_pascal_stack_frames(ins64, {}, ['__pas_method_test'], is_pe64=True)
        self.assertEqual(output, ins64)  # Win64 RSI save needs unwind metadata

    def test_identical_classname_literal_shares_storage(self):
        c, p = self.c, self.p
        program = c.PascalProgram('StringPool', (), (), c.CompoundStatement(
            p, (c.CallStatement(p, 'writeln', (c.LiteralExpression(p, 'TFoo'),)),)),
            types=(c.TypeDeclaration('TFoo', c.ClassTypeSpecification(
                p, None, (), ()), p),))
        for cls in (c._PE32CodeGenerator, c._PE64CodeGenerator):
            ordinary = cls(program, optimization_level=0).generate().assembly
            pooled = cls(program, optimization_level=1).generate().assembly
            self.assertIn('__pas_string_0: db 84, 70, 111, 111, 0', ordinary)
            self.assertIn('__pas_classname_tfoo: db 84, 70, 111, 111, 0', ordinary)
            self.assertIn('__pas_string_0:\n__pas_classname_tfoo: db 84, 70, 111, 111, 0', pooled)
            self.assertEqual(pooled.count('db 84, 70, 111, 111, 0'), 1)

    def test_ini_roundtrip_independent_frame_option(self):
        source = (ROOT/'d64_dism.py').read_text(encoding='utf-8')
        source = source.replace('lazy from app_lang.deu import', 'from app_lang.deu import')
        source = source.replace('lazy from app_lang.enu import', 'from app_lang.enu import')
        tree = ast.parse(source)
        section = 'Settings.Windows.{_suffix}.Compiler.Pascal.Optimierung'
        keys = {'pe32': 'opt32', 'pe64': 'opt64'}
        from pascal_optimizer import normalize_optimization_level
        def level(options):
            return normalize_optimization_level(options.get('level', 0))
        def frame(options):
            return bool(options.get('no_stack_frames', False))
        def parse_bool(value, default=False):
            return str(value).lower() in ('true', 'yes', '1')
        env = {'PROJECT_WINDOWS_PASCAL_OPTIMIZATION_KEYS':keys,
               '_stage537_optimizer_level':level,
               'stage538_no_stack_frames':frame,
               '_parse_project_bool':parse_bool}
        def execute(name, kwargs):
            fn = next(f for f in tree.body if isinstance(f, ast.FunctionDef) and f.name == name)
            node = next(n for n in fn.body if isinstance(n, ast.For) and
                        section in ast.get_source_segment(source, n))
            exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                         '<stage538-ini>', 'exec'), dict(env, **kwargs))
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str
        execute('format_project_ini', {'parser':parser,'entries':{
            'opt32':[{'level':2,'no_stack_frames':True}],
            'opt64':[{'level':3,'no_stack_frames':False}]}})
        self.assertEqual(parser.get('Settings.Windows.32Bit.Compiler.Pascal.Optimierung', 'NoStackFrames'), 'true')
        self.assertEqual(parser.get('Settings.Windows.64Bit.Compiler.Pascal.Optimierung', 'NoStackFrames'), 'false')
        restored={}
        execute('parse_project_ini', {'parser':parser,'entries':restored})
        self.assertTrue(restored['opt32'][0]['no_stack_frames'])
        self.assertFalse(restored['opt64'][0]['no_stack_frames'])
        self.assertEqual(restored['opt32'][0]['level'],2)
        self.assertEqual(restored['opt64'][0]['level'],3)

    def test_gui_persistence_and_parallel_wiring(self):
        source = (ROOT/'d64_dism.py').read_text(encoding='utf-8')
        for expected in ('QGroupBox("Stack: ", body)', 'QCheckBox("No Stack Frames"',
                         '"NoStackFrames":', '"no_stack_frames": stage538_no_stack_frames(',
                         'compiler_kwargs["no_stack_frames"]'):
            self.assertIn(expected, source)
        self.assertIn('"no_stack_frames" in parameters',
                      (ROOT/'pascal_parallel_build.py').read_text(encoding='utf-8'))
        self.assertIn('no_stack_frames=no_stack_frames',
                      (ROOT/'c64pascal/compiler.py').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
