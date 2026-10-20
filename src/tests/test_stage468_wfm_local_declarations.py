# -*- coding: utf-8 -*-
"""Stage 468: WFM LOCAL statements on executable top-level and in events."""
from __future__ import annotations

import re
import pytest

from test_stage460_wfm_typed_slot_optimization import compile_slot_optimized
from test_stage446_real_pe_link import linkers

TOP = '''LOCAL A = 9
? A
? TYPE("A")
? VARTYPE(A)
IF A == 9
    ? "lokale Variable"
ENDIF
CLASS Form1 OF FORM
    PROCEDURE Button_onClick()
        LOCAL A = "Klick"
        ? A
        ? VARTYPE(A)
        RETURN
ENDCLASS
'''


def procedure(asm, name):
    return asm.split(f'__dbase_wfm_proc_{name}:', 1)[1].split(
        f'; END WFM PROCEDURE/FUNCTION: {name}', 1)[0]


@pytest.mark.parametrize('target', ['pe32','pe64'])
@pytest.mark.parametrize('static_numeric,dynamic', [(False, False), (True, False), (False, True), (True, True)])
def test_header_local_initializer_type_vartype_and_scoped_event_slots_assemble_link(target,static_numeric,dynamic):
    asm = compile_slot_optimized(target, static_numeric, dynamic, TOP)
    top = procedure(asm, '__dbase_top_level__')
    event = procedure(asm, 'Button_onClick')
    assert '; Quellcode Zeile: 1' in top
    assert '; LOCAL A = 9' in top
    assert '__dbase_wfm_local___dbase_top_level___a_num' in top
    assert '__dbase_wfm_local_button_onclick_a_num' not in top
    assert '__dbase_wfm_local_button_onclick_a_ptr' in event
    assert '__dbase_wfm_local___dbase_top_level___a_type' not in event
    assert '; LOCAL A = "Klick"' in event
    for prefix in ('__dbase_wfm_local___dbase_top_level___a', '__dbase_wfm_local_button_onclick_a'):
        for field in ('type','num','ptr','len'):
            assert asm.count(f'{prefix}_{field}:') == 1
    assert 'mov dword ptr [__dbase_wfm_local___dbase_top_level___a_type], 0' in top
    assert 'mov dword ptr [__dbase_wfm_local_button_onclick_a_type], 0' in event
    lk = linkers()
    obj = lk[f'assemble_{target}_object_source'](asm)
    coff = lk[f'write_coff{64 if target == "pe64" else 32}_object'](obj)
    exe = lk[f'link_coff{64 if target == "pe64" else 32}_objects'](
        (coff,), entry_symbol='__d64_wfm_entry', gui=True)
    assert exe.executable.startswith(b'MZ')


def test_local_multiple_declarators_comma_in_string_and_assignment_copy():
    src = '''LOCAL A = 9, B = "rot,blau", C
? A
? B
C = A
? C
CLASS Form1 OF FORM
ENDCLASS
'''
    asm = compile_slot_optimized('pe32', False, True, src)
    top = procedure(asm, '__dbase_top_level__')
    for key in ('a','b','c'):
        assert f'__dbase_wfm_local___dbase_top_level___{key}_type:' in asm
    assert 'rot,blau' in asm
    assert '; C = A' in top
    assert 'call DBaseQtConsoleWrite' in top
    assert '; Quellcode Zeile: 1' in top


def test_local_only_null_declaration_no_global_memory_symbol():
    src = '''LOCAL x
? TYPE("x")
? VARTYPE(x)
CLASS Form1 OF FORM
ENDCLASS
'''
    asm = compile_slot_optimized('pe32', False, True, src)
    assert '__dbase_wfm_local___dbase_top_level___x_type:' in asm
    assert '__dbase_wfm_mem_x_type:' not in asm
    assert 'mov dword ptr [__dbase_wfm_local___dbase_top_level___x_type], 0' in asm


def test_local_does_not_leak_into_another_method():
    src = '''LOCAL A = 9
CLASS Form1 OF FORM
    PROCEDURE Click()
        ? TYPE("A")
        ? VARTYPE(A)
        RETURN
ENDCLASS
'''
    asm = compile_slot_optimized('pe32', False, True, src)
    event = procedure(asm, 'Click')
    # TYPE("A") is U; VARTYPE(A) in this context resolves a distinct
    # undefined memory slot, not the header LOCAL A.
    assert '__dbase_wfm_local___dbase_top_level___a_type' not in event
    assert '__dbase_wfm_local___dbase_top_level___a_type:' in asm


@pytest.mark.parametrize('declaration, pattern', [
    ('LOCAL A = 1, A=2', 'mehrfach deklariert'),
    ('LOCAL 2x = 7', 'ungueltige LOCAL-Deklaration'),
    ('LOCAL X = ', 'ungueltige LOCAL-Deklaration'),
    ('LOCAL A=F(1, 2', 'ungueltige LOCAL-Deklaration'),
    ('LOCAL A = MYSTERY(1)', 'Initialisierer wird nicht unterstuetzt'),
])
def test_invalid_local_fails_with_diagnostic_and_not_silently(declaration, pattern):
    src = declaration + '\nCLASS Form1 OF FORM\nENDCLASS\n'
    with pytest.raises(Exception, match=pattern):
        compile_slot_optimized('pe32', False, True, src)


def test_legacy_designer_modal_local_b_still_not_executed():
    src = '''PARAMETER bmodal
LOCAL B
B = NEW Form1()
IF bmodal = .T.
B.ReadModal()
ELSE
B.Open()
ENDIF
CLASS Form1 OF FORM
ENDCLASS
'''
    asm=compile_slot_optimized('pe32', False, True, src)
    assert '__dbase_wfm_proc___dbase_top_level__' not in asm
    assert '__dbase_wfm_local___dbase_top_level___b' not in asm
