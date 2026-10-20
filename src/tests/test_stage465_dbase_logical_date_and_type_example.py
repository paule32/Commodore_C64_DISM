# -*- coding: utf-8 -*-
"""Stage 465: logical/date TYPE/VARTYPE and the exact user example with && comments."""
import pytest
from d64dbase import (
    DBaseCompilerError, compile_dbase_to_assembly,
    parse_dbase_statements, evaluate_dbase_statements,
)
from test_stage446_real_pe_link import linkers
from test_stage460_wfm_typed_slot_optimization import compile_slot_optimized

USER_EXAMPLE = '''STORE 123.45 TO xyz

? TYPE("xyz")       && N
? VARTYPE(xyz)      && N

IF TYPE("xyz") == "N"
    ? "xyz ist numerisch"
ENDIF

STORE "Hallo" TO xyz

? TYPE("xyz")       && C
? VARTYPE(xyz)      && C

? TYPE("unbekannt") && U
'''

TYPES = '''STORE .T. TO xyz
? TYPE("xyz")
? VARTYPE(xyz)
? xyz
STORE .F. TO xyz
? TYPE("xyz")
? VARTYPE(xyz)
? xyz
STORE {^2026-10-19} TO xyz
? TYPE("xyz")
? VARTYPE(xyz)
? xyz
STORE 123 TO xyz
? TYPE("xyz")
STORE "hello" TO xyz
? TYPE("xyz")
? TYPE("missing")
? VARTYPE(.T.)
? VARTYPE({^2026-10-19})
'''

WFM = '''B = NEW Form1()
CLASS Form1 OF FORM
PROCEDURE PushButton1_onClick()
    STORE .T. TO xyz
    ? TYPE("xyz")
    ? VARTYPE(xyz)
    STORE {^2026-10-19} TO xyz
    ? TYPE("xyz")
    ? VARTYPE(xyz)
    ? xyz
    STORE "again" TO xyz
    ? TYPE("xyz")
    RETURN
ENDCLASS
'''


def _link(assembly, target, *, gui):
    f = linkers()
    obj = f[f'assemble_{target}_object_source'](assembly)
    bits = 64 if target == 'pe64' else 32
    coff = f[f'write_coff{bits}_object'](obj)
    linked = f[f'link_coff{bits}_objects'](
        (coff,), entry_symbol='__d64_wfm_entry' if gui else '_start', gui=gui)
    assert linked.executable.startswith(b'MZ')


def test_user_example_with_inline_comments_interprets():
    assert evaluate_dbase_statements(parse_dbase_statements(USER_EXAMPLE)) == (
        'N\r\nN\r\nxyz ist numerisch\r\nC\r\nC\r\nU\r\n')


@pytest.mark.parametrize('target', ('pe32', 'pe64'))
def test_user_example_full_compilation_and_link(target):
    _link(compile_dbase_to_assembly(USER_EXAMPLE, target=target).assembly, target, gui=True)


def test_interpreter_logical_and_date_values():
    assert evaluate_dbase_statements(parse_dbase_statements(TYPES)) == (
        'L\r\nL\r\n.T.\r\nL\r\nL\r\n.F.\r\n'
        'D\r\nD\r\n2026-10-19\r\nN\r\nC\r\nU\r\nL\r\nD\r\n')


@pytest.mark.parametrize('target', ('pe32', 'pe64'))
def test_console_logical_date_compile_and_link(target):
    asm = compile_dbase_to_assembly(TYPES, target=target).assembly
    assert '_type_logical_' in asm
    assert '_type_date_' in asm
    _link(asm, target, gui=True)


@pytest.mark.parametrize('target', ('pe32', 'pe64'))
def test_wfm_logical_date_compile_and_link(target):
    asm = compile_slot_optimized(target, False, True, WFM)
    assert '    mov eax, 76' in asm  # L
    assert '    mov eax, 68' in asm  # D
    assert '    call DBaseWfmFormatValue' in asm
    _link(asm, target, gui=True)


@pytest.mark.parametrize('raw', ('{^2026-02-30}', '{^2026-13-01}', '{2026-12-32}'))
def test_invalid_calendar_date_has_diagnostic(raw):
    with pytest.raises(DBaseCompilerError, match='Ungueltiges dBASE-Datum'):
        parse_dbase_statements(f'? {raw}')
