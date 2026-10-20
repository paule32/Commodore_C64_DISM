"""Stage 464: TYPE('name') and VARTYPE(value), console and WFM PE32/PE64."""
from __future__ import annotations
import pytest
from d64dbase import (DBaseCompilerError, compile_dbase_to_assembly,
                      evaluate_dbase_statements, parse_dbase_statements)
from test_stage446_real_pe_link import linkers
from test_stage460_wfm_typed_slot_optimization import compile_slot_optimized

SAMPLE = '''STORE 123.45 TO xyz
? TYPE("xyz")
? VARTYPE(xyz)
IF TYPE("xyz") == "N"
    ? "numerisch"
ENDIF
STORE "Test" TO xyz
? TYPE("xyz")
? VARTYPE(xyz)
? TYPE("nichtVorhanden")
? VARTYPE("Text")
? VARTYPE(42)
'''
WFM = '''Form1 = NEW Form1()
CLASS Form1 OF FORM
    PROCEDURE PushButton1_onClick()
        ? TYPE("xyz")
        ? VARTYPE(xyz)
        STORE 42 TO xyz
        ? TYPE("xyz")
        IF VARTYPE(xyz) = "N"
            ? "numeric"
        ENDIF
        STORE "abc" TO xyz
        IF TYPE("xyz") != "N" .AND. VARTYPE(xyz) == "C"
            ? "character"
        ENDIF
        STORE VARTYPE(xyz) TO result
        ? result
        RETURN
ENDCLASS
'''

def test_interpreter_classic_and_direct_type():
    assert evaluate_dbase_statements(parse_dbase_statements(SAMPLE)) == (
        'N\r\nN\r\nnumerisch\r\nC\r\nC\r\nU\r\nC\r\nN\r\n')

@pytest.mark.parametrize('target', ('pe32','pe64'))
def test_console_native_type_assembly_and_link(target):
    result = compile_dbase_to_assembly(SAMPLE, target=target)
    asm = result.assembly
    assert not result.external_functions
    assert 'mov eax, dword ptr [__dbase_var_xyz_type]' in asm
    assert '_type_print' in asm
    funcs = linkers()
    ob = funcs[f'assemble_{target}_object_source'](asm)
    bits = 64 if target == 'pe64' else 32
    coff = funcs[f'write_coff{bits}_object'](ob)
    linked = funcs[f'link_coff{bits}_objects']((coff,), entry_symbol='_start',gui=False)
    assert linked.executable[:2] == b'MZ'

@pytest.mark.parametrize('target', ('pe32','pe64'))
def test_wfm_type_assembly_and_link(target):
    asm = compile_slot_optimized(target, False, True, WFM)
    assert '    mov eax, 85' in asm
    assert '    mov eax, 78' in asm
    assert '    mov eax, 67' in asm
    assert '    mov edx, dword ptr [__dbase_wfm_mem_xyz_type]' in asm
    funcs = linkers()
    ob = funcs[f'assemble_{target}_object_source'](asm)
    bits = 64 if target == 'pe64' else 32
    coff = funcs[f'write_coff{bits}_object'](ob)
    linked = funcs[f'link_coff{bits}_objects']((coff,), entry_symbol='__d64_wfm_entry',gui=True)
    assert linked.executable[:2] == b'MZ'

@pytest.mark.parametrize('name', ('TYPE','VARTYPE'))
def test_reject_wrong_arity(name):
    for expression in (f'{name}()', f'{name}(1,2)'):
        with pytest.raises(DBaseCompilerError, match='genau einen Parameter'):
            compile_dbase_to_assembly('? ' + expression, target='pe32')


def test_type_requires_variable_name_but_vartype_allows_expression():
    with pytest.raises(DBaseCompilerError, match='Variablennamen'):
        compile_dbase_to_assembly('? TYPE(123)', target='pe32')
    assert evaluate_dbase_statements(parse_dbase_statements('? VARTYPE(1+2)')) == 'N\r\n'


def test_type_after_different_branch_types_reads_dynamic_slot():
    source = '''STORE 0 TO xyz
IF ISMOUSE()
    STORE "text" TO xyz
ELSE
    STORE 22 TO xyz
ENDIF
? TYPE("xyz")
? VARTYPE(xyz)
'''
    result = compile_dbase_to_assembly(source, target='pe32')
    assert result.assembly.count('mov eax, dword ptr [__dbase_var_xyz_type]') >= 2
    assert not result.external_functions or all(fn.lower() != 'type' for fn in result.external_functions)
