"""Stage 532 regression: opt-in Pascal frame cookies, PE32/PE32+, no GUI.

Run: python test_stage532.py
The smoke test bypasses ANTLR parsing by constructing a tiny Pascal AST;
this allows validation with older installed antlr4 runtimes. Windows native
execution (especially process fail-fast behavior) is a separate test.
"""
from __future__ import annotations

import ast
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = (ROOT / "c64pascal" / "compiler.py").read_text("utf-8")
D64 = (ROOT / "d64_dism.py").read_text("utf-8")


def _compiler():
    # Replacing parser classes is strictly limited to this *codegen-only* test;
    # the real generated lexer/parser and source parsing are not exercised.
    # If the correct antlr4 runtime is available, use the real classes.
    try:
        from c64pascal import compiler
        return compiler
    except (TypeError, ImportError):
        for name in ("C64PascalLexer", "C64PascalParser", "C64PascalParserVisitor"):
            mod = types.ModuleType(f"c64pascal.generated.{name}")
            setattr(mod, name, type(name, (), {}))
            sys.modules[mod.__name__] = mod
        from c64pascal import compiler
        return compiler


def test_opt_in_and_architectures():
    c = _compiler()
    loc = c.SourcePosition(1, 1)
    exit_body = c.CompoundStatement(loc, (c.ExitStatement(loc),))
    routine = c.GlobalRoutineImplementation(
        "procedure", "CookieProbe", (), None, (), exit_body, loc
    )
    prog = c.PascalProgram(
        "Probe", (), (), c.CompoundStatement(loc, ()), global_routines=(routine,)
    )
    for bits, typ in ((32, c._PE32CodeGenerator), (64, c._PE64CodeGenerator)):
        plain = typ(prog).generate().assembly
        active = typ(prog, stack_protector=True).generate().assembly
        assert "cookie_failure" not in plain
        assert "BCryptGenRandom" not in plain
        assert "cookie_failure" in active
        assert "BCryptGenRandom" in active
        assert "InterlockedCompareExchange" in active
        assert "RaiseFailFastException" in active
        assert "cookie_secret" in active
        assert active.count("cookie_initialize") >= 2
        assert active.count("jne __pas_cookie_failure") >= 2, bits
        assert "js __pas_cookie_failure" in active  # NTSTATUS failure only
        assert f"[{'rbp' if bits == 64 else 'ebp'}-{'8' if bits == 64 else '4'}]" in active
        if bits == 64:
            assert "sub rsp, 32\n    call __pas_cookie_initialize\n    add rsp, 32" in active
            assert "resq 1" in active
        else:
            assert "sub esp, 4\n    call __pas_cookie_initialize" in active
            assert "resd 1" in active


def test_settings_reach_compile_worker():
    assert '"stack_protector": False' not in D64  # never override selection
    assert 'compiler_kwargs["stack_protector"] = _parse_project_bool(' in D64
    assert '_cookie_options.get(document.build_target, {})' in D64
    assert '"stack_protector" in parameter_map' in D64
    # 32-bit and 64-bit persistent option handling from Stage 531 unchanged.
    assert 'Settings.Windows.{_suffix}.Compiler.Security' in D64
    assert '"ProtectorCookie"' in D64
    assert 'stack_protector: bool = False' in SRC
    assert 'stack_protector=stack_protector' in SRC


def test_early_exit_and_return_paths():
    c = _compiler()
    loc = c.SourcePosition(1, 1)
    proc = c.GlobalRoutineImplementation(
        "procedure", "A", (), None, (),
        c.CompoundStatement(loc, (c.ExitStatement(loc),)), loc
    )
    prog = c.PascalProgram("B", (), (), c.CompoundStatement(loc, ()), global_routines=(proc,))
    for impl in (c._PE32CodeGenerator,c._PE64CodeGenerator):
        assembly = impl(prog, stack_protector=True).generate().assembly
        # One validation at EXIT and one at normal fall-through.
        body = assembly.split("__pas_global_a:",1)[1].split("; Stage 532",1)[0]
        assert body.count("jne __pas_cookie_failure") == 2
        assert body.count("    ret") == 2


def test_project_file_unaffected_by_default():
    c = _compiler()
    loc=c.SourcePosition(1,1)
    prog=c.PascalProgram("B",(),(),c.CompoundStatement(loc,()))
    for typ in (c._PE32CodeGenerator,c._PE64CodeGenerator):
        no=typ(prog).generate().assembly
        assert "cookie" not in no.casefold()
        yes=typ(prog,stack_protector=True).generate().assembly
        assert "cookie_secret" in yes


def run_all():
    checks = [
        test_opt_in_and_architectures, test_settings_reach_compile_worker,
        test_early_exit_and_return_paths, test_project_file_unaffected_by_default,
    ]
    for fn in checks:
        fn()
        print("PASS",fn.__name__)
    print("Stage 532 tests:",len(checks),"passed")


if __name__=="__main__":
    run_all()
