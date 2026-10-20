# -*- coding: utf-8 -*-
"""Stage 441: native dBASE LEN/LTRIM/RTRIM/TRIM, PE32 and PE32+."""
from __future__ import annotations

from decimal import Decimal

import pytest

from d64dbase import (DBaseCompilerError, compile_dbase_to_assembly,
                      evaluate_dbase_statements, parse_dbase_statements)
from d64dbase.string_length_trim import (emit_trim_operation, string_length,
                                        trim_string)


def _evaluate(source):
    return evaluate_dbase_statements(parse_dbase_statements(source))


def test_len_print_literal_memory_macro_and_expression():
    source = '''#define STRING_MACRO "   Makro-String  "
? len("Ein String")
STORE "  Hallo " TO Text
? len(Text)
? LEN(STRING_MACRO)
? len(TRIM(Text))
? LEN("äöß€")
'''
    assert _evaluate(source) == '10\r\n8\r\n17\r\n5\r\n4\r\n'
    for target in ('pe32', 'pe64'):
        result = compile_dbase_to_assembly(source, target=target)
        assert not result.external_functions
        assert result.transcript == '10\r\n8\r\n17\r\n5\r\n4\r\n'
        assert 'fld' in result.assembly


def test_trim_function_returns_numbers_and_chained_calls():
    source = '''STORE "    x   " TO Text
? LEN(LTRIM(Text))
? LEN(RTRIM(Text))
? LEN(TRIM(Text))
? TRIM(LTRIM("   z \t"))
STORE TRIM(Text) TO Ergebnis
? "[" + Ergebnis + "]"
'''
    assert _evaluate(source) == '4\r\n5\r\n1\r\nz\r\n[x]\r\n'
    for target in ('pe32', 'pe64'):
        result = compile_dbase_to_assembly(source, target=target)
        asm = result.assembly
        # STORE mit konstantem String darf der Analyzer vollstaendig falten.
        # Dynamische Native-Pfade werden im Funktionstest separat getestet.
        assert 'fld' in asm
        assert not result.external_functions


def test_user_function_string_return_in_each_target():
    source = '''FUNCTION getText()
RETURN "   Rueckgabe  "
? LEN(getText())
? LTRIM(getText())
? RTRIM(getText())
? TRIM(getText())
'''
    assert _evaluate(source) == '14\r\nRueckgabe  \r\n   Rueckgabe\r\nRueckgabe\r\n'
    for target in ('pe32', 'pe64'):
        result = compile_dbase_to_assembly(source, target=target)
        assert 'call __dbase_function_gettext__void' in result.assembly
        assert '_copy_loop:' in result.assembly
        assert not result.external_functions


@pytest.mark.parametrize('name,value,expected', [
    ('ltrim', '   abc \t', 'abc \t'),
    ('rtrim', ' abc \n\t\b\r ', ' abc'),
    ('trim', ' \r\t abc \n\b ', 'abc'),
    ('trim', '\t\n\b\r   ', ''),
    ('ltrim', 'abc', 'abc'),
    ('rtrim', 'abc', 'abc'),
    ('trim', '', ''),
    ('trim', '  äöß€  ', 'äöß€'),
])
def test_trim_control_characters(name, value, expected):
    assert trim_string(name, value) == expected


def test_len_codepage_byte_length():
    assert string_length('äöß€') == Decimal(4)
    assert string_length('') == Decimal(0)
    assert string_length('x\n\t') == Decimal(3)


@pytest.mark.parametrize('target', ('pe32','pe64'))
def test_native_assembly_has_bounded_scans_and_independent_copy(target):
    for kind in ('ltrim', 'rtrim', 'trim'):
        asm = '\n'.join(emit_trim_operation('src', 'dest', kind=kind,
                       is64=(target == 'pe64'), prefix='__test', string_type=2))
        assert '__test_copy_loop:' in asm
        assert 'mov dword ptr [dest_len], edi' in asm
        assert 'mov byte ptr [' in asm and '], 0' in asm
        assert 'call __dbase_malloc' in asm
        assert 'mov eax, dword ptr [src_len]' in asm
        if kind in ('rtrim','trim'):
            assert 'cmp al, 9' in asm and 'cmp al, 10' in asm
            assert 'cmp al, 8' in asm and 'cmp al, 13' in asm
        if kind == 'ltrim':
            assert 'cmp al, 9' not in asm
        if target == 'pe64':
            assert 'push rsi' in asm and 'push rdi' in asm
        else:
            assert 'push esi' in asm and 'push edi' in asm


@pytest.mark.parametrize('name', ('len', 'ltrim', 'rtrim', 'trim'))
def test_invalid_argument_types_and_arity(name):
    for source in (f'? {name}()', f'? {name}("a", "b")', f'? {name}(99)'):
        with pytest.raises(DBaseCompilerError):
            compile_dbase_to_assembly(source, target='pe32')


def test_empty_and_only_whitespace_in_real_compiler():
    source = 'STORE "  " TO X\n? LEN(X)\n? "<" + TRIM(X) + ">"\n? LEN(TRIM(X))'
    assert _evaluate(source) == '2\r\n<>\r\n0\r\n'
    for target in ('pe32','pe64'):
        assert compile_dbase_to_assembly(source, target=target)
