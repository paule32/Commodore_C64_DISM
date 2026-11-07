"""Stage 534 targeted code generation and Win32 runtime regression tests.

Tests are source/codegen-level on Linux; native Windows run and rebuilt DLL
required before certifying object lifetime and exception TLS behavior.
"""
from pathlib import Path
import re
import unittest
from test_stage532 import _compiler

ROOT = Path(__file__).resolve().parent


class TestStage534(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = _compiler()
        cls.loc = cls.c.SourcePosition(1, 1)

    def _routine_program(self, *, convention=None, params=1, body=None):
        c, loc = self.c, self.loc
        plist = tuple(c.ParameterDeclaration((f'Value{i}',), 'Integer', 'value', loc)
                      for i in range(params))
        proc = c.GlobalRoutineImplementation('procedure', 'Echo', plist, None, (),
                    c.CompoundStatement(loc, ()), loc, convention)
        args = tuple(c.LiteralExpression(loc, 42+i) for i in range(params))
        block = body or c.CompoundStatement(loc, (c.CallStatement(loc, 'Echo', args),))
        return c.PascalProgram('Smoke', (), (), block, global_routines=(proc,))

    def test_global_cdecl_stack_abi(self):
        asm = self.c._PE32CodeGenerator(self._routine_program(params=2)).generate().assembly
        main = asm.split('_start:', 1)[1].split('; procedure Echo', 1)[0]
        self.assertRegex(main, r'mov eax, 43\s+push eax\s+mov eax, 42\s+push eax\s+call __pas_global_echo\s+add esp, 8')
        callee = asm.split('__pas_global_echo:', 1)[1]
        self.assertIn('mov eax, dword ptr [ebp+8]', callee)
        self.assertIn('mov eax, dword ptr [ebp+12]', callee)
        self.assertNotIn('mov [__pas_param_global_echo_', main)

    def test_global_stdcall_stack_abi(self):
        asm = self.c._PE32CodeGenerator(self._routine_program(convention='stdcall', params=1)).generate().assembly
        main = asm.split('_start:', 1)[1].split('; procedure Echo', 1)[0]
        self.assertIn('call __pas_global_echo', main)
        self.assertNotIn('add esp, 4', main)
        callee = asm.split('__pas_global_echo:', 1)[1]
        self.assertIn('ret 4', callee)

    def test_try_frames_are_stack_local_and_independent(self):
        c,loc=self.c,self.loc
        inner = c.TryStatement(loc, (), 'except', ())
        outer = c.TryStatement(loc, (inner,), 'finally', ())
        program = c.PascalProgram('Smoke', (), (), c.CompoundStatement(loc,(outer,)))
        asm = c._PE32CodeGenerator(program).generate().assembly
        self.assertEqual(asm.count('sub esp, 292'), 2)
        self.assertEqual(asm.count('lea eax, [esp+24]'), 2)
        self.assertEqual(asm.count('call _jit_exception_push'), 2)
        self.assertNotRegex(asm, r'_exc_(env|frame)_\d+: resb')
        self.assertIn('mov dword ptr [esp+16], esp', asm)
        self.assertIn('lea edx, [esp+32]', asm) # preserve rethrow message

    def test_exit_unlinks_active_exception_frame(self):
        c,loc=self.c,self.loc
        statement = c.TryStatement(loc, (c.ExitStatement(loc),), 'except', ())
        routine = c.GlobalRoutineImplementation('procedure','Go',(),None,(),
                    c.CompoundStatement(loc,(statement,)),loc)
        program = c.PascalProgram('Smoke',(),(),c.CompoundStatement(loc,()),global_routines=(routine,))
        asm=c._PE32CodeGenerator(program).generate().assembly
        body=asm.split('__pas_global_go:',1)[1]
        self.assertRegex(body,r'push eax\s+call _jit_exception_pop\s+pop eax\s+mov ebx, dword ptr \[ebp-4\]\s+mov esi, dword ptr \[ebp-8\]\s+mov edi, dword ptr \[ebp-12\]\s+mov esp, ebp')

    def test_runtime_active_assembler_atomic(self):
        for name in ('runtime/memory_nt32.asm','runtime/compiler/memory_nt32.asm'):
            with self.subTest(name=name):
                text=(ROOT/name).read_text()
                self.assertIn('lock cmpxchg dword [crt_init_state]',text)
                self.assertIn('call init_runtime',text)
                self.assertIn('cmp dword [crt_init_state], 2',text)
                self.assertIn('crt_init_state: resd 1',text)

    def test_object_tracking_and_tls(self):
        for branch in ('runtime','runtime/compiler'):
            with self.subTest(branch=branch):
                source=(ROOT/branch/'jitObject.cc').read_text()
                self.assertIn('d64_object_transition(instance, 1)',source)
                self.assertIn('d64_object_transition(instance, 2)',source)
                self.assertIn('D64_OBJECT_LIFETIME_TRACE',source)
                self.assertIn('GetCurrentThreadId',source)
                self.assertIn('GetCurrentProcessId',source)
                exc=(ROOT/branch/'exception.cc').read_text()
                self.assertIn('TlsGetValue',exc)
                self.assertIn('TlsSetValue',exc)
                self.assertIn('TlsFree',exc)
                self.assertIn('frame->message[i] = message[i]',exc)
                self.assertNotIn('JitExceptionFrame *gExceptionFrame =',exc)
                dllmain=(ROOT/branch/'dllmain.cc').read_text()
                self.assertIn('DLL_PROCESS_DETACH',dllmain)
                self.assertIn('_jit_exception_tls_cleanup();',dllmain)


if __name__ == '__main__':
    unittest.main(verbosity=2)
