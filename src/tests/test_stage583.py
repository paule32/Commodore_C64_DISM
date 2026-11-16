"""Stage 583: PE32 Pascal stack-cookie runtime extraction & CES OFF tests.

Pure-source/AST tests: MinGW32, NASM, and native Windows execution are separate.
"""
from pathlib import Path

from test_stage532 import _compiler
from test_stage581 import _ctx, _args

ROOT = Path(__file__).resolve().parent


def test_cookie_imports_pe32_only_when_enabled():
    c = _compiler()
    p = c.SourcePosition(1, 1)
    routine = c.GlobalRoutineImplementation(
        'procedure', 'VerifyGuard', (), None, (),
        c.CompoundStatement(p, (c.ExitStatement(p),)), p
    )
    program = c.PascalProgram(
        'CookieCheck', (), (), c.CompoundStatement(p, ()),
        global_routines=(routine,),
    )
    off = c._PE32CodeGenerator(program, stack_protector=False).generate().assembly
    on = c._PE32CodeGenerator(program, stack_protector=True).generate().assembly
    assert 'jit_pas_cookie_' not in off
    assert '__pas_cookie_secret' not in off
    assert '"libd64_runtime.dll", "jit_pas_cookie_initialize32"' in on
    assert '"libd64_runtime.dll", "jit_pas_cookie_failure32"' in on
    assert 'BCryptGenRandom' not in on
    assert 'InterlockedCompareExchange' not in on
    assert 'RaiseFailFastException' not in on
    assert 'import __d64_cookie_' not in on
    assert 'call __d64_pas_cookie_initialize32' in on
    assert 'jmp __d64_pas_cookie_failure32' in on
    assert '__pas_cookie_secret: resd 1' in on
    body = on.split('__pas_global_verifyguard:', 1)[1].split('; Stage 583:', 1)[0]
    assert body.count('jne __pas_cookie_failure') == 2
    assert body.count('call __pas_cookie_initialize') == 1
    assert on.count('call __d64_pas_cookie_initialize32') == 1


def test_cookie_64bit_path_remains_inline():
    c = _compiler()
    p = c.SourcePosition(1, 1)
    routine = c.GlobalRoutineImplementation(
        'procedure', 'VerifyGuard', (), None, (),
        c.CompoundStatement(p, ()), p
    )
    program = c.PascalProgram('Cookie64', (), (), c.CompoundStatement(p, ()), global_routines=(routine,))
    on = c._PE64CodeGenerator(program, stack_protector=True).generate().assembly
    assert 'BCryptGenRandom' in on
    assert 'RaiseFailFastException' in on
    assert 'jit_pas_cookie_initialize32' not in on
    assert '__pas_cookie_secret: resq 1' in on


def test_runtime_assembly_exports_and_both_build_trees():
    a = (ROOT / 'runtime/pascal/cookie32.asm').read_text('utf-8')
    for symbol in ('_jit_pas_cookie_initialize32', '_jit_pas_cookie_failure32'):
        assert f'global {symbol}' in a
        assert f'{symbol}:' in a
    for api in ('_BCryptGenRandom@16', '_RaiseFailFastException@12',
                '_ExitProcess@4'):
        assert f'extern {api}' in a
        assert f'call {api}' in a
    assert 'or edx, 1' in a
    assert 'lock cmpxchg dword [ecx], edx' in a
    assert '_InterlockedCompareExchange@12' not in a
    assert 'push 0xC0000409' in a
    for directory in ('runtime', 'runtime/compiler'):
        script = (ROOT / directory / 'build.win32.sh').read_text('utf-8')
        assert 'pas_cookie32.o' in script
        assert 'pascal/cookie32.asm' in script
        assert '-lbcrypt -lkernel32' in script
        defs = (ROOT / directory / 'win32/libd64_runtime.def').read_text('utf-8')
        assert 'jit_pas_cookie_initialize32' in defs
        assert 'jit_pas_cookie_failure32' in defs
        source_defs = (ROOT / directory / 'exports/strings.def').read_text('utf-8')
        assert 'jit_pas_cookie_initialize32' in source_defs
        assert 'jit_pas_cookie_failure32' in source_defs


def test_ces_off_omits_all_messagebox_code_even_with_global_on():
    # The context deliberately has global CES ON; per-build OFF must win.
    ns = _ctx()
    create = ns['_build_pe32_mszip_loader']
    off = create(**_args(), ces_enabled=False)
    on = create(**_args(), ces_enabled=True)
    assert b'CES:' not in off
    assert b'MessageBoxA\0' not in off
    assert b'user32.dll\0' not in off
    assert b'CES: LoadLibraryA failed' in on
    assert b'CES: GetProcAddress failed' in on
    assert len(off) < len(on)


if __name__ == '__main__':
    for function in (test_cookie_imports_pe32_only_when_enabled,
                     test_cookie_64bit_path_remains_inline,
                     test_runtime_assembly_exports_and_both_build_trees,
                     test_ces_off_omits_all_messagebox_code_even_with_global_on):
        function()
        print('PASS', function.__name__)
