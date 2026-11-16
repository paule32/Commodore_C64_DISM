"""Stage 587 - conservative no-frame optimization for Pascal routines.

Run with: python -m unittest -v test_stage587.py
"""
from __future__ import annotations

import unittest
from pathlib import Path

from pascal_optimizer import omit_safe_pascal_stack_frames
from test_stage532 import _compiler

ROOT = Path(__file__).resolve().parent


def frame_body(prefix='__pas_global_tick', *, source=None, epilogue=True):
    lines = [f'{prefix}:', '    push ebp', '    mov ebp, esp',
             '    push ebx', '    push esi', '    push edi']
    lines.extend(source or [])
    if epilogue:
        lines.extend([
            '    mov ebx, dword ptr [ebp-4]',
            '    mov esi, dword ptr [ebp-8]',
            '    mov edi, dword ptr [ebp-12]',
            '    mov esp, ebp', '    pop ebp', '    ret',
        ])
    return lines


class Stage587Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = _compiler()
        cls.p = cls.c.SourcePosition(1, 1)

    def program(self, *, body=None, parameters=(), locals_=(), convention='cdecl'):
        c, p = self.c, self.p
        routine = c.GlobalRoutineImplementation(
            'procedure', 'Tick', tuple(parameters), None, tuple(locals_),
            body or c.CompoundStatement(p, ()), p, convention)
        return c.PascalProgram('Stage587', (), (), c.CompoundStatement(p, ()),
                               global_routines=(routine,))

    def body_asm(self, cls, **options):
        asm = cls(self.program(**options.pop('program', {})),
                  no_stack_frames=options.pop('no_stack_frames', True),
                  optimization_level=options.pop('optimization_level', 2),
                  console_mode=False, **options).generate().assembly
        return asm.split('__pas_global_tick:', 1)[1].split('section .data', 1)[0]

    def test_pe32_call_and_multiple_returns_without_ebp(self):
        c, p = self.c, self.p
        body = c.CompoundStatement(p, (
            c.CallStatement(p, 'writeln', (c.LiteralExpression(p, 123),)),
            c.ExitStatement(p)))
        asm = self.body_asm(c._PE32CodeGenerator, program={'body': body})
        self.assertNotIn('mov ebp, esp', asm)
        self.assertNotIn('mov esp, ebp', asm)
        self.assertIn('call __pas_print_int', asm)
        self.assertEqual(asm.count('    pop edi'), 2)
        self.assertIn('    pop esi\n    pop ebx\n    ret', asm)

    def test_pe32_O0_param_materialization_rebased(self):
        c, p = self.c, self.p
        param = c.ParameterDeclaration(('Value',), 'integer', 'value', p)
        asm = self.body_asm(c._PE32CodeGenerator, optimization_level=0,
                            program={'parameters': (param,)})
        self.assertNotIn('mov ebp, esp', asm)
        self.assertIn('[esp+4]', asm)  # parameter before EBX/ESI/EDI pushes
        self.assertNotIn('[ebp+8]', asm)

    def test_pe32_O2_param_rebased_while_stack_has_argument(self):
        snippet = frame_body(source=['    push eax',
                                     '    mov edx, [ebp+8]',
                                     '    add esp, 4',
                                     '    call __pas_other'])
        source_map = {2: 99, 8: 101, 9: 102, 12: 103}
        out, mapped = omit_safe_pascal_stack_frames(
            snippet, source_map, ['__pas_global_tick'])
        self.assertNotIn('    mov ebp, esp', out)
        self.assertIn('    mov edx, [esp+20]', out)  # base 16 + 4 pushed
        self.assertEqual(mapped[out.index('    mov edx, [esp+20]') + 1], 101)

    def test_pe32_stdcall_ret_n_is_preserved(self):
        snippet = frame_body(source=['    lea ecx, [ebp+12]', '    mov eax, [ecx]'])
        snippet[-1] = '    ret 8'
        out, _ = omit_safe_pascal_stack_frames(snippet, {}, ['__pas_global_tick'])
        self.assertNotIn('push ebp', '\n'.join(out))
        self.assertIn('    lea ecx, [esp+20]', out)
        self.assertEqual(out[-1], '    ret 8')

    def test_pe32_branch_balanced_paths(self):
        snippet = frame_body(source=[
            '    test eax, eax',
            '    jz __pas_skip',
            '    push ecx',
            '    call __pas_other',
            '    add esp, 4',
            '__pas_skip:',
            '    lea ecx, [ebp+8]',
        ])
        out, _ = omit_safe_pascal_stack_frames(snippet, {}, ['__pas_global_tick'])
        self.assertIn('    lea ecx, [esp+16]', out)
        self.assertNotIn('mov esp, ebp', '\n'.join(out))

    def test_pe32_rejects_conflicting_branch_heights(self):
        snippet = frame_body(source=[
            '    test eax, eax', '    jz __pas_skip',
            '    push ecx', '__pas_skip:', '    mov eax, 5'])
        out, _ = omit_safe_pascal_stack_frames(snippet, {}, ['__pas_global_tick'])
        self.assertEqual(out, snippet)

    def test_pe32_rejects_stack_locals_and_unsafe_sp_references(self):
        cases = ([ '    lea eax, [ebp-20]' ],
                 [ '    mov eax, [esp+4]' ],
                 [ '    pushfd' ],
                 [ '    jmp __external_label' ],
                 [ '    sub esp, 12', '    mov eax, 1' ])
        for case in cases:
            with self.subTest(case=case):
                snippet = frame_body(source=case)
                out, _ = omit_safe_pascal_stack_frames(
                    snippet, {}, ['__pas_global_tick'])
                self.assertEqual(out, snippet)

    def test_pe32_local_vars_keep_frame(self):
        c, p = self.c, self.p
        local = c.VarDeclaration(('Value',), 'integer', None, p)
        asm = self.body_asm(c._PE32CodeGenerator,
                            program={'locals_': (local,)})
        self.assertIn('mov ebp, esp', asm)
        self.assertIn('sub esp,', asm)

    def test_pe64_home_space_spills_rebased_for_leaf(self):
        c, p = self.c, self.p
        param = c.ParameterDeclaration(('Value',), 'integer', 'value', p)
        asm = self.body_asm(c._PE64CodeGenerator,
                            program={'parameters': (param,)})
        self.assertIn('mov qword ptr [rsp+8], rcx', asm)
        self.assertNotIn('mov rbp, rsp', asm)
        self.assertNotIn('pop rbp', asm)

    def test_pe64_call_keeps_frame_for_shadow_unwind(self):
        c, p = self.c, self.p
        body = c.CompoundStatement(p, (
            c.CallStatement(p, 'writeln', (c.LiteralExpression(p, 1),)),))
        asm = self.body_asm(c._PE64CodeGenerator, program={'body': body})
        self.assertIn('mov rbp, rsp', asm)
        self.assertIn('sub rsp, 32', asm)

    def test_stack_cookie_and_disabled_option_both_keep_frame(self):
        c = self.c
        for impl, target in ((c._PE32CodeGenerator, 'ebp'),
                             (c._PE64CodeGenerator, 'rbp')):
            with self.subTest(arch=impl.__name__):
                self.assertIn(f'mov {target}', self.body_asm(
                    impl, stack_protector=True))
                self.assertIn(f'mov {target}', self.body_asm(
                    impl, no_stack_frames=False))


    def test_pe32_all_optimization_levels_keep_balanced_calls_frameless(self):
        c, p = self.c, self.p
        body = c.CompoundStatement(p, (
            c.CallStatement(p, 'writeln', (c.LiteralExpression(p, 3),)),))
        for level in (0, 1, 2, 3):
            with self.subTest(level=level):
                asm = self.body_asm(c._PE32CodeGenerator,
                                    optimization_level=level,
                                    program={'body': body})
                self.assertNotIn('mov ebp, esp', asm)
                self.assertIn('call __pas_print_int', asm)

    def test_pe32_method_candidate_is_optimized(self):
        code = frame_body('__pas_method_tfoo_ping', source=[
            '    mov eax, dword ptr [ebp+8]',
            '    push eax', '    call __pas_other', '    add esp, 4'])
        out, _ = omit_safe_pascal_stack_frames(
            code, {}, ['__pas_method_tfoo_ping'])
        self.assertNotIn('mov ebp, esp', '\n'.join(out))
        self.assertIn('    mov eax, dword ptr [esp+16]', out)

    def test_pe64_cannot_omit_method_frame_or_nonvolatile_save(self):
        code = ['__pas_method_tfoo_ping:', '    push rbp', '    mov rbp, rsp',
                '    push rsi', '    mov rsi, rcx',
                '    pop rsi', '    mov rsp, rbp', '    pop rbp', '    ret']
        out, _ = omit_safe_pascal_stack_frames(
            code, {}, ['__pas_method_tfoo_ping'], is_pe64=True)
        self.assertEqual(out, code)

    def test_gui_option_and_unit_build_wiring_remain(self):
        d64 = (ROOT / 'd64_dism.py').read_text('utf-8')
        compiler = (ROOT / 'c64pascal/compiler.py').read_text('utf-8')
        self.assertIn('QCheckBox("No Stack Frames"', d64)
        self.assertIn('compiler_kwargs["no_stack_frames"]', d64)
        self.assertIn('omit_safe_pascal_stack_frames(', compiler)
        self.assertIn('"no_stack_frames" in parameters',
                      (ROOT / 'pascal_parallel_build.py').read_text('utf-8'))


if __name__ == '__main__':
    unittest.main()
