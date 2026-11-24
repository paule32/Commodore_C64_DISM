"""Stage 682: O3 must remove dead exception BSS safely, not share live state."""
from __future__ import annotations

import pytest
from d64dbase import compile_dbase_to_assembly
from dbase_size_optimizer import optimize_dbase_size_assembly
from dbase_exception_optimizer import compact_unreferenced_exception_state


@pytest.mark.parametrize('target', ('pe32', 'pe64'))
def test_plain_program_has_no_exception_state_under_o3(target):
    raw = compile_dbase_to_assembly('? "hello"', target=target).assembly
    assert '__dbase_exception_id:' in raw
    for level in ('O0', 'O1', 'O2'):
        assert '__dbase_exception_id:' in optimize_dbase_size_assembly(raw, level=level).assembly
    optimized = optimize_dbase_size_assembly(raw, level='O3').assembly
    assert '__dbase_exception_id:' not in optimized
    assert '__dbase_exception_message_ptr:' not in optimized
    assert '__dbase_exception_objects_head:' not in optimized
    assert '__dbase_exception_unhandled_' not in optimized
    assert optimize_dbase_size_assembly(optimized, level='O3').assembly == optimized

    from test_stage605_link import _load_pe_linker
    backend = _load_pe_linker()
    assemble = backend['assemble_pe32_object_source' if target == 'pe32' else 'assemble_pe64_object_source']
    write = backend['write_coff32_object' if target == 'pe32' else 'write_coff64_object']
    link = backend['link_coff32_objects' if target == 'pe32' else 'link_coff64_objects']
    obj = assemble(optimized)
    assert '__dbase_exception_id' not in obj.symbols
    assert link((write(obj),), entry_symbol='_start', gui=True).executable[:2] == b'MZ'


@pytest.mark.parametrize('target', ('pe32', 'pe64'))
def test_live_exception_state_preserved(target):
    source = 'TRY\n THROW NEW Exception("raised")\nCATCH (Exception e)\n ? e.Message\nENDTRY'
    raw = compile_dbase_to_assembly(source, target=target).assembly
    opt = optimize_dbase_size_assembly(raw, level='O3').assembly
    assert '__dbase_exception_id:' in opt
    assert '__dbase_exception_message_ptr:' in opt
    assert '__dbase_exception_objects_head:' in opt
    assert '__dbase_exception_unhandled_' in opt
    from test_stage605_link import _load_pe_linker
    b = _load_pe_linker()
    obj = b['assemble_pe32_object_source' if target == 'pe32' else 'assemble_pe64_object_source'](opt)
    writer = b['write_coff32_object' if target == 'pe32' else 'write_coff64_object']
    linker = b['link_coff32_objects' if target == 'pe32' else 'link_coff64_objects']
    assert linker((writer(obj),), entry_symbol='_start', gui=True).executable[:2] == b'MZ'


def test_referenced_inner_exception_fallback_label_never_removed():
    asm = '''section .text
    jmp __dbase_exception_unhandled_7
__dbase_exception_unhandled_7:
    mov eax, [__dbase_exception_class_ptr]
    mov ecx, [__dbase_exception_message_ptr]
    call DBaseQtProcessEvents
__dbase_exception_continue_8:
section .bss
__dbase_exception_id:
    resd 1
__dbase_exception_class_ptr:
    resd 1
__dbase_exception_message_ptr:
    resd 1
'''
    result, changes = compact_unreferenced_exception_state(asm)
    assert result == asm
    assert changes == 0


def test_packed_slots_are_not_pruned_when_their_base_address_is_used():
    asm = '''section .text
    lea esi, [__dbase_exception_message_type]
section .bss
__dbase_exception_message_type:
    resd 1
__dbase_exception_message_num:
    resq 1
__dbase_exception_message_ptr:
    resd 1
__dbase_exception_message_len:
    resd 1
'''
    result, changes = compact_unreferenced_exception_state(asm)
    assert result == asm
    assert changes == 0
