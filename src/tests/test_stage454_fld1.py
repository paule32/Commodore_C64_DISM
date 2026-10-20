# -*- coding: utf-8 -*-
"""Stage 454: FLD1 must round-trip through both native assemblers and WFM."""
from __future__ import annotations

import pytest
from test_stage446_real_pe_link import linkers
from test_stage451_wfm_size_optimizations import compile_wfm, FORM


@pytest.mark.parametrize('target', ('pe32', 'pe64'))
def test_x87_fld1_bytes_with_following_fldz_and_ret(target):
    ns = linkers()
    source = 'section .text\nentry _start\n_start:\n    fld1\n    fldz\n    ret\n'
    assemble = ns['assemble_pe32_object_source'] if target == 'pe32' else ns['assemble_pe64_object_source']
    result = assemble(source)
    assert result.code == bytes.fromhex('d9e8d9eec3')
    assert result.symbols['_start'] == 0


@pytest.mark.parametrize('target', ('pe32', 'pe64'))
def test_x87_fld1_coff_link(target):
    ns = linkers()
    asm = 'section .text\nentry _start\n_start:\n    fld1\n    fistp dword ptr [output]\n    ret\nsection .bss\noutput: resd 1\n'
    asm_fn, coff_fn, linker = ((ns['assemble_pe32_object_source'], ns['write_coff32_object'], ns['link_coff32_objects'])
                              if target == 'pe32' else (ns['assemble_pe64_object_source'], ns['write_coff64_object'], ns['link_coff64_objects']))
    obj = coff_fn(asm_fn(asm))
    binary = linker((obj,), entry_symbol='_start', gui=True).executable
    assert binary.startswith(b'MZ')


@pytest.mark.parametrize('target', ('pe32', 'pe64'))
def test_real_wfm_with_true_const_pool_assembles_and_links(target):
    ns = linkers()
    source = FORM.replace('IF A > 0 .AND. C < 10', 'IF A > 1 .AND. C < 10')
    result = compile_wfm(source, target=target, const_pool=True)
    asm = result.assembly
    assert '    fld1' in asm
    asm_fn, coff_fn, linker = ((ns['assemble_pe32_object_source'], ns['write_coff32_object'], ns['link_coff32_objects'])
                              if target == 'pe32' else (ns['assemble_pe64_object_source'], ns['write_coff64_object'], ns['link_coff64_objects']))
    binary = linker((coff_fn(asm_fn(asm)),), entry_symbol='__d64_wfm_entry', gui=True).executable
    assert binary.startswith(b'MZ')
