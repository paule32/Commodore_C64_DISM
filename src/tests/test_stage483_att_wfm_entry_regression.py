"""Stage 483: WFM's dot-prefixed entry metadata in generated AT&T source.

The normal WFM compiler writes '.entry __d64_wfm_entry'; the original
Stage-480 adapter mistakenly made this '.entry $__d64_wfm_entry', which
cannot be handled by the internal COFF assembler.  Both spellings are covered.
"""
from __future__ import annotations

import pytest

from windows_asm_att import intel_to_att, att_to_intel
from test_stage446_real_pe_link import linkers
from test_stage460_wfm_typed_slot_optimization import compile_slot_optimized
from test_stage466_wfm_top_level_program import USER_SOURCE


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_dot_entry_generated_as_plain_d64_metadata(target):
    source = ('.section .text\n.entry __d64_wfm_entry\n'
              '__d64_wfm_entry:\n mov eax, 42\n ret\n')
    att = intel_to_att(source, target=target)
    assert '.d64_entry __d64_wfm_entry\n' in att
    assert '.entry $__d64_wfm_entry' not in att
    restored = att_to_intel(att)
    assert 'entry __d64_wfm_entry\n' in restored
    ns = linkers()
    obj = ns[f'assemble_{target}_object_source'](restored)
    coff = ns[f'write_coff{64 if target == "pe64" else 32}_object'](obj)
    exe = ns[f'link_coff{64 if target == "pe64" else 32}_objects'](
        (coff,), entry_symbol='__d64_wfm_entry', gui=True)
    assert exe.executable.startswith(b'MZ')


@pytest.mark.parametrize('declaration', [
    '.entry $__d64_wfm_entry', '.entry __d64_wfm_entry',
    '.d64_entry $__d64_wfm_entry', '.d64_entry __d64_wfm_entry',
])
def test_legacy_entry_formats_are_normalized(declaration):
    source = '.att_syntax\n.text\n' + declaration + '\n__d64_wfm_entry:\n movl $42, %eax\n ret\n'
    restored = att_to_intel(source)
    assert 'entry __d64_wfm_entry\n' in restored
    assert 'entry $' not in restored


def test_reject_invalid_entry_symbol_instead_of_bad_coff_metadata():
    with pytest.raises(ValueError, match='Einstiegssymbol'):
        att_to_intel('.att_syntax\n.entry $foo+4\n')
    with pytest.raises(ValueError, match='Einstiegssymbol'):
        intel_to_att('.entry foo+4\n')


@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_real_wfm_assembly_roundtrip_and_pe_link(target):
    intel = compile_slot_optimized(target, False, True, USER_SOURCE)
    assert '.entry __d64_wfm_entry' in intel
    att = intel_to_att(intel, target=target)
    assert '.d64_entry __d64_wfm_entry' in att
    assert '.entry $' not in att
    restored = att_to_intel(att)
    ns = linkers()
    obj = ns[f'assemble_{target}_object_source'](restored)
    coff = ns[f'write_coff{64 if target == "pe64" else 32}_object'](obj)
    exe = ns[f'link_coff{64 if target == "pe64" else 32}_objects'](
        (coff,), entry_symbol='__d64_wfm_entry', gui=True)
    assert exe.executable.startswith(b'MZ')

@pytest.mark.parametrize('target', ['pe32', 'pe64'])
def test_wfm_ffi_x87_and_displacement_roundtrip_keeps_exact_machine_code(target):
    """A WFM FFI call uses FILD/FISTP and a symbol+4 DWORD store on PE64."""
    from test_stage477_dbase_winapi_ffi import DECL, CALL
    source = DECL + 'result = ' + CALL + '\nCLASS Form1 OF FORM\nENDCLASS\n'
    original = compile_slot_optimized(target, False, True, source)
    att = intel_to_att(original, target=target)
    assert '.d64_entry __d64_wfm_entry' in att
    if target == 'pe64':
        assert 'fistpll __dbase_ffi_return' in att
        assert 'fildll __dbase_ffi_return' in att
    restored = att_to_intel(att)
    ns = linkers()
    assemble = ns[f'assemble_{target}_object_source']
    first, second = assemble(original), assemble(restored)
    assert first.code == second.code
    assert first.data == second.data
    coff = ns[f'write_coff{64 if target == "pe64" else 32}_object'](second)
    linked = ns[f'link_coff{64 if target == "pe64" else 32}_objects'](
        (coff,), entry_symbol='__d64_wfm_entry', gui=True)
    assert linked.executable.startswith(b'MZ')


@pytest.mark.parametrize('intel,expected_att,restored', [
    ('fistp word ptr [tmp]', 'fistps tmp', 'fistp word ptr [tmp]'),
    ('fistp dword ptr [tmp]', 'fistpl tmp', 'fistp dword ptr [tmp]'),
    ('fistp qword ptr [tmp]', 'fistpll tmp', 'fistp qword ptr [tmp]'),
    ('fild word ptr [tmp]', 'filds tmp', 'fild word ptr [tmp]'),
    ('fild dword ptr [tmp]', 'fildl tmp', 'fild dword ptr [tmp]'),
    ('fild qword ptr [tmp]', 'fildll tmp', 'fild qword ptr [tmp]'),
    ('fld dword ptr [tmp]', 'flds tmp', 'fld dword ptr [tmp]'),
    ('fld qword ptr [tmp]', 'fldl tmp', 'fld qword ptr [tmp]'),
    ('fstp dword ptr [tmp]', 'fstps tmp', 'fstp dword ptr [tmp]'),
    ('fstp qword ptr [tmp]', 'fstpl tmp', 'fstp qword ptr [tmp]'),
])
def test_gnu_x87_suffix_matches_actual_memory_width(intel, expected_att, restored):
    att = intel_to_att('.section .text\n' + intel + '\n')
    assert expected_att in att
    assert restored in att_to_intel(att)


def test_gnu_symbol_displacement_is_memory_not_immediate():
    intel = 'mov dword ptr [__dbase_ffi_return+4], 0\n'
    att = intel_to_att(intel)
    assert 'movl $0, __dbase_ffi_return+4' in att
    assert 'mov dword ptr [__dbase_ffi_return+4], 0' in att_to_intel(att)


def test_old_intel_entry_with_dollar_is_repaired():
    assert '.d64_entry __d64_wfm_entry\n' in intel_to_att(
        '.entry $__d64_wfm_entry\n')
