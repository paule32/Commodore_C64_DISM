"""Stage 579: remove unused Pascal Double BSS scratch areas (PE32/PE64).

Run: python -m unittest -v test_stage579
Tests operate on the actual code generator with AST input, without Windows.
"""
from __future__ import annotations

from pathlib import Path
import unittest

from test_stage532 import _compiler


ROOT = Path(__file__).resolve().parent
C = _compiler()
P = C.SourcePosition(1, 1)
DEAD_NAMES = ('__pas_double_scratch', '__pas_double_int_scratch',
              '__pas_double_buffer')


def _program(expr, *, with_globals=True):
    variables = (
        C.VarDeclaration(('Value',), 'integer', None, P),
        C.VarDeclaration(('ResultValue',), 'double', None, P),
    ) if with_globals else ()
    if with_globals:
        statements = (C.AssignmentStatement(P, 'ResultValue', expr),)
    else:
        statements = (C.IfStatement(P, expr, C.CompoundStatement(P, ()), None),)
    return C.PascalProgram('Stage579', (), variables,
                           C.CompoundStatement(P, statements))


class Stage579Tests(unittest.TestCase):
    def test_both_targets_emit_no_dead_scratch_variables(self):
        # Cover literal-only Double, mixed Integer/Double, no FP and all
        # optimization levels with and without the stack-protector cookie.
        expressions = (
            C.LiteralExpression(P, 2.5),
            C.BinaryExpression(P, C.NameExpression(P, 'Value'), '+',
                               C.LiteralExpression(P, 2.5)),
            C.LiteralExpression(P, 1),
        )
        for backend in (C._PE32CodeGenerator, C._PE64CodeGenerator):
            for expr in expressions:
                for protector in (False, True):
                    for level in (0, 1, 2, 3):
                        with self.subTest(backend=backend.__name__,
                                          expression=type(expr).__name__,
                                          cookie=protector, opt=level):
                            asm = backend(_program(expr),
                                          stack_protector=protector,
                                          optimization_level=level).generate().assembly
                            for name in DEAD_NAMES:
                                self.assertNotIn(name, asm)
                            if protector:
                                self.assertIn('__pas_cookie_secret: res', asm)
                            self.assertIn('section .bss', asm)

    def test_pe32_int_to_double_uses_short_lived_stack_value(self):
        expr = C.BinaryExpression(P, C.NameExpression(P, 'Value'), '+',
                                  C.LiteralExpression(P, 2.5))
        asm = C._PE32CodeGenerator(_program(expr)).generate().assembly
        self.assertIn('    push eax\n    fild dword ptr [esp]\n    add esp, 4', asm)
        self.assertNotIn('mov dword ptr [__pas_double_int_scratch]', asm)
        self.assertIn('    faddp', asm)
        self.assertIn('    fstp qword ptr [ecx]', asm)
        for name in DEAD_NAMES:
            self.assertNotIn(name, asm)

    def test_double_literals_alone_do_not_open_empty_bss(self):
        expr = C.BinaryExpression(P, C.LiteralExpression(P, 1.5), '>',
                                  C.LiteralExpression(P, 1.0))
        for backend in (C._PE32CodeGenerator, C._PE64CodeGenerator):
            with self.subTest(target=backend.__name__):
                asm = backend(_program(expr, with_globals=False),
                              console_mode=False).generate().assembly
                self.assertIn('section .data', asm)
                self.assertNotIn('section .bss', asm)
                self.assertIn('fld qword ptr', asm)
                for name in DEAD_NAMES:
                    self.assertNotIn(name, asm)

    def test_regression_uses_new_code_generation_not_stale_asm(self):
        # The Stage-577/579 test_raise.generated.pe32.asm predated the
        # System.Strings DLL conversion and must not be shipped as current.
        self.assertFalse((ROOT/'runtime/pascal/test/test_raise.generated.pe32.asm').exists())
        asm = C._PE32CodeGenerator(_program(C.LiteralExpression(P, 3.5))).generate().assembly
        for name in DEAD_NAMES:
            self.assertNotIn(name, asm)
        self.assertIn('section .bss', asm)

    def test_new_implementation_does_not_use_global_double_scratch(self):
        source = (ROOT/'c64pascal/compiler.py').read_text('utf-8')
        for suffix in ('_double_scratch', '_double_int_scratch', '_double_buffer'):
            self.assertNotIn('f"{self.symbol_prefix}'+suffix, source)
        self.assertIn('    fild dword ptr [esp]', source)


if __name__ == '__main__':
    unittest.main(verbosity=2)
