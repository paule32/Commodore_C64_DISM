"""Stage 484: GNU x87 control-word memory operands require WORD in internal COFF."""
from __future__ import annotations

import pytest

from windows_asm_att import att_to_intel, intel_to_att
from test_stage446_real_pe_link import linkers


@pytest.mark.parametrize('target,stack', [('pe32', 'esp'), ('pe64', 'rsp')])
def test_x87_control_word_roundtrip_and_real_coff_link(target, stack):
    intel = (f'section .text\nentry _start\n_start:\n'
             f' sub {stack}, 8\n'
             f' fnstcw word ptr [{stack}]\n'
             f' fldcw word ptr [{stack}+4]\n'
             f' add {stack}, 8\n ret\n')
    att = intel_to_att(intel, target=target)
    assert f'fnstcw (%{stack})' in att
    assert f'fldcw 4(%{stack})' in att
    restored = att_to_intel(att)
    assert f'fnstcw word ptr [{stack}]' in restored
    assert f'fldcw word ptr [{stack}+4]' in restored

    funcs = linkers()
    assemble = funcs[f'assemble_{target}_object_source']
    original_obj = assemble(intel)
    translated_obj = assemble(restored)
    assert original_obj.code == translated_obj.code
    assert b'\xd9\x3c\x24' in translated_obj.code
    bits = 64 if target == 'pe64' else 32
    coff = funcs[f'write_coff{bits}_object'](translated_obj)
    exe = funcs[f'link_coff{bits}_objects']((coff,), entry_symbol='_start', gui=True)
    assert exe.executable[:2] == b'MZ'


@pytest.mark.parametrize('syntax,expected', [
    ('fnstcw (%esp)', 'fnstcw word ptr [esp]'),
    ('fldcw 4(%esp)', 'fldcw word ptr [esp+4]'),
    ('fnstcw (%rsp)', 'fnstcw word ptr [rsp]'),
    ('fldcw 4(%rsp)', 'fldcw word ptr [rsp+4]'),
    ('fnstcw symbol', 'fnstcw word ptr [symbol]'),
    ('fldcw symbol+2', 'fldcw word ptr [symbol+2]'),
])
def test_gnu_control_word_operands_are_16bit(syntax, expected):
    assert expected in att_to_intel('.att_syntax\n.text\n' + syntax + '\n')


def test_existing_narrowing_and_macro_directives_stay_unchanged():
    source = '%include "test.inc"\n%define VAL 7\n.att_syntax\n.text\nfnstcw (%esp)\n'
    intel = att_to_intel(source)
    assert '%include "test.inc"' in intel
    assert '%define VAL 7' in intel
    assert 'fnstcw word ptr [esp]' in intel
